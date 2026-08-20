import pdfplumber

pdf_path = './uploads/loandesk/cases/1/documents/Gst certificate (2) R B ENTERPRICE.pdf'

with pdfplumber.open(pdf_path) as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    for i, page in enumerate(pdf.pages):
        text = page.extract_text(layout=True)
        print(f"Page {i+1} text length (with layout): {len(text) if text else 0}")
        if text:
            print(f"--- Page {i+1} Preview ---")
            print(text[:200])
            print(f"--- End Page {i+1} Preview ---\n")
