from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
import os
import time
import shutil
from fastapi.responses import StreamingResponse
from io import BytesIO
from typing import List
from sqlalchemy.orm import Session
from database import get_db
import crud.business as crud_business
from routes.auth import get_current_user
from models.user import User
from schemas.business_tools import (
    InvoiceRequest, QuotationRequest, ReceiptRequest, BusinessCardRequest,
    ProductCreate, ProductResponse, InventoryAdd, InventoryResponse,
    SalesTrackerRequest, ExpenseManagerRequest,
    ProfitCalculatorRequest, AnalyticsRequest, POSCheckoutRequest,
    PurchaseInvoiceRequest, StockMovementResponse, GSTMasterResponse
)
import random
import string
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.graphics.barcode import code128
    from reportlab.platypus import Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    REPORTLAB_INSTALLED = True
except ImportError:
    REPORTLAB_INSTALLED = False

router = APIRouter()

@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    ext = file.filename.split(".")[-1]
    filename = f"image_{int(time.time())}_{current_user.id}.{ext}"
    filepath = os.path.join("uploads", filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # The frontend will hit this endpoint which is at /business-tools/upload-image
    # We return just the relative URL or path to be appended to baseUrl
    return {"url": f"/uploads/{filename}"}

def ensure_reportlab():
    if not REPORTLAB_INSTALLED:
        raise HTTPException(status_code=500, detail="PDF Generation module (reportlab) is not installed. Please run: ./venv/bin/pip install reportlab")

# 1. Invoice Generator
def num2words(amount):
    def convert_whole(num):
        if num == 0:
            return "Zero"
        ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
        
        def helper(n):
            if n < 20:
                return ones[n]
            elif n < 100:
                return tens[n // 10] + (" " + ones[n % 10] if n % 10 != 0 else "")
            elif n < 1000:
                return ones[n // 100] + " Hundred" + (" and " + helper(n % 100) if n % 100 != 0 else "")
            elif n < 100000:
                return helper(n // 1000) + " Thousand" + (" " + helper(n % 1000) if n % 1000 != 0 else "")
            elif n < 10000000:
                return helper(n // 100000) + " Lakh" + (" " + helper(n % 100000) if n % 100000 != 0 else "")
            else:
                return helper(n // 10000000) + " Crore" + (" " + helper(n % 10000000) if n % 10000000 != 0 else "")
                
        return helper(int(num))

    try:
        amount_float = float(amount)
        rupees = int(amount_float)
        paise = int(round((amount_float - rupees) * 100))
        
        words = convert_whole(rupees) + " Rupees"
        if paise > 0:
            words += " and " + convert_whole(paise) + " Paise"
        return words + " Only"
    except Exception:
        return f"Rupees {amount} Only"

@router.post("/invoice-generator")
def generate_invoice(req: InvoiceRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_reportlab()
    
    # 1. Save to DB
    total_amount = sum((item.quantity * item.unit_price) * (1 + ((item.gst_rate or 0)/100 if req.is_gst_invoice else 0)) for item in req.items)
    
    db_invoice = {
        "invoice_number": req.invoice_number,
        "invoice_date": req.invoice_date,
        "client_name": req.client_name,
        "is_gst_invoice": req.is_gst_invoice,
        "total_amount": total_amount,
        "items_json": [item.dict() for item in req.items]
    }
    crud_business.create_invoice_record(db, db_invoice, user_id=current_user.id)
    
    # 1.1 Save Client Details
    if req.client_name and req.client_name.strip():
        from models.business import Client
        # Check if client exists by phone or name
        client_q = db.query(Client).filter(Client.user_id == current_user.id)
        if req.client_phone:
            client_record = client_q.filter(Client.phone == req.client_phone).first()
        else:
            client_record = client_q.filter(Client.name == req.client_name).first()
            
        if not client_record:
            client_record = Client(
                user_id=current_user.id,
                name=req.client_name,
                phone=req.client_phone,
                address=req.client_address,
                gstin=req.client_gstin,
                company_name=req.client_company_name
            )
            db.add(client_record)
            db.commit()
        else:
            # Update missing info
            updated = False
            if req.client_address and not client_record.address:
                client_record.address = req.client_address
                updated = True
            if req.client_gstin and not client_record.gstin:
                client_record.gstin = req.client_gstin
                updated = True
            if req.client_company_name and not client_record.company_name:
                client_record.company_name = req.client_company_name
                updated = True
                
            if updated:
                db.commit()
    
    # Sales and stock decrement are now deferred to end of day sync (Sales Tracker)
    # just return PDF

    # 2. Generate PDF using advanced layout
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Outer Box
    margin = 20
    c.setLineWidth(1)
    c.rect(margin, margin, width - 2*margin, height - 2*margin)
    
    # Title
    c.setFont("Helvetica-Bold", 10)
    title = "TAX INVOICE" if req.is_gst_invoice else "INVOICE"
    c.drawCentredString(width/2, height - 35, title)
    
    # Header Line
    c.line(margin, height - 45, width - margin, height - 45)
    
    # Company Info (Center)
    y_company = height - 65
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, y_company, req.company_name.upper())
    
    y_company -= 15
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2, y_company, req.company_address)
    
    y_company -= 15
    contact_str = ""
    if req.company_phone: contact_str += f"Ph: {req.company_phone}  "
    if req.company_whatsapp: contact_str += f"WA: {req.company_whatsapp}"
    if contact_str:
        c.drawCentredString(width/2, y_company, contact_str)
        y_company -= 15
        
    # GSTIN Right
    if req.company_gstin and req.is_gst_invoice:
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(width - margin - 10, height - 65, f"GSTIN: {req.company_gstin.upper()}")
        
    # Handle Logo (Top Left)
    if req.company_logo_url:
        from urllib.parse import urlparse
        path = urlparse(req.company_logo_url).path
        # Sometimes path may be just /uploads/... or could be a full URL
        if path.startswith("/uploads/"):
            local_path = "." + path
        else:
            local_path = req.company_logo_url # Try direct if it's already a local path
            
        if os.path.exists(local_path):
            c.drawImage(local_path, margin + 10, height - 100, width=50, height=50, preserveAspectRatio=True)
    
    # Divider below header
    y = height - 110
    c.line(margin, y, width - margin, y)
    
    # Client Info (Left) and Invoice Info (Right)
    # Vertical Line for Details Box
    mid_x = width/2 + 50
    c.line(mid_x, y, mid_x, y - 80)
    
    # Client Details
    c.setFont("Helvetica-Bold", 11)
    client_name_str = req.client_company_name.upper() if req.client_company_name else req.client_name.upper()
    c.drawString(margin + 10, y - 15, client_name_str)
    
    c.setFont("Helvetica", 10)
    c.drawString(margin + 10, y - 30, req.client_address)
    y_client = y - 45
    if req.client_phone:
        c.drawString(margin + 10, y_client, f"Ph: {req.client_phone}")
        y_client -= 15
        
    if req.is_gst_invoice and req.client_gstin:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margin + 10, y_client, f"GSTIN: {req.client_gstin.upper()}")
        
    # Invoice Details
    x_inv = mid_x + 10
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x_inv, y - 15, "Inv No.")
    c.drawString(x_inv + 60, y - 15, str(req.invoice_number))
    
    c.drawString(x_inv, y - 30, "Date")
    c.drawString(x_inv + 60, y - 30, str(req.invoice_date))
    
    c.setFont("Helvetica", 10)
    if req.notes:
        c.drawString(x_inv, y - 45, "Notes:")
        c.drawString(x_inv + 60, y - 45, str(req.notes)[:25])
        
    y -= 80
    
    # Items Table
    headers = ["S.No", "Description", "HSN", "Qty", "Unit", "Rate"]
    show_gst = req.is_gst_invoice or req.pricing_mode.upper() == "EXCLUSIVE"
    
    if show_gst:
        headers.extend(["GST%", "Amount"])
    else:
        headers.extend(["Amount"])
        
    data = [headers]
    
    subtotal = 0
    total_tax = 0
    total_qty = 0
    
    # Pre-calculate item bases to distribute invoice discount
    item_bases = []
    total_base_amount = 0
    total_item_discounts = 0
    
    for item in req.items:
        qty = item.quantity
        price = item.unit_price
        item_discount = 0
        if item.discount_type == "PERCENTAGE":
            item_discount = (qty * price) * ((item.discount_value or 0) / 100)
        elif item.discount_type == "AMOUNT":
            item_discount = item.discount_value or 0
        base = (qty * price) - item_discount
        item_bases.append({"base": base, "discount": item_discount})
        total_base_amount += base
        total_item_discounts += item_discount
        
    invoice_discount_amount = 0
    if req.invoice_discount_type == "PERCENTAGE":
        invoice_discount_amount = total_base_amount * ((req.invoice_discount_value or 0) / 100)
    elif req.invoice_discount_type == "AMOUNT":
        invoice_discount_amount = req.invoice_discount_value or 0
        
    # For GST Summary footer
    gst_summary = {0: {'tax': 0, 'taxable': 0}, 5: {'tax': 0, 'taxable': 0}, 12: {'tax': 0, 'taxable': 0}, 18: {'tax': 0, 'taxable': 0}, 28: {'tax': 0, 'taxable': 0}} 
    
    for idx, item in enumerate(req.items, start=1):
        gst = getattr(item, "gst_rate", 0) or 0
        qty = item.quantity
        price = item.unit_price
        
        # Proportional invoice discount
        ratio = item_bases[idx-1]["base"] / total_base_amount if total_base_amount > 0 else 0
        item_inv_discount = invoice_discount_amount * ratio
        
        final_taxable_base = item_bases[idx-1]["base"] - item_inv_discount
        
        if show_gst:
            if req.pricing_mode.upper() == "WITHOUT_GST":
                tax = 0
                taxable_value = final_taxable_base
                amt = final_taxable_base
            else:
                # EXCLUSIVE
                tax = final_taxable_base * (gst / 100)
                taxable_value = final_taxable_base
                amt = final_taxable_base + tax
        else:
            tax = 0
            taxable_value = final_taxable_base
            amt = final_taxable_base
        
        subtotal += final_taxable_base
        total_tax += tax
        total_qty += qty
        
        if gst not in gst_summary:
            gst_summary[gst] = {'tax': 0, 'taxable': 0}
            
        gst_summary[gst]['tax'] += tax
        gst_summary[gst]['taxable'] += taxable_value
            
        row = [
            str(idx),
            item.description,
            item.hsn_code or "",
            str(item.quantity),
            getattr(item, 'unit', 'Piece'),
            f"{item.unit_price:.2f}"
        ]
        if show_gst:
            row.extend([f"{gst}%", f"{amt:.2f}"])
        else:
            row.extend([f"{amt:.2f}"])
            
        data.append(row)
        
    # Calculate column widths
    if show_gst:
        colWidths = [30, 200, 50, 40, 45, 60, 40, 90]
    else:
        colWidths = [30, 240, 60, 45, 50, 65, 65]
        
    table = Table(data, colWidths=colWidths)
    
    style_cmds = [
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (1,1), (1,-1), 'LEFT'), # Left align description
        ('ALIGN', (-1,1), (-1,-1), 'RIGHT'), # Right align amount
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]
    table.setStyle(TableStyle(style_cmds))
    
    table.wrapOn(c, width, height)
    table_height = table._height
    
    # We want the table to stretch downwards to a fixed footer point if possible,
    # but for now, we just draw it and draw lines down to the footer.
    table_y = y - table_height
    table.drawOn(c, margin, table_y)
    
    # Draw vertical grid lines extending to footer
    footer_y = margin + 260
    # Actually, simpler to just use table as is, and have empty space below it.
    
    # Divider for footer
    c.line(margin, footer_y, width - margin, footer_y)
    
    # Footer Layout
    # Split into left (Bank details) and right (Totals)
    footer_mid_x = width - 200
    c.line(footer_mid_x, footer_y, footer_mid_x, margin)
    
    # Left Side: Bank Details
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin + 10, footer_y - 15, "OUR BANK DETAILS:")
    c.setFont("Helvetica", 9)
    
    bx = margin + 10
    by = footer_y - 30
    if hasattr(req, 'bank_name') and req.bank_name:
        c.drawString(bx, by, f"Bank Name: {req.bank_name}")
        by -= 15
    if hasattr(req, 'account_number') and req.account_number:
        c.drawString(bx, by, f"A/C No: {req.account_number}")
        by -= 15
    if hasattr(req, 'ifsc_code') and req.ifsc_code:
        c.drawString(bx, by, f"IFSC: {req.ifsc_code}")
        by -= 15
    if hasattr(req, 'bank_branch') and req.bank_branch:
        c.drawString(bx, by, f"Branch: {req.bank_branch}")
        
    # Amount in Words (below bank details)
    by -= 20
    c.setFont("Helvetica", 9)
    grand_total = subtotal + total_tax
    c.drawString(bx, by, f"Amount in Words: {num2words(grand_total)}")
    
    # Total Items
    c.drawString(bx, margin + 10, f"Total Items: {len(req.items)}   Total Qty: {total_qty}")
    
    # Right Side: Totals
    x_totals = footer_mid_x + 10
    val_x = width - margin - 10
    c.setFont("Helvetica", 9)
    
    gross_total = sum(item.quantity * item.unit_price for item in req.items)
    total_discount = total_item_discounts + invoice_discount_amount
    
    ty = footer_y - 15
    if total_discount > 0:
        c.drawString(x_totals, ty, "Gross Amount:")
        c.drawRightString(val_x, ty, f"{gross_total:.2f}")
        ty -= 15
        c.drawString(x_totals, ty, "Total Discount:")
        c.drawRightString(val_x, ty, f"-{total_discount:.2f}")
        ty -= 15
        c.drawString(x_totals, ty, "Taxable Value:")
        c.drawRightString(val_x, ty, f"{subtotal:.2f}")
    else:
        c.drawString(x_totals, ty, "Sub Total:")
        c.drawRightString(val_x, ty, f"{subtotal:.2f}")
    
    if show_gst:
        for rate, values in sorted(gst_summary.items()):
            if values['tax'] > 0:
                tax_half = values['tax'] / 2
                
                ty -= 15
                c.drawString(x_totals, ty, f"CGST @ {rate/2}%:")
                c.drawRightString(val_x, ty, f"{tax_half:.2f}")
                
                ty -= 15
                c.drawString(x_totals, ty, f"SGST @ {rate/2}%:")
                c.drawRightString(val_x, ty, f"{tax_half:.2f}")
                
        ty -= 20
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x_totals, ty, "Total GST:")
        c.drawRightString(val_x, ty, f"{total_tax:.2f}")
        c.setFont("Helvetica", 9)
        
    ty -= 30
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x_totals, ty, "GRAND TOTAL:")
    c.drawRightString(val_x, ty, f"{grand_total:.2f}")
    
    # Signature fixed position at the bottom of the box
    sig_y = margin + 15
    c.setFont("Helvetica", 8)
    c.drawRightString(val_x, sig_y + 15, f"For {req.company_name.upper()}")
    c.drawRightString(val_x, sig_y, "Authorized Signatory")
    
    c.showPage()
    c.save()
    
    buffer.seek(0)
    filename = f"invoice_{int(time.time())}_{current_user.id}.pdf"
    filepath = os.path.join("uploads", filename)
    with open(filepath, "wb") as f:
        f.write(buffer.getvalue())
        
    return {"pdf_url": f"/uploads/{filename}"}

