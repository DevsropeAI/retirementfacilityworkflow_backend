import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def send_email(to_email: str, subject: str, body: str, html_body: str = None):
    """
    Send email via Gmail SMTP
    Returns: (success: bool, message: str)
    """
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_USER
        msg["To"] = to_email

        # Plain text version
        part1 = MIMEText(body, "plain")
        msg.attach(part1)

        # HTML version (if provided)
        if html_body:
            part2 = MIMEText(html_body, "html")
            msg.attach(part2)

        # Send email
        context = ssl.create_default_context()
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, to_email, msg.as_string())

        logger.info(f" Email sent to {to_email}")
        return True, "Email sent successfully"

    except Exception as e:
        logger.error(f" Email failed: {str(e)}")
        return False, str(e)


def send_application_link(email: str, lead_name: str, link: str):
    """Send application link to lead"""
    subject = "Complete Your Application — Retirees Paradise"
    
    body = f"""
Dear {lead_name},

You have been invited to complete your application for residency with Retirees Paradise.

Click the link below to access your application:
{link}

If you have any questions, please contact our team.

Best regards,
The Retirees Paradise Team
"""
    
    html_body = f"""
<h2>Complete Your Application</h2>
<p>Dear {lead_name},</p>
<p>You have been invited to complete your application for residency with Retirees Paradise.</p>
<p><a href="{link}" style="display: inline-block; background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600;">Complete Application</a></p>
<p>If you have any questions, please contact our team.</p>
<p>Best regards,<br>The Retirees Paradise Team</p>
"""
    
    return send_email(email, subject, body, html_body)    