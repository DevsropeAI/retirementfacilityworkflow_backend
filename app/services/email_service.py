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

        logger.info(f"✅ Email sent to {to_email}")
        return True, "Email sent successfully"

    except Exception as e:
        logger.error(f"❌ Email failed: {str(e)}")
        return False, str(e)