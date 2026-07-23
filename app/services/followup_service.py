from app.services.email_service import send_email
from app.services.sms_service import send_sms
import logging

logger = logging.getLogger(__name__)

# ============ TEMPLATE FUNCTIONS ============

def get_welcome_templates(name: str):
    return {
        "subject": "Welcome to Retirees Paradise!",
        "body": f"""
Dear {name},

Thank you for your interest in Retirees Paradise! We're excited to help you find your perfect retirement destination.

Our team is reviewing your information and will be in touch shortly. In the meantime, feel free to explore our resources:

- Browse our facilities: https://retireesparadise.com/facilities
- Learn about destinations: https://retireesparadise.com/destinations

If you have any immediate questions, reply to this email or call us at +1-800-555-0123.

Best regards,
The Retirees Paradise Team
""",
        "html": f"""
<h2>Welcome to Retirees Paradise!</h2>
<p>Dear {name},</p>
<p>Thank you for your interest in Retirees Paradise! We're excited to help you find your perfect retirement destination.</p>
<p>Our team is reviewing your information and will be in touch shortly. In the meantime, feel free to explore our resources:</p>
<ul>
  <li><a href="https://retireesparadise.com/facilities">Browse our facilities</a></li>
  <li><a href="https://retireesparadise.com/destinations">Learn about destinations</a></li>
</ul>
<p>If you have any immediate questions, reply to this email or call us at +1-800-555-0123.</p>
<p>Best regards,<br>The Retirees Paradise Team</p>
"""
    }

def get_score_templates(name: str, score: str):
    if score == "Hot":
        return {
            "subject": "🔥 Your Dream Retirement Awaits — Let's Talk!",
            "body": f"""
Dear {name},

Great news! Based on your profile, you're a perfect match for our premium retirement communities.

Our team has pre-qualified you for:
✅ Exclusive facility tours
✅ Personalized consultation with our retirement experts
✅ Special early-bird pricing

Ready to take the next step? Book your consultation now:
https://retireesparadise.com/book-consultation

We're excited to help you start this new chapter!

Best regards,
The Retirees Paradise Team
""",
            "sms": f"🔥 Hi {name}, you're pre-qualified for premium retirement! Book your consultation: https://retireesparadise.com/book"
        }
    elif score == "Warm":
        return {
            "subject": "📋 Explore Retirement Options with Retirees Paradise",
            "body": f"""
Dear {name},

You're on the right track! Based on your profile, we have some excellent retirement options that might interest you.

Here's what we recommend:
📖 Download our free Retirement Guide
🏡 Explore our facility tours
📞 Schedule a call with our team

Get started here: https://retireesparadise.com/explore

We look forward to helping you find your perfect home!

Best regards,
The Retirees Paradise Team
""",
            "sms": f"📋 Hi {name}, check out our retirement guide and facilities: https://retireesparadise.com/explore"
        }
    else:  # Cold
        return {
            "subject": "📚 Retirement Planning — A Free Guide",
            "body": f"""
Dear {name},

Thinking about retirement? We're here to help! We've created a comprehensive guide to help you understand your options.

📖 Download your free copy: https://retireesparadise.com/guide

This guide covers:
• Top retirement destinations
• Cost of living comparisons
• Healthcare access
• Visa requirements

No obligation — just helpful information to support your journey.

Best regards,
The Retirees Paradise Team
""",
            "sms": f"📚 Hi {name}, download our free retirement guide: https://retireesparadise.com/guide"
        }

# ============ HELPER: Convert SQLAlchemy to Dict ============

def _to_dict(lead):
    """Convert SQLAlchemy lead to dictionary if needed"""
    if hasattr(lead, '__dict__') and not isinstance(lead, dict):
        return {
            "id": lead.id,
            "name": lead.name,
            "email": lead.email,
            "phone": lead.phone,
            "age": lead.age,
            "current_location": lead.current_location,
            "retirement_status": lead.retirement_status,
            "monthly_income": lead.monthly_income,
            "desired_move_date": lead.desired_move_date,
            "desired_country": lead.desired_country,
            "budget": lead.budget,
            "timeline": lead.timeline,
            "medical_requirements": lead.medical_requirements,
            "family_info": lead.family_info,
            "lead_source": lead.lead_source,
            "status": lead.status,
            "qualification_score": lead.qualification_score,
            "qualification_reasoning": lead.qualification_reasoning,
        }
    return lead

# ============ SEND FUNCTIONS ============

def send_welcome(lead, db=None):
    """Send welcome email to new lead"""
    lead = _to_dict(lead)
    name = lead.get("name", "there")
    email = lead.get("email")
    
    if not email:
        logger.warning("❌ No email address provided")
        return False, "No email address"
    
    templates = get_welcome_templates(name)
    success, msg = send_email(email, templates["subject"], templates["body"], templates["html"])
    
    if success and db:
        add_communication_entry(lead, "email", f"Welcome email sent to {email}", db)
    
    return success, msg

def send_score_followup(lead, db=None):
    """Send score-specific follow-up email + SMS"""
    lead = _to_dict(lead)
    name = lead.get("name", "there")
    email = lead.get("email")
    phone = lead.get("phone")
    score = lead.get("qualification_score", "Cold")
    
    if not email:
        logger.warning("❌ No email address provided")
        return False, "No email address"
    
    templates = get_score_templates(name, score)
    
    # Send email
    success, msg = send_email(email, templates["subject"], templates["body"])
    
    if success and db:
        add_communication_entry(lead, "email", f"{score} follow-up email sent to {email}", db)
    
    # Send SMS (only if Hot or Warm)
    if score in ["Hot", "Warm"] and phone and templates.get("sms"):
        sms_success, sms_msg = send_sms(phone, templates["sms"])
        if sms_success and db:
            add_communication_entry(lead, "sms", f"{score} SMS sent to {phone}", db)
    
    return success, msg

def add_communication_entry(lead, comm_type, message, db):
    """Add entry to communication history"""
    from datetime import datetime
    
    if not lead.get("communication_history"):
        lead["communication_history"] = []
    
    entry = {
        "date": datetime.now().isoformat(),
        "type": comm_type,
        "message": message,
        "by": "system"
    }
    lead["communication_history"].append(entry)
    
    # If we have a DB session, update the actual lead
    if db and lead.get("id"):
        from app.models.db_models import Lead
        db_lead = db.query(Lead).filter(Lead.id == lead["id"]).first()
        if db_lead:
            db_lead.communication_history = lead["communication_history"]
            db.commit()