import pdfplumber
import os

for f in os.listdir("uploads"):
    if f.endswith(".pdf"):
        path = os.path.join("uploads", f)
        try:
            with pdfplumber.open(path) as pdf:
                for p in pdf.pages:
                    text = p.extract_text()
                    if text and "Constitution" in text:
                        print(f"FOUND GST IN {f}")
                        idx = text.find("Address")
                        print(text[idx:idx+200])
                        exit()
        except Exception:
            pass