# 2. GST Billing
@router.post("/gst-billing")
def generate_gst_bill(req: InvoiceRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    req.is_gst_invoice = True
    return generate_invoice(req, current_user, db)

# POS Checkout
@router.post("/pos-checkout")
def generate_pos_receipt(req: POSCheckoutRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_reportlab()
    
    # Override from profile if missing
    comp_name = req.company_name or current_user.company_name or "My Store"
    comp_address = req.company_address or current_user.company_address or ""
    comp_phone = req.company_phone or current_user.phone_number or ""
    comp_gstin = req.company_gstin or current_user.gst_number or ""
    
    total_amount = 0
    total_qty = 0
    total_base_amount = 0
    total_item_discounts = 0
    item_bases = []
    
    for item in req.items:
        total_qty += item.quantity
        qty = item.quantity
        price = item.unit_price
        
        item_discount = 0
        if getattr(item, "discount_type", None) == "PERCENTAGE":
            item_discount = (qty * price) * (getattr(item, "discount_value", 0) / 100)
        elif getattr(item, "discount_type", None) == "AMOUNT":
            item_discount = getattr(item, "discount_value", 0)
            
        base = (qty * price) - item_discount
        item_bases.append({"base": base, "discount": item_discount})
        total_base_amount += base
        total_item_discounts += item_discount

    invoice_discount_amount = 0
    if getattr(req, "invoice_discount_type", None) == "PERCENTAGE":
        invoice_discount_amount = total_base_amount * (getattr(req, "invoice_discount_value", 0) / 100)
    elif getattr(req, "invoice_discount_type", None) == "AMOUNT":
        invoice_discount_amount = getattr(req, "invoice_discount_value", 0)
        
    for idx, item in enumerate(req.items):
        gst = getattr(item, "gst_rate", 0) or 0
        ratio = item_bases[idx]["base"] / total_base_amount if total_base_amount > 0 else 0
        item_inv_discount = invoice_discount_amount * ratio
        final_taxable_base = item_bases[idx]["base"] - item_inv_discount
        
        if req.pricing_mode.upper() == "WITHOUT_GST":
            total_amount += final_taxable_base
        else:
            total_amount += final_taxable_base * (1 + gst / 100)

    if getattr(req, "receipt_size", "Thermal") == "A4":
        inv_req = InvoiceRequest(
            company_name=comp_name,
            company_address=comp_address,
            company_phone=comp_phone,
            company_gstin=comp_gstin,
            company_whatsapp=current_user.whatsapp_number,
            company_logo_url=current_user.company_logo_url,
            bank_name=current_user.bank_name,
            account_name=current_user.account_name,
            account_number=current_user.account_number,
            ifsc_code=current_user.ifsc_code,
            client_name=req.customer_name or "Walk-in Customer",
            client_address="",
            client_phone=req.customer_phone,
            invoice_number=req.receipt_number,
            invoice_date=req.receipt_date,
            items=req.items,
            is_gst_invoice=False,
            pricing_mode=req.pricing_mode,
            invoice_discount_type=req.invoice_discount_type,
            invoice_discount_value=req.invoice_discount_value
        )
        return generate_invoice(inv_req, current_user, db)

    # 1.5 Save Client Details for Thermal POS
    if req.customer_name and req.customer_name.strip():
        from models.business import Client
        client_q = db.query(Client).filter(Client.user_id == current_user.id)
        if req.customer_phone:
            client_record = client_q.filter(Client.phone == req.customer_phone).first()
        else:
            client_record = client_q.filter(Client.name == req.customer_name).first()
            
        if not client_record:
            client_record = Client(
                user_id=current_user.id,
                name=req.customer_name,
                phone=req.customer_phone,
            )
            db.add(client_record)
            db.commit()
        else:
            if req.customer_phone and not client_record.phone:
                client_record.phone = req.customer_phone
                db.commit()

    # 2. Generate Thermal Receipt PDF
    buffer = BytesIO()
    
    # Calculate dynamic height based on number of items
    WIDTH = 226
    
    gst_rates = set(getattr(item, "gst_rate", 0) or 0 for item in req.items if (getattr(item, "gst_rate", 0) or 0) > 0)
    HEIGHT = 280 + (len(req.items) * 30) + (len(gst_rates) * 15)
    if HEIGHT < 400: HEIGHT = 400
    
    c = canvas.Canvas(buffer, pagesize=(WIDTH, HEIGHT))
    
    margin = 10
    
    y = HEIGHT - 20
    
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(WIDTH/2, y, comp_name.upper())
    y -= 15
    
    c.setFont("Helvetica", 9)
    if comp_address:
        c.drawCentredString(WIDTH/2, y, comp_address)
        y -= 12
    if comp_phone:
        c.drawCentredString(WIDTH/2, y, f"Ph: {comp_phone}")
        y -= 12
    if comp_gstin:
        c.drawCentredString(WIDTH/2, y, f"GSTIN: {comp_gstin.upper()}")
        y -= 15
        
    c.line(margin, y, WIDTH - margin, y)
    y -= 15
    
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(WIDTH/2, y, "CASH RECEIPT" if req.payment_mode.lower() == "cash" else "PAYMENT RECEIPT")
    y -= 15
    
    c.setFont("Helvetica", 8)
    c.drawString(margin, y, f"Receipt No: {req.receipt_number}")
    c.drawRightString(WIDTH - margin, y, f"Date: {req.receipt_date}")
    y -= 12
    if req.customer_name:
        c.drawString(margin, y, f"Customer: {req.customer_name}")
        y -= 12
    if getattr(req, "customer_phone", None):
        c.drawString(margin, y, f"Phone: {req.customer_phone}")
        y -= 12
        
    c.line(margin, y, WIDTH - margin, y)
    y -= 15
    
    # Items
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin, y, "Item")
    c.drawRightString(WIDTH - margin, y, "Amount")
    y -= 10
    c.line(margin, y, WIDTH - margin, y)
    y -= 15
    
    c.setFont("Helvetica", 8)
    subtotal = 0
    gst_breakdown = {}
    
    for idx, item in enumerate(req.items):
        # Description might be long, truncate it
        desc = item.description[:25] + ".." if len(item.description) > 27 else item.description
        c.drawString(margin, y, desc)
        
        gst = getattr(item, "gst_rate", 0) or 0
        qty = item.quantity
        price = item.unit_price
        
        ratio = item_bases[idx]["base"] / total_base_amount if total_base_amount > 0 else 0
        item_inv_discount = invoice_discount_amount * ratio
        final_taxable_base = item_bases[idx]["base"] - item_inv_discount
        
        if req.pricing_mode.upper() == "WITHOUT_GST":
            tax = 0
            unit_display = price
        else:
            tax = final_taxable_base * (gst / 100)
            unit_display = price
            
        subtotal += final_taxable_base
        if gst > 0:
            gst_breakdown[gst] = gst_breakdown.get(gst, 0) + tax
        
        c.drawRightString(WIDTH - margin, y, f"{final_taxable_base:.2f}")
        y -= 12
        
        c.setFont("Helvetica", 7)
        c.drawString(margin + 10, y, f"Qty: {qty} x Rate: {unit_display:.2f}")
        c.setFont("Helvetica", 8)
        y -= 15
        
    c.line(margin, y, WIDTH - margin, y)
    y -= 15
    
    c.setFont("Helvetica", 9)
    c.drawString(margin, y, "Subtotal:")
    c.drawRightString(WIDTH - margin, y, f"{subtotal:.2f}")
    y -= 15
    
    for rate, tax_amt in sorted(gst_breakdown.items()):
        if tax_amt > 0:
            c.setFont("Helvetica", 8)
            c.drawString(margin, y, f"GST @ {rate}%:")
            c.drawRightString(WIDTH - margin, y, f"{tax_amt:.2f}")
            y -= 12
            
    total_savings = total_item_discounts + invoice_discount_amount
    if total_savings > 0:
        c.setFont("Helvetica-Bold", 8)
        c.drawString(margin, y, "Total Savings:")
        c.drawRightString(WIDTH - margin, y, f"Rs {total_savings:.2f}")
        y -= 12
        
    y -= 3
    c.line(margin, y, WIDTH - margin, y)
    y -= 15
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "GRAND TOTAL:")
    c.drawRightString(WIDTH - margin, y, f"Rs {total_amount:.2f}")
    y -= 15
    
    c.setFont("Helvetica", 8)
    c.drawString(margin, y, f"Total Items: {len(req.items)} | Qty: {total_qty}")
    c.drawRightString(WIDTH - margin, y, f"Mode: {req.payment_mode}")
    y -= 25
    
    c.setFont("Helvetica", 8)
    c.drawCentredString(WIDTH/2, y, "Thank you for your visit!")
    
    c.showPage()
    c.save()
    
    buffer.seek(0)
    filename = f"pos_receipt_{int(time.time())}_{current_user.id}.pdf"
    filepath = os.path.join("uploads", filename)
    with open(filepath, "wb") as f:
        f.write(buffer.getvalue())
        
    return {"pdf_url": f"/uploads/{filename}"}

