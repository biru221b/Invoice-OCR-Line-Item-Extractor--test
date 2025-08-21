import os
import re
import sys
import argparse
import shutil
import cv2
import pytesseract
import pandas as pd

# ================= CONFIG =================
OCR_CONFIG = r"--oem 3 --psm 6"
INPUT_FOLDER = "invoices"
OUTPUT_FOLDER = "outputs"
SUMMARY_FILE = "invoices_summary.csv"
LINE_ITEMS_FILE = "invoice_line_items.csv"

# ================= UTILS =================
def ensure_dirs(path: str):
    os.makedirs(path, exist_ok=True)

def find_tesseract() -> bool:
    if getattr(pytesseract.pytesseract, "tesseract_cmd", None) and os.path.exists(pytesseract.pytesseract.tesseract_cmd):
        return True
    return shutil.which("tesseract") is not None

def load_image(path: str):
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {path}")
    return img

# ================= PREPROCESS =================
def preprocess_image(img, upscale=2.0):
    """Preprocess image for OCR"""
    if upscale != 1:
        img = cv2.resize(img, None, fx=upscale, fy=upscale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    gray = cv2.medianBlur(gray, 3)
    th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY, 31, 10)
    th = cv2.fastNlMeansDenoising(th, None, 30, 7, 21)
    return th

# ================= PARSING HELPERS =================
TOTAL_PATTERNS = [r"(gross\s*amount|net\s*amount|total\s*amount|amount\s*due|grand\s*total|total)\s*[:\-]?\s*(?:Rs\.?|रु\.?|NPR|₹)?\s*([0-9][0-9,]*\.?[0-9]{0,2})"]

def find_first(patterns, text, group=2):
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            return m.group(group).strip()
    return ""

def extract_total(text):
    t = find_first(TOTAL_PATTERNS, text)
    if t: return t
    nums = re.findall(r"([0-9][0-9,]*\.[0-9]{2})", text)
    if nums:
        try: return f"{max([float(n.replace(',','')) for n in nums]):.2f}"
        except: return nums[0]
    return ""

# ================= LINE ITEM PARSER =================
def parse_line_items(text, filename):
    """Extract only line items with numbers and descriptions"""
    items = []
    ignore_keywords = ["TOTAL", "AMOUNT DUE", "CHANGE", "CASH", "RECEIPT", "SUBTOTAL"]
    for line in text.splitlines():
        line = line.strip()
        if not line: continue
        if any(kw in line.upper() for kw in ignore_keywords):
            continue
        numbers = re.findall(r"[\d,.]+", line)
        description = re.sub(r"[\d,.]+", "", line).strip()
        if numbers and description:
            qty = numbers[0] if len(numbers) > 2 else ""
            unit_price = numbers[1] if len(numbers) > 2 else numbers[0] if len(numbers) > 1 else ""
            line_total = numbers[-1]
            items.append({
                "File": filename,
                "Item": description,
                "Quantity": qty,
                "Unit Price": unit_price,
                "Line Total": line_total
            })
    return items

# ================= PROCESS =================
def process_image(path):
    filename = os.path.basename(path)
    img = load_image(path)
    prep = preprocess_image(img)
    text = pytesseract.image_to_string(prep, config=OCR_CONFIG)
    total = extract_total(text)
    items = parse_line_items(text, filename)
    summary = {"File": filename, "Total Amount": total}
    return summary, items

def process_folder(input_path):
    summary_list, line_items_list = [], []
    supported_ext = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp")
    files = [f for f in os.listdir(input_path) if f.lower().endswith(supported_ext)]
    files.sort()
    for f in files:
        try:
            summary, items = process_image(os.path.join(input_path, f))
            summary_list.append(summary)
            line_items_list.extend(items)
            print(f"[INFO] {f} → {len(items)} line items detected")
        except Exception as e:
            print(f"[ERROR] {f}: {e}")
    return pd.DataFrame(summary_list), pd.DataFrame(line_items_list)

# ================= MAIN =================
def main():
    parser = argparse.ArgumentParser(description="Invoice OCR → CSV")
    parser.add_argument("--input", "-i", default=INPUT_FOLDER)
    parser.add_argument("--out", "-o", default=OUTPUT_FOLDER)
    args = parser.parse_args()
    
    if not find_tesseract():
        print("ERROR: Tesseract not found!")
        sys.exit(1)
    
    ensure_dirs(args.out)
    df_summary, df_items = process_folder(args.input)
    
    sum_csv = os.path.join(args.out, SUMMARY_FILE)
    items_csv = os.path.join(args.out, LINE_ITEMS_FILE)
    
    df_summary.to_csv(sum_csv, index=False)
    if not df_items.empty: df_items.to_csv(items_csv, index=False)
    
    print("\n✅ Done")
    print(f"- Summary CSV: {sum_csv} ({len(df_summary)} files)")
    print(f"- Line Items CSV: {items_csv} ({len(df_items)} rows)")

if __name__ == "__main__":
    main()
