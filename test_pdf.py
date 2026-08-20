import pdfplumber
import os

pdf_path = None
for f in os.listdir("uploads"):
    if f.endswith(".pdf"):
        pdf_path = os.path.join("uploads", f)

if pdf_path:
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text()
        print("WITHOUT LAYOUT:")
        print(text[:500])
        print("="*50)
        text2 = pdf.pages[0].extract_text(layout=True)
        print("WITH LAYOUT:")
        print(text2[:500])