# 3. Quotation Gen
@router.post("/quotation-gen")
def generate_quotation(req: QuotationRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_reportlab()
    
    # Save to DB
    total_amount = sum(item.quantity * item.unit_price for item in req.items)
    db_quote = {
        "quotation_number": req.quotation_number,
        "valid_until": req.valid_until,
        "client_name": req.client_name,
        "total_amount": total_amount,
        "items_json": [item.dict() for item in req.items]
    }
    crud_business.create_quotation_record(db, db_quote, user_id=current_user.id)
    
    # Generate PDF
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 50, "QUOTATION / ESTIMATE")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, req.company_name)
    c.drawString(400, height - 80, f"Quote #: {req.quotation_number}")
    c.drawString(400, height - 95, f"Valid Until: {req.valid_until}")
    
    y = height - 200
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Description")
    c.drawString(320, y, "Qty")
    c.drawString(400, y, "Unit Price")
    c.drawString(500, y, "Total")
    y -= 20
    c.setFont("Helvetica", 10)
    
    total = 0
    for item in req.items:
        line_tot = item.quantity * item.unit_price
        total += line_tot
        c.drawString(50, y, item.description)
        c.drawString(320, y, str(item.quantity))
        c.drawString(400, y, f"{item.unit_price:.2f}")
        c.drawString(500, y, f"{line_tot:.2f}")
        y -= 20
        
    c.setFont("Helvetica-Bold", 12)
    c.drawString(400, y - 20, f"Estimated Total: {total:.2f}")
    
    c.showPage()
    c.save()
    buffer.seek(0)
    filename = f"quote_{int(time.time())}_{current_user.id}.pdf"
    filepath = os.path.join("uploads", filename)
    with open(filepath, "wb") as f:
        f.write(buffer.getvalue())
    return {"pdf_url": f"/uploads/{filename}"}

