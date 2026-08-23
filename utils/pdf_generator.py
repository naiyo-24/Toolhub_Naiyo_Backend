import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from sqlalchemy.orm import Session
from models.loan_case import LoanCase
from models.document import Document
from models.ocr_result import OCRResult
from models.risk_analysis import RiskAnalysis
from utils.graphs import generate_income_pie_chart
from reportlab.platypus import Image

def generate_case_report(case_id: int, db: Session) -> str:
    # 1. Fetch data
    case = db.query(LoanCase).filter(LoanCase.id == case_id).first()
    if not case:
        raise ValueError("Case not found")
        
    customer = case.customer
    documents = db.query(Document).filter(Document.case_id == case_id).all()
    
    # 2. Setup PDF path
    reports_dir = os.path.join("uploads", "reports")
    os.makedirs(reports_dir, exist_ok=True)
    file_name = f"Case_Report_{case.case_number}.pdf"
    file_path = os.path.join(reports_dir, file_name)
    
    # 3. Setup document
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor("#0D47A1"),
        spaceAfter=12,
        alignment=1 # Center
    )
    
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor("#1565C0"),
        spaceBefore=15,
        spaceAfter=10
    )
    
    normal_style = styles['Normal']
    
    # --- HEADER ---
    logo_path = "toolhub_logo.png"
    header_data = []
    
    title_paragraphs = [
        Paragraph("TOOLHUB LOAN DESK", title_style),
        Paragraph("Comprehensive Case Report", ParagraphStyle('Sub', parent=styles['Heading2'], alignment=1))
    ]
    
    if os.path.exists(logo_path):
        logo_img = Image(logo_path, width=2.5*inch, height=1.0*inch)
        # Preserve aspect ratio or just use standard sizing
        header_data.append([logo_img, title_paragraphs])
        header_table = Table(header_data, colWidths=[2.5*inch, 4.5*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ]))
        elements.append(header_table)
    else:
        elements.extend(title_paragraphs)
        
    elements.append(Spacer(1, 0.2*inch))
    
    # --- CASE DETAILS TABLE ---
    elements.append(Paragraph("Case Details", section_title))
    
    case_data = [
        ["Case Number", case.case_number, "Status", case.status],
        ["Loan Type", case.loan_type, "Requested Amount", f"Rs. {case.requested_amount:,.2f}" if case.requested_amount else "N/A"],
        ["Customer Name", customer.full_name if customer else "N/A", "Customer Type", customer.customer_type if customer else "N/A"],
        ["Mobile", customer.mobile if customer else "N/A", "Email", customer.email if customer else "N/A"],
        ["PAN", customer.pan if customer else "N/A", "DOB", str(customer.dob) if customer and customer.dob else "N/A"]
    ]
    
    case_table = Table(case_data, colWidths=[1.2*inch, 2.3*inch, 1.2*inch, 2.3*inch])
    case_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), # Col 1 labels
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'), # Col 3 labels
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#E0E0E0")),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor("#0D47A1")),
    ]))
    
    elements.append(case_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # --- LOAN ANALYSIS DECISION ---
    analysis = db.query(RiskAnalysis).filter(RiskAnalysis.case_id == case_id).first()
    if analysis:
        elements.append(Paragraph("Loan Analysis & Decision", section_title))
        
        # Risk Score and Grade
        score_text = f"<b>Risk Score:</b> {analysis.risk_score} / 100 &nbsp;&nbsp;&nbsp;&nbsp; <b>Risk Grade:</b> {analysis.risk_grade}"
        elements.append(Paragraph(score_text, normal_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # Decision
        decision_color = "#43A047" if analysis.decision == "ELIGIBLE" else ("#FFB300" if analysis.decision == "REVIEW" else "#E53935")
        decision_style = ParagraphStyle('Decision', parent=styles['Normal'], fontSize=14, textColor=colors.HexColor(decision_color), fontName='Helvetica-Bold')
        elements.append(Paragraph(f"RECOMMENDED DECISION: {analysis.decision}", decision_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Loan Metrics
        metrics_data = [
            ["Verified Monthly Income", f"Rs. {float(analysis.verified_monthly_income or 0):,.2f}"],
            ["Proposed EMI", f"Rs. {float(analysis.proposed_emi or 0):,.2f}"],
            ["Existing EMI", f"Rs. {float(analysis.existing_emi or 0):,.2f}"],
            ["FOIR (Debt-to-Income)", f"{float(analysis.foir_percentage or 0):.1f}%"]
        ]
        metrics_table = Table(metrics_data, colWidths=[2.5*inch, 2.5*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(metrics_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Graphical Analysis
        try:
            chart_path = generate_income_pie_chart(
                float(analysis.verified_monthly_income or 0),
                float(analysis.proposed_emi or 0),
                float(analysis.existing_emi or 0)
            )
            elements.append(Image(chart_path, width=3.2*inch, height=2.1*inch))
            elements.append(Spacer(1, 0.1*inch))
        except Exception as e:
            elements.append(Paragraph(f"(Could not generate chart: {str(e)})", normal_style))
            
        # Explanations
        if analysis.analysis_details:
            details = analysis.analysis_details
            
            elements.append(Paragraph("<b>Positive Factors:</b>", normal_style))
            for pf in details.get("positive_factors", []):
                elements.append(Paragraph(f"<font color='green'>&#10004;</font> {pf}", normal_style))
            elements.append(Spacer(1, 0.1*inch))
            
            elements.append(Paragraph("<b>Risk Factors:</b>", normal_style))
            for rf in details.get("risk_factors", []):
                elements.append(Paragraph(f"<font color='red'>&#9888;</font> {rf}", normal_style))
                
            if details.get("recommended_offers"):
                elements.append(Spacer(1, 0.2*inch))
                elements.append(Paragraph("<b>AI Recommended Loan Options:</b>", normal_style))
                elements.append(Spacer(1, 0.1*inch))
                
                offers_data = [["Plan Name", "Tenure", "Rate/Limit", "Max EMI", "Max Loan Amount"]]
                for offer in details.get("recommended_offers", []):
                    offers_data.append([
                        offer.get("plan_name", ""),
                        f"{offer.get('tenure_months', 0)} mos",
                        f"{offer.get('interest_rate', 0)}% / {offer.get('foir', 0)}%",
                        f"Rs. {offer.get('max_emi', 0):,.2f}",
                        f"Rs. {offer.get('max_loan_amount', 0):,.0f}"
                    ])
                    
                offers_table = Table(offers_data, colWidths=[2.2*inch, 0.8*inch, 1.2*inch, 1.2*inch, 1.5*inch])
                offers_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0D47A1")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                ]))
                elements.append(offers_table)
                
        elements.append(Spacer(1, 0.4*inch))
        elements.append(PageBreak())

    # --- OCR EXTRACTED DATA ---
    elements.append(Paragraph("Extracted Document Data", section_title))
    
    has_ocr_data = False
    for document in documents:
        ocr_result = db.query(OCRResult).filter(OCRResult.document_id == document.id).first()
        if not ocr_result or not ocr_result.structured_data:
            continue
            
        has_ocr_data = True
        elements.append(Paragraph(f"Document: {document.document_type} - {document.file_name}", styles['Heading3']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Build table for OCR data
        ocr_data_list = []
        for key, value in ocr_result.structured_data.items():
            # Convert values to strings and handle long text
            val_str = str(value)
            if len(val_str) > 80:
                val_str = val_str[:77] + "..."
            ocr_data_list.append([key, val_str])
            
        if not ocr_data_list:
            elements.append(Paragraph("No structured data found.", normal_style))
            continue
            
        ocr_table = Table(ocr_data_list, colWidths=[2.5*inch, 4.5*inch])
        ocr_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#F5F5F5")),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
        ]))
        
        elements.append(ocr_table)
        elements.append(Spacer(1, 0.2*inch))
        
    if not has_ocr_data:
        elements.append(Paragraph("No extracted OCR data found for this case.", normal_style))
        
    # Generate PDF
    doc.build(elements)
    
    return file_path
