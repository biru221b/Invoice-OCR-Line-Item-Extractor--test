project: Invoice OCR & Line Item Extractor-test

description: >
  A Python tool to extract invoice line items and total amounts from
  scanned invoice or receipt images using Tesseract OCR and OpenCV.

features:
  - Extracts line items: description, quantity, unit price, line total
  - Extracts invoice summary: File name, Total Amount
  - Ignores headers, totals, and other non-item lines
  - Supports multiple image formats: .jpg, .jpeg, .png, .tif, .bmp
  - Outputs two CSV files:
      - invoices_summary.csv: Invoice summary
      - invoice_line_items.csv: Line item details

requirements:
  - Python >= 3.8
  - Tesseract OCR
  - Python packages:
      - opencv-python
      - pytesseract
      - pandas
      - numpy

installation:
  - Clone the repository:
      - git clone https://github.com/yourusername/invoice-ocr.git
      - cd invoice-ocr
  - Install dependencies:
      - pip install opencv-python pytesseract pandas numpy
  - Ensure Tesseract OCR is installed and added to PATH, or set path in script:
      - pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

usage:
  - Place all invoice images in the invoices folder (or any folder of your choice)
  - Run the script:
      - python ocr_extract.py --input invoices --out outputs
  - Check the outputs folder for CSV files:
      - invoices_summary.csv: Summary of each invoice with total amount
      - invoice_line_items.csv: List of items extracted from all invoices