# 4. Receipt Gen
@router.get("/gst-master", response_model=List[GSTMasterResponse])
def get_gst_master(db: Session = Depends(get_db)):
    from models.business import GSTMaster
    return db.query(GSTMaster).order_by(GSTMaster.gst_rate.asc()).all()

@router.post("/receipt-gen")
def generate_receipt(req: ReceiptRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_reportlab()
    
    # Save to DB
    db_receipt = {
        "receipt_number": req.receipt_number,
        "receipt_date": req.receipt_date,
        "received_from": req.received_from,
        "amount": req.amount,
        "payment_mode": req.payment_mode,
        "purpose": req.purpose
    }
    crud_business.create_receipt_record(db, db_receipt, user_id=current_user.id)
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 50, "PAYMENT RECEIPT")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, req.company_name)
    c.drawString(400, height - 80, f"Receipt #: {req.receipt_number}")
    c.drawString(400, height - 95, f"Date: {req.receipt_date}")
    
    c.drawString(50, height - 150, f"Received from: {req.received_from}")
    c.drawString(50, height - 170, f"Amount Received: {req.amount:.2f}")
    c.drawString(50, height - 190, f"Payment Mode: {req.payment_mode}")
    c.drawString(50, height - 210, f"Purpose: {req.purpose}")
    
    if req.transaction_id:
        c.drawString(50, height - 230, f"Transaction ID: {req.transaction_id}")
        
    c.showPage()
    c.save()
    buffer.seek(0)
    filename = f"receipt_{int(time.time())}_{current_user.id}.pdf"
    filepath = os.path.join("uploads", filename)
    with open(filepath, "wb") as f:
        f.write(buffer.getvalue())
    return {"pdf_url": f"/uploads/{filename}"}

