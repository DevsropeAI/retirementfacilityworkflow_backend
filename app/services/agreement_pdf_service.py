import os
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
import base64
from io import BytesIO
from PIL import Image

def generate_agreement_pdf(agreement):
    """Generate a PDF of the signed agreement"""
    
    # Create directory if not exists
    pdf_dir = Path("uploads/agreements")
    pdf_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    filename = f"agreement_{agreement.agreement_number}.pdf"
    file_path = pdf_dir / filename
    
    # Get lead
    lead = agreement.lead
    
    # Create PDF
    doc = SimpleDocTemplate(str(file_path), pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Title'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=10
    )
    
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8
    )
    
    story = []
    
    # Title
    story.append(Paragraph("RETIREES PARADISE", title_style))
    story.append(Paragraph("RESIDENCY AGREEMENT", title_style))
    story.append(Spacer(1, 20))
    
    # Agreement Number
    story.append(Paragraph(f"Agreement Number: {agreement.agreement_number}", normal_style))
    story.append(Spacer(1, 10))
    
    # Date
    story.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", normal_style))
    story.append(Spacer(1, 20))
    
    # Parties
    story.append(Paragraph("PARTIES", heading_style))
    story.append(Paragraph(f"This agreement is made between:", normal_style))
    story.append(Paragraph(f"Retirees Paradise (the 'Facility')", normal_style))
    story.append(Paragraph(f"and {lead.name} (the 'Resident')", normal_style))
    story.append(Spacer(1, 20))
    
    # Resident Details
    story.append(Paragraph("RESIDENT DETAILS", heading_style))
    story.append(Paragraph(f"Name: {lead.name}", normal_style))
    story.append(Paragraph(f"Email: {lead.email}", normal_style))
    story.append(Paragraph(f"Phone: {lead.phone}", normal_style))
    story.append(Spacer(1, 20))
    
    # Agreement Details
    story.append(Paragraph("AGREEMENT DETAILS", heading_style))
    story.append(Paragraph(f"Facility: {agreement.facility}", normal_style))
    if agreement.room_number:
        story.append(Paragraph(f"Room Number: {agreement.room_number}", normal_style))
    story.append(Paragraph(f"Move-in Date: {agreement.move_in_date.strftime('%B %d, %Y')}", normal_style))
    story.append(Paragraph(f"Monthly Fee: ${agreement.monthly_fee:,.2f}", normal_style))
    if agreement.security_deposit:
        story.append(Paragraph(f"Security Deposit: ${agreement.security_deposit:,.2f}", normal_style))
    story.append(Spacer(1, 20))
    
    # Terms and Conditions
    story.append(Paragraph("TERMS AND CONDITIONS", heading_style))
    terms = agreement.terms_conditions or "Standard terms and conditions apply."
    story.append(Paragraph(terms.replace('\n', '<br/>'), normal_style))
    story.append(Spacer(1, 20))
    
    # Signature Section
    story.append(Paragraph("SIGNATURES", heading_style))
    story.append(Paragraph("By signing below, the Resident agrees to the terms and conditions of this agreement.", normal_style))
    story.append(Spacer(1, 20))
    
    # Signature image
    if agreement.signature_image:
        try:
            # Decode base64 image
            image_data = base64.b64decode(agreement.signature_image.split(',')[1] if ',' in agreement.signature_image else agreement.signature_image)
            img = Image.open(BytesIO(image_data))
            
            # Resize to fit
            img_width, img_height = img.size
            max_width = 300
            if img_width > max_width:
                ratio = max_width / img_width
                img_width = max_width
                img_height = int(img_height * ratio)
            
            # Save temp image
            temp_img_path = pdf_dir / "temp_signature.png"
            img.save(temp_img_path)
            
            # Add to PDF
            from reportlab.platypus import Image
            story.append(Image(str(temp_img_path), width=img_width, height=img_height))
            
            # Clean up
            os.remove(temp_img_path)
            
        except Exception as e:
            story.append(Paragraph("Signature image not available", normal_style))
        
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"Signed Date: {agreement.signed_at.strftime('%B %d, %Y at %I:%M %p') if agreement.signed_at else 'N/A'}", normal_style))
    
    story.append(Spacer(1, 20))
    story.append(Paragraph("Retirees Paradise Representative", normal_style))
    story.append(Paragraph("___________________________", normal_style))
    story.append(Paragraph("Authorized Signature", normal_style))
    
    # Build PDF
    doc.build(story)
    
    return str(file_path)