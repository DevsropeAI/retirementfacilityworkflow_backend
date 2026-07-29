import os
from pathlib import Path
from datetime import datetime
from io import BytesIO
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage

def generate_agreement_pdf(agreement):
    """Generate a PDF of the signed agreement with signature image"""
    
    # Create directory if not exists
    pdf_dir = Path("uploads/agreements")
    pdf_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    filename = f"agreement_{agreement.agreement_number}.pdf"
    file_path = pdf_dir / filename
    
    # Get lead
    lead = agreement.lead
    
    # Create PDF canvas
    c = canvas.Canvas(str(file_path), pagesize=letter)
    width, height = letter
    y = height - 50
    
    # Title
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width/2, y, "RETIREES PARADISE")
    y -= 30
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, y, "RESIDENCY AGREEMENT")
    y -= 30
    
    # Agreement Number
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Agreement Number: {agreement.agreement_number}")
    y -= 20
    c.drawString(50, y, f"Date: {datetime.now().strftime('%B %d, %Y')}")
    y -= 30
    
    # Parties
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "PARTIES")
    y -= 20
    c.setFont("Helvetica", 11)
    c.drawString(50, y, "This agreement is made between:")
    y -= 16
    c.drawString(50, y, f"Retirees Paradise (the 'Facility')")
    y -= 16
    c.drawString(50, y, f"and {lead.name} (the 'Resident')")
    y -= 25
    
    # Resident Details
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "RESIDENT DETAILS")
    y -= 20
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Name: {lead.name}")
    y -= 16
    c.drawString(50, y, f"Email: {lead.email}")
    y -= 16
    c.drawString(50, y, f"Phone: {lead.phone}")
    y -= 25
    
    # Agreement Details
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "AGREEMENT DETAILS")
    y -= 20
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Facility: {agreement.facility}")
    y -= 16
    if agreement.room_number:
        c.drawString(50, y, f"Room Number: {agreement.room_number}")
        y -= 16
    c.drawString(50, y, f"Move-in Date: {agreement.move_in_date.strftime('%B %d, %Y')}")
    y -= 16
    c.drawString(50, y, f"Monthly Fee: ${agreement.monthly_fee:,.2f}")
    y -= 16
    if agreement.security_deposit:
        c.drawString(50, y, f"Security Deposit: ${agreement.security_deposit:,.2f}")
        y -= 16
    y -= 10
    
    # Terms and Conditions
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "TERMS AND CONDITIONS")
    y -= 20
    c.setFont("Helvetica", 11)
    terms = agreement.terms_conditions or "Standard terms and conditions apply."
    lines = terms.split('\n')
    for line in lines:
        if y < 100:
            c.showPage()
            y = height - 50
        c.drawString(50, y, line[:80])
        y -= 16
    
    # Signature Section
    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "SIGNATURES")
    y -= 20
    c.setFont("Helvetica", 11)
    c.drawString(50, y, "By signing below, the Resident agrees to the terms and conditions of this agreement.")
    y -= 25
    
    # Add signature image
    if agreement.signature_image:
        try:
            print("🖼️ Processing signature image...")
            
            image_data = agreement.signature_image
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            img = PILImage.open(BytesIO(image_bytes))
            print(f"✅ Image opened: {img.size}")
            
            max_width = 300
            max_height = 100
            img_width, img_height = img.size
            
            if img_width > max_width:
                ratio = max_width / img_width
                img_width = max_width
                img_height = int(img_height * ratio)
            
            if img_height > max_height:
                ratio = max_height / img_height
                img_height = max_height
                img_width = int(img_width * ratio)
            
            print(f"📐 Resized to: {img_width}x{img_height}")
            
            img_bytes_io = BytesIO()
            img.save(img_bytes_io, format='PNG')
            img_bytes_io.seek(0)
            
            img_reader = ImageReader(img_bytes_io)
            c.drawImage(img_reader, 50, y - img_height - 10, width=img_width, height=img_height)
            print("✅ Signature added to PDF")
            y -= img_height + 20
            
        except Exception as e:
            print(f"❌ Signature image failed: {e}")
            import traceback
            traceback.print_exc()
            c.drawString(50, y, "[Signature image not available]")
            y -= 20
    else:
        c.drawString(50, y, "[No signature provided]")
        y -= 20
    
    y -= 10
    c.drawString(50, y, f"Signed Date: {agreement.signed_at.strftime('%B %d, %Y at %I:%M %p') if agreement.signed_at else 'N/A'}")
    y -= 25
    
    c.setFont("Helvetica", 11)
    c.drawString(50, y, "Retirees Paradise Representative")
    y -= 16
    c.drawString(50, y, "___________________________")
    y -= 16
    c.drawString(50, y, "Authorized Signature")
    
    c.save()
    
    print(f"✅ PDF generated: {file_path}")
    return str(file_path)