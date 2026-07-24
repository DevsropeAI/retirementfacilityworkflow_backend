from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.cron import CronTrigger
from app.core.database import engine
from app.routers.consultations import send_due_reminders
from app.core.database import SessionLocal
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Job store using SQLAlchemy (stores jobs in MySQL)
jobstores = {
    'default': SQLAlchemyJobStore(engine=engine)
}

# Thread pool for executing jobs
executors = {
    'default': ThreadPoolExecutor(10)
}

# Scheduler configuration
job_defaults = {
    'coalesce': True,  # Don't run multiple instances of the same job
    'max_instances': 1,  # Only one instance of a job at a time
    'misfire_grace_time': 300  # 5 minutes grace time for missed jobs
}

# Create scheduler
scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone=settings.SCHEDULER_TIMEZONE 
)

def send_daily_reminders():
    """Job function: Send reminders for consultations today"""
    try:
        db = SessionLocal()
        count = send_due_reminders(db)
        db.close()
        logger.info(f"✅ Daily reminders sent: {count} notifications/emails")
    except Exception as e:
        logger.error(f"❌ Daily reminders failed: {e}")

def start_scheduler():
    """Start the scheduler and add the daily job"""
    try:
        # Remove existing job if it exists
        try:
            scheduler.remove_job('daily_reminder_job')
        except:
            pass
        
        # ✅ Add the job with proper args
        scheduler.add_job(
            send_daily_reminders,
            trigger=CronTrigger(hour=9, minute=0),
            id='daily_reminder_job',
            replace_existing=True,
            args=[]  # ← No args needed — it creates its own db session
        )
        
        scheduler.start()
        print("✅ Scheduler started successfully")
        print("📅 Daily reminder job scheduled for 9:00 AM UTC")
        
    except Exception as e:
        print(f"❌ Failed to start scheduler: {e}")

def shutdown_scheduler():
    """Shutdown the scheduler gracefully"""
    try:
        scheduler.shutdown()
        logger.info("✅ Scheduler shutdown successfully")
    except Exception as e:
        logger.error(f"❌ Scheduler shutdown failed: {e}")