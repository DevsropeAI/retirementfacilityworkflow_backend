from twilio.rest import Client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def send_sms(to_phone: str, message: str):
    """
    Send SMS via Twilio
    Returns: (success: bool, message: str)
    """
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # Remove any non-digit characters from phone number
        to_phone = ''.join(filter(str.isdigit, to_phone))
        if not to_phone.startswith('+'):
            to_phone = '+' + to_phone
        
        message = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        
        logger.info(f"✅ SMS sent to {to_phone} | SID: {message.sid}")
        return True, f"SMS sent successfully (SID: {message.sid})"

    except Exception as e:
        logger.error(f"❌ SMS failed: {str(e)}")
        return False, str(e)