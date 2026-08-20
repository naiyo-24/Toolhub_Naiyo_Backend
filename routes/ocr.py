from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.document import Document
from models.ocr_result import OCRResult
from schemas.ocr import OCRResultCreate, OCRResultUpdate, OCRResultResponse
from routes.auth import get_current_user

router = APIRouter()

@router.get("/document/{document_id}", response_model=OCRResultResponse)
def get_ocr_result(document_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    ocr_result = db.query(OCRResult).filter(OCRResult.document_id == document_id).first()
    if not ocr_result:
        raise HTTPException(status_code=404, detail="OCR result not found")
        
    return ocr_result

@router.post("", response_model=OCRResultResponse)
def create_ocr_result(ocr_data: OCRResultCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == ocr_data.document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    existing_ocr = db.query(OCRResult).filter(OCRResult.document_id == ocr_data.document_id).first()
    if existing_ocr:
        raise HTTPException(status_code=400, detail="OCR result already exists for this document")

    ocr_result = OCRResult(
        document_id=ocr_data.document_id,
        raw_text=ocr_data.raw_text,
        structured_data=ocr_data.structured_data,
        confidence=ocr_data.confidence,
        language=ocr_data.language
    )
    db.add(ocr_result)
    
    # Update document status
    doc.ocr_status = "COMPLETED"
    
    db.commit()
    db.refresh(ocr_result)
    return ocr_result

@router.patch("/{ocr_id}", response_model=OCRResultResponse)
def update_ocr_result(ocr_id: int, ocr_data: OCRResultUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ocr_result = db.query(OCRResult).filter(OCRResult.id == ocr_id).first()
    if not ocr_result:
        raise HTTPException(status_code=404, detail="OCR result not found")

    update_data = ocr_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ocr_result, key, value)

    db.commit()
    db.refresh(ocr_result)
    return ocr_result

@router.post("/document/{document_id}/extract", response_model=OCRResultResponse)
def run_ocr_on_document(document_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    import os
    import re
    from fastapi.responses import JSONResponse
    
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    file_path = os.path.join("uploads", doc.storage_key)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
        
    import pytesseract
    
    extracted_text = ""
    with open(file_path, "rb") as f:
        file_bytes = f.read()
        
    if doc.file_name.lower().endswith('.pdf'):
        import pdfplumber
        import io
        from pdf2image import convert_from_bytes
        
        try:
            images = None # Lazy load images only if a page needs it
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text(layout=True)
                    if page_text and len(page_text.strip()) >= 50:
                        extracted_text += page_text + "\n"
                    else:
                        # Fallback to Tesseract OCR for this specific page if it's a scanned image
                        if images is None:
                            images = convert_from_bytes(file_bytes)
                        if i < len(images):
                            text = pytesseract.image_to_string(images[i])
                            extracted_text += text + "\n"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")
    else:
        from PIL import Image
        import io
        try:
            image = Image.open(io.BytesIO(file_bytes))
            extracted_text = pytesseract.image_to_string(image)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process Image: {str(e)}")
            
    structured = {}
    doc_type = doc.document_type.upper() if doc.document_type else ""
    
    # Advanced extraction helper
    def extract_between(text, start_label, end_labels):
        def make_regex(label):
            chars = [re.escape(c) for c in label if c.strip()]
            return r'\s*'.join(chars)
            
        start_pattern = make_regex(start_label)
        start_match = re.search(start_pattern, text, re.IGNORECASE)
        if not start_match: return None
        
        start_idx = start_match.end()
        end_idx = len(text)
        
        for end_label in end_labels:
            end_pattern = make_regex(end_label)
            end_match = re.search(end_pattern, text[start_idx:], re.IGNORECASE)
            if end_match:
                match_pos = start_idx + end_match.start()
                if match_pos < end_idx:
                    end_idx = match_pos
                    
        extracted = text[start_idx:end_idx].strip()
        extracted = re.sub(r'^[\s:\-,|]+', '', extracted)
        extracted = re.sub(r'\s*\d+[\.,]?\s*$', '', extracted)
        extracted = re.sub(r'\s*de\s*$', '', extracted)
        extracted = re.sub(r'[\s.,|]+$', '', extracted)
        
        return extracted.strip() if extracted else None

    if doc_type == "GST" or "GST" in doc_type:
        # Basic Regex for structured data
        gst_match = re.search(r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b', extracted_text)
        gst_number = gst_match.group(0) if gst_match else None

        gst_legal_name = extract_between(extracted_text, "Legal Name", ["Trade Name", "Constitution of Business", "Address"])
        gst_trade_name = extract_between(extracted_text, "Trade Name, if any", ["Constitution of Business", "Address", "Date of Liability"])
        gst_constitution = extract_between(extracted_text, "Constitution of Business", ["Address of Principal", "Date of Liability"])
        gst_address = extract_between(extracted_text, "Address of Principal Place of Business", ["Date of Liability", "Period of Validity", "Type of Registration"])
        gst_date_of_liability = extract_between(extracted_text, "Date of Liability", ["Period of Validity", "Type of Registration"])
        gst_period_of_validity = extract_between(extracted_text, "Period of Validity", ["Type of Registration", "Particulars of"])
        gst_type_of_registration = extract_between(extracted_text, "Type of Registration", ["Particulars of Approving Authority", "Signature", "Particulars of"])
        gst_approving_authority = extract_between(extracted_text, "Particulars of Approving Authority", ["Signature", "Date", "Place"])
        
        if gst_number: structured["GST Number"] = gst_number
        if gst_legal_name: structured["Legal Name"] = gst_legal_name
        if gst_trade_name: structured["Trade Name"] = gst_trade_name
        if gst_constitution: structured["Constitution of Business"] = gst_constitution
        if gst_address: structured["Address"] = gst_address
        if gst_date_of_liability: structured["Date of Liability"] = gst_date_of_liability
        if gst_period_of_validity: structured["Period of Validity"] = gst_period_of_validity
        if gst_type_of_registration: structured["Type of Registration"] = gst_type_of_registration
        if gst_approving_authority: structured["Approving Authority"] = gst_approving_authority

    elif doc_type == "ITR" or "ITR" in doc_type:
        pan_match = re.search(r'PAN\s+([A-Z]{5}[0-9]{4}[A-Z])', extracted_text)
        name_match = re.search(r'Name\s+(.+?)(?=\s+Address)', extracted_text, re.DOTALL)
        address_match = re.search(r'Address\s+(.+?)(?=\s+Status)', extracted_text, re.DOTALL)
        status_match = re.search(r'Status\s+(.+?)(?=\s+Form Number)', extracted_text)
        form_number_match = re.search(r'Form Number\s+(.+?)(?=\s+Filed)', extracted_text)
        filed_us_match = re.search(r'Filed u/s\s+(.+?)(?=\s+e-Filing)', extracted_text)
        ack_match = re.search(r'e-Filing Acknowledgement Number\s+(\d+)', extracted_text)
        ay_match = re.search(r'Assessment Year\s+(\d{4}-\d{2})', extracted_text)
        
        row_skip = r'(?:\d{1,2}[A-Za-z\.]*\s+)?'
        def extract_fin(label_regex, text):
            match = re.search(label_regex + r'\s+' + row_skip + r'([^\n]+)', text, re.IGNORECASE)
            if not match: return None
            val = match.group(1).strip()
            clean_val = re.sub(r'[^\d,\.\-]', '', val)
            return clean_val if clean_val else '0'
        
        income_match = extract_fin(r'Total Income', extracted_text)
        loss_match = extract_fin(r'Current Year business loss, if any', extracted_text)
        mat_match = extract_fin(r'Book Profit under MAT, where applicable', extracted_text)
        amt_match = extract_fin(r'Adjusted Total Income under AMT, where applicable', extracted_text)
        net_tax_match = extract_fin(r'Net tax payable', extracted_text)
        interest_match = extract_fin(r'Interest and Fee Payable', extracted_text)
        total_tax_match = extract_fin(r'Total tax, interest and Fee payable', extracted_text)
        taxes_paid_match = extract_fin(r'Taxes Paid', extracted_text)
        payable_refundable_match = extract_fin(r'\(\+\)\s*Tax Payable\s*/\(-\)\s*Refundable\s*\(6-7\)', extracted_text)
        accreted_match = extract_fin(r'Accreted Income as per section 115TD\.?', extracted_text)
        add_tax_115td_match = extract_fin(r'Additional Tax payable u/s 115TD', extracted_text)
        interest_115te_match = extract_fin(r'Interest payable u/s 115TE', extracted_text)
        add_tax_int_payable_match = extract_fin(r'Additional Tax and interest payable', extracted_text)
        tax_int_paid_match = extract_fin(r'Tax and interest paid', extracted_text)
        payable_refundable_12_13_match = extract_fin(r'\(\+\)\s*Tax Payable\s*/\(-\)\s*Refundable\s*\(12-13\)', extracted_text)
        
        if pan_match: structured["PAN Number"] = pan_match.group(1).strip()
        if name_match: structured["Name"] = name_match.group(1).strip()
        if address_match: structured["Address"] = address_match.group(1).strip()
        if status_match: structured["Status"] = status_match.group(1).strip()
        if form_number_match: structured["Form Number"] = form_number_match.group(1).strip()
        if filed_us_match: structured["Filed u/s"] = filed_us_match.group(1).strip()
        if ack_match: structured["Acknowledgement Number"] = ack_match.group(1).strip()
        if ay_match: structured["Assessment Year"] = ay_match.group(1).strip()
        
        if income_match: structured["Total Income"] = income_match
        if loss_match: structured["Current Year business loss"] = loss_match
        if mat_match: structured["Book Profit under MAT"] = mat_match
        if amt_match: structured["Adjusted Total Income under AMT"] = amt_match
        if net_tax_match: structured["Net tax payable"] = net_tax_match
        if interest_match: structured["Interest and Fee Payable"] = interest_match
        if total_tax_match: structured["Total tax, interest and Fee payable"] = total_tax_match
        if taxes_paid_match: structured["Taxes Paid"] = taxes_paid_match
        if payable_refundable_match: structured["Tax Payable / Refundable (6-7)"] = payable_refundable_match
        if accreted_match: structured["Accreted Income (115TD)"] = accreted_match
        if add_tax_115td_match: structured["Additional Tax payable (115TD)"] = add_tax_115td_match
        if interest_115te_match: structured["Interest payable (115TE)"] = interest_115te_match
        if add_tax_int_payable_match: structured["Additional Tax and interest payable"] = add_tax_int_payable_match
        if tax_int_paid_match: structured["Tax and interest paid"] = tax_int_paid_match
        if payable_refundable_12_13_match: structured["Tax Payable / Refundable (12-13)"] = payable_refundable_12_13_match

    elif doc_type == "BANK STATEMENT" or "BANK STATEMENT" in doc_type:
        def extract_bank_val(label_pattern, text):
            match = re.search(label_pattern + r'\s*[:\-]?\s*([^\n]+)', text, re.IGNORECASE)
            if not match: return None
            val = match.group(1).strip()
            val = re.sub(r'\s{2,}.*', '', val)
            return val if val else None

        # Bank Name (Generalized or Explicit)
        bank_name_match = re.search(r'Account Statement\s+(.*?[Bb]ank)', extracted_text)
        bank_name = bank_name_match.group(1).strip() if bank_name_match else extract_bank_val(r'Bank\s+Name', extracted_text)

        # Customer Name (Table format or Label format)
        cust_name_match = re.search(r'Name Holding Status Customer ID\s*\n\s*([A-Za-z\s]{1,50}?)\s+(?:Primary|Joint)', extracted_text)
        cust_name = cust_name_match.group(1).strip() if cust_name_match else extract_bank_val(r'(?:Customer\s+Name|Name)', extracted_text)

        # Account Holder Type
        holder_type_match = re.search(r'([A-Za-z]+\s+Holder)\s+[A-Z0-9X]+', extracted_text)
        acc_holder_type = holder_type_match.group(1).strip() if holder_type_match else extract_bank_val(r'Account\s+Holder\s+Type', extracted_text)

        # Customer ID
        cust_id_match = re.search(r'(?:Primary|Joint) Holder\s+([A-Z0-9X]+)', extracted_text)
        cust_id = cust_id_match.group(1).strip() if cust_id_match else extract_bank_val(r'(?:Customer\s+ID|Cust\s+ID)', extracted_text)

        # Account Number
        acc_num_match = re.search(r'Account No[^\n]*\n\s*(\d{9,18})', extracted_text)
        if not acc_num_match: acc_num_match = re.search(r'\b(\d{10,18})\b', extracted_text)
        acc_num = acc_num_match.group(1).strip() if acc_num_match else extract_bank_val(r'(?:Account\s+Number|A/c\s+No\.?)', extracted_text)

        # Account Type
        acc_type_match = re.search(r'Account No[^\n]*\n\s*\d{9,18}\s+([A-Za-z\s]{1,50}?)\s+(?:INR|USD)', extracted_text, re.DOTALL)
        acc_type = acc_type_match.group(1).replace('\n', ' ').strip() if acc_type_match else extract_bank_val(r'(?:Account\s+Type|A/c\s+Type)', extracted_text)
        if acc_type: acc_type = re.sub(r'\s+', ' ', acc_type)

        # Currency, Lien, Balance
        currency = None
        lien_amt = None
        closing_bal = None
        
        fin_match = re.search(r'\b(INR|USD|EUR)\b\s+([\d,\.]+)\s+([\d,\.]+)', extracted_text)
        if fin_match:
            currency = fin_match.group(1).strip()
            lien_amt = fin_match.group(2).strip()
            closing_bal = fin_match.group(3).strip()
        else:
            currency = extract_bank_val(r'Currency', extracted_text)
            lien_amt = extract_bank_val(r'Lien\s+Amount', extracted_text)
            closing_bal = extract_bank_val(r'Closing\s+Balance', extracted_text)

        # Dates
        start_date = extract_bank_val(r'(?:Statement\s+(?:Start\s+)?Date|From\s+Date)', extracted_text)
        end_date = extract_bank_val(r'(?:Statement\s+(?:End\s+)?Date|To\s+Date)', extracted_text)
        period_match = re.search(r'Period:\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})\s*-\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})', extracted_text)
        if period_match:
            start_date = period_match.group(1).strip()
            end_date = period_match.group(2).strip()

        # IFSC Code
        ifsc_match = re.search(r'([A-Z]{4}0[A-Z0-9]{6})', extracted_text)
        ifsc = ifsc_match.group(1).strip() if ifsc_match else extract_bank_val(r'(?:IFSC\s*Code|IFSC)', extracted_text)
        
        # Bank Name Logic
        bank_name_match = re.search(r'Statement of Account\s*-\s*([A-Za-z\s]+)', extracted_text, re.IGNORECASE)
        bank_name = bank_name_match.group(1).strip() if bank_name_match else extract_bank_val(r'Bank\s+Name', extracted_text)
        
        if not bank_name and ifsc:
            if ifsc.startswith('INDB'): bank_name = 'IndusInd Bank'
            elif ifsc.startswith('SBIN'): bank_name = 'State Bank of India'
            elif ifsc.startswith('HDFC'): bank_name = 'HDFC Bank'
            elif ifsc.startswith('ICIC'): bank_name = 'ICICI Bank'
            elif ifsc.startswith('UTIB'): bank_name = 'Axis Bank'
            elif ifsc.startswith('PUNB'): bank_name = 'Punjab National Bank'
            elif ifsc.startswith('KKBK'): bank_name = 'Kotak Mahindra Bank'
            elif ifsc.startswith('BARB'): bank_name = 'Bank of Baroda'
            elif ifsc.startswith('IDIB'): bank_name = 'Indian Bank'
            elif ifsc.startswith('UBIN'): bank_name = 'Union Bank of India'
        
        # Branch Name Logic
        branch_name = extract_bank_val(r'(?:Branch\s+Name|Branch)', extracted_text)
        if branch_name and ('IFSC' in branch_name or re.search(r'^[A-Z0-9]+$', branch_name)):
            branch_name = None # Clear bad matches like M626875 or IFSC Code


        # Nomination
        nomination_match = re.search(r'Nomination\s+(?:Registered|Status)\s*[:\-]?\s*([A-Za-z]+)', extracted_text, re.IGNORECASE)
        nomination = nomination_match.group(1).strip() if nomination_match else extract_bank_val(r'Nomination\s+(?:Status|Registered)', extracted_text)

        # Mobile Number
        mobile_match = re.search(r'Mob\.No.*?([+0-9X\s]{10,})', extracted_text)
        mobile = mobile_match.group(1).strip() if mobile_match else extract_bank_val(r'(?:Mobile\s+Number|Mobile|Phone)', extracted_text)

        # Address
        address = extract_bank_val(r'(?:Customer\s+Address|Address)', extracted_text)
        if not address:
            address_match = re.search(r'Date:.*?\n(.*?)(?=\nMob\.No)', extracted_text, re.DOTALL)
            if address_match:
                address = address_match.group(1).replace('\n', ' ').strip()
                address = re.sub(r'\s+', ' ', address)
                address = re.sub(r'Period:\s*\d{1,2}\s+[A-Za-z]{3}\s+\d{4}\s*-\s*\d{1,2}\s+[A-Za-z]{3}\s+\d{4}', '', address).strip()
                address = re.sub(r'\s+', ' ', address).strip()

        # Opening Balance
        
        opening_bal = extract_bank_val(r'Opening\s+Balance', extracted_text)
        
        # Calculate Universal Totals (Debits/Withdrawals and Credits/Deposits)
        total_debit = extract_bank_val(r'(?:Total\s+Withdrawals?|Total\s+Debits?|Total\s+Amount\s+Debited)', extracted_text)
        total_credit = extract_bank_val(r'(?:Total\s+Deposits?|Total\s+Credits?|Total\s+Amount\s+Credited)', extracted_text)

        # Fallback: Mathematical accounting heuristics to sum up transaction lines
        if not total_debit or not total_credit:
            sum_dr = 0.0
            sum_cr = 0.0
            prev_bal = None
            
            lines = extracted_text.split('\n')
            for line in lines:
                # Remove dates so they don't get parsed as amounts
                clean_line = re.sub(r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}', '', line)
                clean_line = re.sub(r'\d{1,2}\s+[A-Za-z]{3}\s+\d{4}', '', clean_line)
                
                # Find all amounts (e.g. 12,345.50)
                amounts_str = re.findall(r'\b\d+[\d,]*\.\d{2}\b', clean_line)
                if len(amounts_str) >= 2:
                    amounts = [float(a.replace(',', '')) for a in amounts_str]
                    bal = amounts[-1]
                    txn_amt = amounts[0]
                    
                    if len(amounts) >= 3:
                        # Format: [Withdrawal, Deposit, Balance] or [Debit, Credit, Balance]
                        val1, val2 = amounts[-3], amounts[-2]
                        if val1 > 0 and val2 == 0:
                            sum_dr += val1
                        elif val2 > 0 and val1 == 0:
                            sum_cr += val2
                        else:
                            # Trust math if both are non-zero (rare)
                            if prev_bal is not None:
                                diff = bal - prev_bal
                                if abs(diff - txn_amt) < 0.1: sum_cr += txn_amt
                                elif abs(diff - (-txn_amt)) < 0.1: sum_dr += txn_amt
                    else:
                        # Format: [Amount, Balance]
                        if prev_bal is not None:
                            diff = bal - prev_bal
                            if abs(diff - txn_amt) < 0.1:
                                sum_cr += txn_amt
                            elif abs(diff - (-txn_amt)) < 0.1:
                                sum_dr += txn_amt
                            else:
                                # Fallback to text markers if math fails
                                if re.search(r'\bDR\b|DEBIT|WITHDRAWAL', line, re.IGNORECASE):
                                    sum_dr += txn_amt
                                elif re.search(r'\bCR\b|CREDIT|DEPOSIT', line, re.IGNORECASE):
                                    sum_cr += txn_amt
                        else:
                            # Fallback if no previous balance
                            if re.search(r'\bDR\b|DEBIT|WITHDRAWAL', line, re.IGNORECASE):
                                sum_dr += txn_amt
                            elif re.search(r'\bCR\b|CREDIT|DEPOSIT', line, re.IGNORECASE):
                                sum_cr += txn_amt
                                
                    prev_bal = bal
                elif len(amounts_str) == 1:
                    # OCR often drops the balance or splits it across lines.
                    # If we only have 1 amount on the line, we can't use math. 
                    # We MUST fallback to keywords.
                    txn_amt = float(amounts_str[0].replace(',', ''))
                    if re.search(r'\bDR\b|DEBIT|WITHDRAWAL', line, re.IGNORECASE):
                        sum_dr += txn_amt
                    elif re.search(r'\bCR\b|CREDIT|DEPOSIT', line, re.IGNORECASE):
                        sum_cr += txn_amt
                    elif re.search(r'UPI|IMPS|NEFT|RTGS', line, re.IGNORECASE):
                        # Extreme fallback: If it's a known payment type but no DR/CR marker,
                        # and no math to verify it, it's very likely a debit (purchases).
                        # We leave this out to avoid false positives, but we capture the ones with markers.
                        pass
                    
            if not total_debit and sum_dr > 0:
                total_debit = f"{sum_dr:,.2f}"
            if not total_credit and sum_cr > 0:
                total_credit = f"{sum_cr:,.2f}"

        # Populate structured data unconditionally so they always appear in the UI
        structured["Customer Name"] = cust_name or "Not Found"
        structured["Customer ID"] = cust_id or "Not Found"
        structured["Total Debit (Withdrawals)"] = total_debit or "Not Found"
        structured["Total Credit (Deposits)"] = total_credit or "Not Found"
 
        # Calculate Net Cash Flow
        try:
            td = float(total_debit.replace(',', '')) if total_debit else 0.0
            tc = float(total_credit.replace(',', '')) if total_credit else 0.0
            if td > 0 or tc > 0:
                net_flow = tc - td
                structured["Net Cash Flow"] = f"{net_flow:,.2f}"
            else:
                structured["Net Cash Flow"] = "Not Found"
        except:
            structured["Net Cash Flow"] = "Not Found"
        structured["Account Number"] = acc_num or "Not Found"
        structured["Account Type"] = acc_type or "Not Found"
        structured["Bank Name"] = bank_name or "Not Found"
        structured["Branch Name"] = branch_name or "Not Found"
        structured["IFSC Code"] = ifsc or "Not Found"
        structured["Account Holder Type"] = acc_holder_type or "Not Found"
        structured["Customer Address"] = address or "Not Found"
        structured["Mobile Number"] = mobile or "Not Found"
        structured["Currency"] = currency or "Not Found"
        structured["Statement Start Date"] = start_date or "Not Found"
        structured["Statement End Date"] = end_date or "Not Found"
        structured["Opening Balance"] = opening_bal or "Not Found"
        structured["Closing Balance"] = closing_bal or "Not Found"
        structured["Lien Amount"] = lien_amt or "Not Found"
        structured["Nomination Status"] = nomination or "Not Found"

    elif doc_type == "UDYAM" or "UDYAM" in doc_type:
        pan_match = re.search(r'[A-Z]{5}[0-9]{4}[A-Z]{1}', extracted_text)
        pan = pan_match.group(0) if pan_match else None
        
        # Advanced extraction for Udyam Certificates
        udyam_match = re.search(r'\bUDYAM-[A-Z]{2}-\d{2}-\d{7}\b', extracted_text)
        udyam_number = udyam_match.group(0) if udyam_match else None
        
        udyam_type_match = re.search(r'\b(Micro|Small|Medium)\b', extracted_text, re.IGNORECASE)
        udyam_type = udyam_type_match.group(0).capitalize() if udyam_type_match else None
        
        udyam_activity_match = re.search(r'\b(Manufacturing|Services|Trading)\b', extracted_text, re.IGNORECASE)
        udyam_activity = udyam_activity_match.group(0).capitalize() if udyam_activity_match else None
        
        udyam_org_match = re.search(r'(?i)(Propriet\w+|Partnership|Private Limited|Public Limited|LLP|Society|Trust|HUF)', extracted_text)
        udyam_org_type = udyam_org_match.group(0).capitalize() if udyam_org_match else None
        
        udyam_email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', extracted_text)
        udyam_email = udyam_email_match.group(0) if udyam_email_match else None
        
        udyam_mobile_match = re.search(r'\b[6-9]\d{9}\b', extracted_text)
        udyam_mobile = udyam_mobile_match.group(0) if udyam_mobile_match else None
        
        udyam_category_match = re.search(r'\b(General|OBC|SC|ST)\b', extracted_text, re.IGNORECASE)
        udyam_category = udyam_category_match.group(0).capitalize() if udyam_category_match else None
        
        udyam_gender_match = re.search(r'(?i)(Male|Female|Transgender)', extracted_text)
        udyam_gender = udyam_gender_match.group(0).capitalize() if udyam_gender_match else None
        
        def extract_short_text(text, start_label, max_length=60):
            start_idx = text.lower().find(start_label.lower())
            if start_idx == -1: return None
            start_idx += len(start_label)
            
            chunk = text[start_idx:start_idx+150].strip()
            chunk = re.sub(r'^[\s:\-,|]+', '', chunk)
            
            lines = re.split(r'\n|  +', chunk)
            if lines:
                val = lines[0].strip()
                val = re.sub(r'(?i)\b(Type|Major|Social|Gender|Mobile|Email|Date|PAN|Do you|Specially|Is ITR|Unit|Official)\b.*', '', val)
                return val.strip()[:max_length].strip()
            return None
            
        udyam_name = extract_short_text(extracted_text, "Name of Enterprise")
        udyam_owner = extract_short_text(extracted_text, "Owner")
        
        dates = re.findall(r'\b\d{2}/\d{2}/\d{4}\b', extracted_text)
        udyam_incorporation = dates[0] if len(dates) > 0 else None
        udyam_commencement = dates[1] if len(dates) > 1 else None
        udyam_registration_date = dates[2] if len(dates) > 2 else None
        
        def extract_yes_no(text, keyword):
            idx = text.lower().find(keyword.lower())
            if idx != -1:
                chunk = text[idx:idx+30]
                if re.search(r'(?i)(yes|ycs|ye)', chunk): return "Yes"
                if re.search(r'(?i)(no|n0)', chunk): return "No"
            return None
            
        udyam_has_gstin = extract_yes_no(extracted_text, "GSTIN")
        udyam_specially_abled = extract_yes_no(extracted_text, "DIVYANG")
        if not udyam_specially_abled: udyam_specially_abled = extract_yes_no(extracted_text, "Specially Abled")
        
        # Resilient Units Extraction - search entire text for "1 | NAME" or "2. | NAME"
        udyam_units = []
        unit_matches = re.finditer(r'\b(\d{1,2})[\s\.\|]+([A-Z][A-Z\s]+)(?=\n|$|Flat|Village|OFFICAL)', extracted_text)
        seen_units = set()
        for match in unit_matches:
            unit_num = match.group(1)
            unit_name = match.group(2).strip()
            # Clean up trailing noise
            unit_name = re.sub(r'\s*\|.*', '', unit_name).strip()
            if len(unit_name) > 3 and unit_name not in seen_units:
                udyam_units.append(f"Unit {unit_num}: {unit_name}")
                seen_units.add(unit_name)
                
        # Resilient Investment Extraction - search entire text for "2024-25 Micro 08/04/2024"
        udyam_investment = []
        invest_matches = re.finditer(r'\b(20\d{2}-\d{2}[\s\|A-Za-z]+?\d{2}/\d{2}/\d{4})\b', extracted_text)
        for match in invest_matches:
            inv_text = match.group(1).strip()
            # Clean up pipe characters and excess spaces
            inv_text = re.sub(r'[\|]+', ' ', inv_text)
            inv_text = re.sub(r'\s+', ' ', inv_text)
            if inv_text not in udyam_investment:
                udyam_investment.append(inv_text)
        
        # Specific Extraction for Bank Details
        bank_name = None
        ifs_code = None
        bank_acc_num = None
        
        bank_match = re.search(r'([A-Za-z\s]+?)[\s\|\n]+([A-Z]{4}0[A-Z0-9]{6})[\s\|\n]+(\d{9,18})', extracted_text)
        if bank_match:
            b_name = re.sub(r'^[\s\|\n]+', '', bank_match.group(1)).strip()
            # Clean up if it grabbed too much text before the bank name
            b_name = b_name.split('\n')[-1].strip()
            # Remove header leftovers if any
            b_name = re.sub(r'(?i)\b(Bank Name|IFS Code|Bank Account Number|Bank Details)\b', '', b_name).strip()
            if b_name: bank_name = b_name
            ifs_code = bank_match.group(2)
            bank_acc_num = bank_match.group(3)
        else:
            # Fallback to block extraction if strict regex fails
            udyam_bank = extract_between(extracted_text, "Bank Account Number", ["Employment Details", "Unit(s) Details", "Investment in Plant"])
            if not udyam_bank: udyam_bank = extract_between(extracted_text, "Bank Details", ["Employment Details", "Unit(s) Details"])

        
        udyam_address = extract_between(extracted_text, "Official address of Enterprise", ["Latitude", "Disclaimer", "Printed"])
        if not udyam_address: udyam_address = extract_between(extracted_text, "Name of Premises/", ["Latitude", "Disclaimer"])
        
        if pan: structured["PAN Number"] = pan
        if udyam_number: structured["Udyam Number"] = udyam_number
        if udyam_name: structured["Name of Enterprise"] = udyam_name
        if udyam_type: structured["Type of Enterprise"] = udyam_type
        if udyam_activity: structured["Major Activity"] = udyam_activity
        if udyam_org_type: structured["Type of Organisation"] = udyam_org_type
        if udyam_owner: structured["Owner Name"] = udyam_owner
        if udyam_has_gstin: structured["Has GSTIN"] = udyam_has_gstin
        if udyam_mobile: structured["Mobile Number"] = udyam_mobile
        if udyam_email: structured["Email ID"] = udyam_email
        if udyam_category: structured["Social Category"] = udyam_category
        if udyam_gender: structured["Gender"] = udyam_gender
        if udyam_specially_abled: structured["Specially Abled"] = udyam_specially_abled
        if udyam_incorporation: structured["Date of Incorporation"] = udyam_incorporation
        if udyam_commencement: structured["Date of Commencement"] = udyam_commencement
        if udyam_registration_date: structured["Date of Udyam Registration"] = udyam_registration_date
        if bank_name: structured["Bank Name"] = bank_name
        if ifs_code: structured["IFS Code"] = ifs_code
        if bank_acc_num: structured["Bank Account Number"] = bank_acc_num
        elif udyam_bank: structured["Bank Details"] = udyam_bank
        if udyam_investment: structured["Investment Data"] = "\n\n".join(udyam_investment)
        if udyam_units: structured["Units Data"] = "\n\n".join(udyam_units)
        if udyam_address: structured["Official Address"] = udyam_address
        
    with open("ocr_debug.log", "w") as f:
        f.write(f"units_block_idx: {locals().get('units_block_idx')}\n")
        f.write(f"invest_block_idx: {locals().get('invest_block_idx')}\n")
        f.write(f"udyam_units: {locals().get('udyam_units')}\n")
        f.write(f"udyam_investment: {locals().get('udyam_investment')}\n")
        f.write(f"structured_data: {structured}\n")
        f.write(f"raw_text:\n{extracted_text}\n")
    
    # Save or update OCR result
    existing_ocr = db.query(OCRResult).filter(OCRResult.document_id == document_id).first()
    if existing_ocr:
        existing_ocr.raw_text = extracted_text.strip()
        existing_ocr.structured_data = structured
        ocr_result = existing_ocr
    else:
        ocr_result = OCRResult(
            document_id=document_id,
            raw_text=extracted_text.strip(),
            structured_data=structured,
            confidence=0.9,
            language="en"
        )
        db.add(ocr_result)
        
    doc.ocr_status = "COMPLETED"
    db.commit()
    db.refresh(ocr_result)
    
    return ocr_result
