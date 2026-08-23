from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import io
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.loan_case import LoanCase
from models.report import Report
from models.document import Document
from models.ocr_result import OCRResult
from schemas.report import ReportCreate, ReportResponse
from routes.auth import get_current_user
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

router = APIRouter()

@router.get("/case/{case_id}/summary-pdf")
def generate_case_summary_pdf(case_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loan_case = db.query(LoanCase).filter(LoanCase.id == case_id, LoanCase.banker_id == current_user.id).first()
    if not loan_case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    documents = db.query(Document).filter(Document.case_id == case_id).all()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1 # Center
    h2_style = styles['Heading2']
    
    elements = []
    
    # Title
    elements.append(Paragraph(f"Credit Assessment Memo (CAM)", title_style))
    elements.append(Spacer(1, 20))
    
    # Case Details
    elements.append(Paragraph("Case Overview", h2_style))
    case_data = [
        ["Applicant Name", loan_case.customer_name or "N/A"],
        ["Loan Amount", f"Rs. {loan_case.requested_amount:,.2f}" if loan_case.requested_amount else "N/A"],
        ["Product Type", loan_case.loan_type or "N/A"],
        ["Status", loan_case.status or "N/A"],
        ["Created At", str(loan_case.created_at)[:10] if loan_case.created_at else "N/A"]
    ]
    t = Table(case_data, colWidths=[150, 350])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Document Extracted Data
    for d in documents:
        ocr = db.query(OCRResult).filter(OCRResult.document_id == d.id).first()
        if ocr and ocr.structured_data:
            elements.append(Paragraph(f"Extracted Data: {d.document_type or 'Document'}", h2_style))
            doc_data = []
            for k, v in ocr.structured_data.items():
                # Ensure long strings wrap properly by keeping column sizes fixed
                doc_data.append([str(k).replace('_', ' ').upper(), str(v)])
            
            if doc_data:
                dt = Table(doc_data, colWidths=[200, 300])
                dt.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f4f6f8")),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
                ]))
                elements.append(dt)
                elements.append(Spacer(1, 20))
                
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer, 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"inline; filename=CAM_Report_{loan_case.id}.pdf"}
    )


@router.get("/case/{case_id}", response_model=list[ReportResponse])
def get_case_reports(case_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loan_case = db.query(LoanCase).filter(LoanCase.id == case_id, LoanCase.banker_id == current_user.id).first()
    if not loan_case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    reports = db.query(Report).filter(Report.case_id == case_id).all()
    return reports

@router.post("", response_model=ReportResponse)
def create_report(report_data: ReportCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loan_case = db.query(LoanCase).filter(LoanCase.id == report_data.case_id, LoanCase.banker_id == current_user.id).first()
    if not loan_case:
        raise HTTPException(status_code=404, detail="Case not found")

    # In a real app, this might trigger a background task to generate a PDF.
    report = Report(
        case_id=report_data.case_id,
        report_type=report_data.report_type,
        status=report_data.status,
        generated_by=current_user.id
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