# 5. Business Card
@router.post("/business-card")
def generate_business_card(req: BusinessCardRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_reportlab()
    
    # Save to DB
    crud_business.upsert_business_card(db, req.dict(), user_id=current_user.id)
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(3.5*inch, 2*inch))
    
    c.setFillColorRGB(0.9, 0.9, 0.9)
    c.rect(0, 0, 3.5*inch, 2*inch, fill=1)
    
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(0.2*inch, 1.6*inch, req.name)
    
    c.setFont("Helvetica", 10)
    c.drawString(0.2*inch, 1.4*inch, req.job_title)
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(0.2*inch, 1.1*inch, req.company_name)
    
    c.setFont("Helvetica", 8)
    c.drawString(0.2*inch, 0.7*inch, req.phone)
    c.drawString(0.2*inch, 0.5*inch, req.email)
    if req.website:
        c.drawString(0.2*inch, 0.3*inch, req.website)
        
    c.showPage()
    c.save()
    buffer.seek(0)
    filename = f"business_card_{int(time.time())}_{current_user.id}.pdf"
    filepath = os.path.join("uploads", filename)
    with open(filepath, "wb") as f:
        f.write(buffer.getvalue())
    return {"pdf_url": f"/uploads/{filename}"}

# 6. Master Product Catalog & Retailer Inventory
@router.post("/product", response_model=ProductResponse)
def create_product(req: ProductCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not req.barcode:
        req.barcode = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
    try:
        product = crud_business.create_product(
            db, 
            req.dict(), 
            user_id=current_user.id, 
            owner_type=current_user.business_type or "Retailer"
        )
        # Automatically add the created product to the user's inventory
        inv_data = {
            "barcode": product.barcode,
            "available_stock": req.initial_stock or 0,
            "reminder_stock": req.reminder_stock or 0,
            "purchase_price": 0.0,
            "selling_price": product.mrp if product.mrp else 0.0
        }
        crud_business.add_to_inventory(db, inv_data, current_user.id)
        
        return product
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/product/lookup/{barcode}", response_model=ProductResponse)
def lookup_product(barcode: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    product = crud_business.lookup_product(db, barcode, current_user.id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or not accessible")
    return product

@router.post("/inventory", response_model=InventoryResponse)
def add_to_inventory(req: InventoryAdd, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        inv = crud_business.add_to_inventory(db, req.dict(), current_user.id)
        return inv
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/inventory")
def get_inventory(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = crud_business.get_inventory(db, user_id=current_user.id)
    # Serialize manually or rely on Pydantic list
    res = []
    for i in items:
        prod = i.product
        if not prod:
            continue
        res.append({
            "id": i.id,
            "product_id": i.product_id,
            "name": prod.name,
            "barcode": prod.barcode,
            "current_stock": i.available_stock,
            "purchase_price": i.purchase_price,
            "selling_price": i.selling_price,
            "gst_rate": prod.gst_rate,
            "mrp": prod.mrp,
            "owner_type": prod.owner_type,
            "product_type": prod.product_type or 'Finished Good',
            "reminder_stock": i.reminder_stock,
            "brand": prod.brand,
            "category": prod.category,
            "description": prod.description,
            "hsn_code": prod.hsn_code,
            "image_url": getattr(prod, 'image_url', None),
            "batch_number": getattr(i, 'batch_number', None),
            "expiry_date": i.expiry_date.isoformat() if getattr(i, 'expiry_date', None) else None
        })
    return {"items": res}

@router.get("/inventory/scan/{barcode}")
def scan_inventory(barcode: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from models.business import RetailerInventory, Product
    # 1. Check local private inventory
    local_inv = db.query(RetailerInventory).join(Product).filter(
        RetailerInventory.retailer_id == current_user.id,
        Product.barcode == barcode
    ).first()
    
    if local_inv:
        return {
            "source": "local",
            "item": {
                "id": local_inv.id,
                "product_id": local_inv.product_id,
                "name": local_inv.product.name,
                "barcode": local_inv.product.barcode,
                "current_stock": local_inv.available_stock,
                "reminder_stock": local_inv.reminder_stock,
                "purchase_price": local_inv.purchase_price,
                "selling_price": local_inv.selling_price,
                "gst_rate": local_inv.product.gst_rate,
                "mrp": local_inv.product.mrp,
                "brand": local_inv.product.brand,
                "category": local_inv.product.category,
                "owner_type": local_inv.product.owner_type
            }
        }
        
    # 2. Check global product catalog
    global_product = db.query(Product).filter(
        Product.barcode == barcode,
        Product.visibility == "Global"
    ).first()
    
    if global_product:
        return {
            "source": "global",
            "product": {
                "id": global_product.id,
                "name": global_product.name,
                "barcode": global_product.barcode,
                "brand": global_product.brand,
                "category": global_product.category,
                "gst_rate": global_product.gst_rate,
                "mrp": global_product.mrp,
                "image_url": global_product.image_url
            }
        }
        
    raise HTTPException(status_code=404, detail="Product not found")

@router.get("/inventory/barcodes")
def get_inventory_barcodes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_reportlab()
    items = crud_business.get_inventory(db, user_id=current_user.id)
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Inventory Barcodes")
    
    x_start = 50
    y_start = height - 120
    x_offset = 250
    y_offset = 100
    
    col = 0
    row = 0
    
    for item in items:
        barcode_value = item.product.barcode if item.product.barcode else f"ITEM-{item.product.id}"
        
        x = x_start + (col * x_offset)
        y = y_start - (row * y_offset)
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y + 40, item.product.name[:25])
        
        c.setFont("Helvetica", 8)
        display_price = item.selling_price if item.selling_price > 0 else (item.product.mrp or 0.0)
        c.drawString(x, y + 30, f"Price: Rs.{display_price:.2f} | Stock: {item.available_stock}")
        
        # Draw barcode
        try:
            barcode = code128.Code128(barcode_value, barHeight=30, barWidth=0.8)
            barcode.drawOn(c, x, y - 10)
            c.setFont("Helvetica", 8)
            c.drawString(x + 20, y - 25, barcode_value)
        except Exception as e:
            c.drawString(x, y - 10, f"[Barcode Error]")
        
        col += 1
        if col > 1:
            col = 0
            row += 1
            
        if row > 6:
            c.showPage()
            col = 0
            row = 0
            y_start = height - 100
                
    c.save()
    buffer.seek(0)
    
    filename = f"inventory_barcodes_{int(time.time())}_{current_user.id}.pdf"
    filepath = os.path.join("uploads", filename)
    with open(filepath, "wb") as f:
        f.write(buffer.getvalue())
    return {"pdf_url": f"/uploads/{filename}"}

@router.get("/inventory/barcode/{item_id}")
def get_single_inventory_barcode(item_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_reportlab()
    
    from models.business import RetailerInventory
    item = db.query(RetailerInventory).filter(RetailerInventory.id == item_id, RetailerInventory.retailer_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(3.5*inch, 2*inch)) # Small label size
    
    barcode_value = item.product.barcode if item.product.barcode else f"ITEM-{item.product.id}"
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(0.2*inch, 1.6*inch, item.product.name[:25])
    
    c.setFont("Helvetica", 8)
    display_price = item.selling_price if item.selling_price > 0 else (item.product.mrp or 0.0)
    c.drawString(0.2*inch, 1.4*inch, f"Price: Rs.{display_price:.2f} | Stock: {item.available_stock}")
    
    barcode = code128.Code128(barcode_value, barHeight=40, barWidth=0.8)
    barcode.drawOn(c, 0.2*inch, 0.6*inch)
    
    c.setFont("Helvetica", 8)
    c.drawString(0.2*inch, 0.4*inch, barcode_value)
    
    c.save()
    buffer.seek(0)
    
    filename = f"barcode_{int(time.time())}_{current_user.id}.pdf"
    filepath = os.path.join("uploads", filename)
    with open(filepath, "wb") as f:
        f.write(buffer.getvalue())
    return {"pdf_url": f"/uploads/{filename}"}

@router.get("/inventory/report")
def get_inventory_report(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_reportlab()
    items = crud_business.get_inventory(db, user_id=current_user.id)
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Inventory Report")
    
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    y = height - 120
    
    # Table Header
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Item Name")
    c.drawString(250, y, "SKU")
    c.drawString(380, y, "Stock")
    c.drawString(450, y, "Price")
    c.drawString(520, y, "MRP")
    
    c.line(50, y - 5, 550, y - 5)
    y -= 25
    
    c.setFont("Helvetica", 10)
    
    for item in items:
        name = item.product.name[:25]
        sku = item.product.barcode if item.product.barcode else f"ITEM-{item.product.id}"
        stock = str(item.available_stock)
        display_price = item.selling_price if item.selling_price > 0 else (item.product.mrp or 0.0)
        price = f"{display_price:.2f}"
        mrp = f"{item.product.mrp:.2f}" if item.product.mrp else "-"
        
        c.drawString(50, y, name)
        c.drawString(250, y, sku)
        c.drawString(380, y, stock)
        c.drawString(450, y, price)
        c.drawString(520, y, mrp)
        
        y -= 20
        
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)
            
    c.save()
    buffer.seek(0)
    
    filename = f"inventory_report_{int(time.time())}_{current_user.id}.pdf"
    filepath = os.path.join("uploads", filename)
    with open(filepath, "wb") as f:
        f.write(buffer.getvalue())
    return {"pdf_url": f"/uploads/{filename}"}

# 7. Sales Tracker
@router.post("/sales-tracker")
def sales_tracker(req: SalesTrackerRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    total_revenue = 0
    items_sold = 0
    
    for sale in req.sales:
        rev = sale.quantity_sold * sale.unit_price
        total_revenue += rev
        items_sold += sale.quantity_sold
        
        db_sale = sale.dict()
        db_sale["total_amount"] = rev
        crud_business.create_sale_record(db, db_sale, user_id=current_user.id)
        
        # Decrement inventory stock
        from models.business import RetailerInventory, Product
        inv_query = db.query(RetailerInventory).join(Product).filter(RetailerInventory.retailer_id == current_user.id)
        if sale.sku:
            inv_item = inv_query.filter(Product.barcode == sale.sku).first()
        else:
            inv_item = inv_query.filter(Product.name == sale.item_name).first()
            
        if inv_item:
            inv_item.available_stock -= sale.quantity_sold
            
            # Record Stock Movement
            from models.business import StockMovement
            from datetime import date
            db_movement = StockMovement(
                product_id=inv_item.product_id,
                retailer_id=current_user.id,
                movement_type="SALE",
                quantity_change=-sale.quantity_sold,
                reference_id=f"TRK-{int(total_revenue)}",
                date=date.today()
            )
            db.add(db_movement)
            db.commit()
        
    return {
        "status": "Sales Synced to Database",
        "total_revenue": round(total_revenue, 2),
        "total_items_sold": items_sold,
    }

# 8. Expense Manager
@router.post("/expense-manager")
def expense_manager(req: ExpenseManagerRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    total = 0
    for e in req.expenses:
        total += e.amount
        db_exp = e.dict()
        db_exp["expense_date"] = e.date if hasattr(e, 'date') else None
        crud_business.create_expense(db, db_exp, user_id=current_user.id)
        
    return {
        "status": "Expenses Synced to Database",
        "total_business_expenses_added": round(total, 2)
    }

# 9. Profit Calculator (Stateless Tool)
@router.post("/profit-calculator")
def profit_calculator(req: ProfitCalculatorRequest):
    gross_profit = req.total_revenue - req.cost_of_goods_sold
    gross_margin = (gross_profit / req.total_revenue) * 100 if req.total_revenue > 0 else 0
    
    net_profit = gross_profit - req.operating_expenses - (req.taxes_paid or 0)
    net_margin = (net_profit / req.total_revenue) * 100 if req.total_revenue > 0 else 0
    
    return {
        "gross_profit": round(gross_profit, 2),
        "gross_margin_percentage": round(gross_margin, 2),
        "net_profit": round(net_profit, 2),
        "net_margin_percentage": round(net_margin, 2),
        "status": "Profitable" if net_profit > 0 else "Loss"
    }

@router.get("/sales-tracker/history")
def get_sales_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sales = crud_business.get_sales(db, user_id=current_user.id)
    return [
        {
            "item_name": s.item_name,
            "quantity_sold": s.quantity_sold,
            "unit_price": s.unit_price,
            "total_amount": s.total_amount,
            "sale_date": s.sale_date.isoformat() if s.sale_date else None
        }
        for s in sales
    ]

# 10. Business Analytics (Now Queries DB!)
@router.get("/business-analytics")
def business_analytics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # In a real app, we would query the database by date ranges.
    # For now, we just aggregate all historical data stored in Postgres!
    sales = crud_business.get_sales(db, user_id=current_user.id)
    expenses = crud_business.get_expenses(db, user_id=current_user.id)
    
    total_revenue = sum(s.total_amount for s in sales)
    total_expenses = sum(e.amount for e in expenses)
    net_profit = total_revenue - total_expenses
    
    return {
        "status": "Live Data Aggregated from PostgreSQL",
        "total_historical_revenue": round(total_revenue, 2),
        "total_historical_expenses": round(total_expenses, 2),
        "net_profit_margin": round(net_profit, 2),
        "total_sales_transactions_recorded": len(sales),
        "total_expense_transactions_recorded": len(expenses)
    }

# 11. Purchase & Stock Module
@router.post("/purchase-invoice")
def create_purchase_invoice(req: PurchaseInvoiceRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from models.business import PurchaseInvoice, PurchaseInvoiceItem, StockMovement, RetailerInventory, Product
    
    # 1. Create Purchase Invoice
    db_purchase = PurchaseInvoice(
        user_id=current_user.id,
        supplier_name=req.supplier_name,
        invoice_number=req.invoice_number,
        invoice_date=req.invoice_date,
        total_amount=req.total_amount,
        pdf_url=req.pdf_url
    )
    db.add(db_purchase)
    db.flush() # Get ID
    
    # 2. Process Items
    for item in req.items:
        # Resolve Product ID
        product = db.query(Product).filter(Product.barcode == item.sku).first()
        if not product:
            product = db.query(Product).filter(Product.name == item.description).first()
            
        if not product:
            # Create a new product automatically
            product = Product(
                creator_id=current_user.id,
                owner_type=current_user.business_type or 'Retailer',
                visibility='Private',
                product_type='Raw Material',
                barcode=item.sku if item.sku else f'SKU-{int(time.time())}-{item.description[:3]}',
                name=item.description,
                mrp=item.unit_price
            )
            db.add(product)
            db.flush()
            
        db_item = PurchaseInvoiceItem(
            purchase_id=db_purchase.id,
            product_id=product.id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.quantity * item.unit_price
        )
        db.add(db_item)
        
        # Update Inventory
        inv_item = db.query(RetailerInventory).filter(
            RetailerInventory.retailer_id == current_user.id,
            RetailerInventory.product_id == product.id
        ).first()
        
        if inv_item:
            inv_item.available_stock += item.quantity
        else:
            # Create new inventory record
            inv_item = RetailerInventory(
                retailer_id=current_user.id,
                product_id=product.id,
                available_stock=item.quantity,
                purchase_price=item.unit_price,
                selling_price=item.unit_price * 1.2 # Default 20% markup
            )
            db.add(inv_item)
            
        # Record Stock Movement
        db_movement = StockMovement(
            product_id=product.id,
            retailer_id=current_user.id,
            movement_type="PURCHASE",
            quantity_change=item.quantity,
            reference_id=f"PUR-{req.invoice_number or 'NA'}",
            date=req.invoice_date
        )
        db.add(db_movement)
        
    db.commit()
    return {"status": "success", "message": "Purchase invoice recorded and stock updated."}

@router.get("/stock-movements/{product_id}", response_model=List[StockMovementResponse])
def get_stock_movements(product_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from models.business import StockMovement
    movements = db.query(StockMovement).filter(
        StockMovement.retailer_id == current_user.id,
        StockMovement.product_id == product_id
    ).order_by(StockMovement.date.desc(), StockMovement.id.desc()).all()
    return movements
