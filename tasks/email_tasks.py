from celery import current_task
from celery_app import celery_app
import resend
from config import settings
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def send_bulk_email(self, emails_data):
    """Send bulk emails using Resend"""
    try:
        # Initialize Resend with API key
        resend.api_key = settings.RESEND_API_KEY
        
        total_emails = len(emails_data)
        successful_sends = 0
        
        for idx, email_data in enumerate(emails_data):
            try:
                params = {
                    "from": email_data.get("from", "onboarding@resend.dev"),
                    "to": email_data["to"],
                    "subject": email_data["subject"],
                    "html": email_data.get("html", ""),
                    "text": email_data.get("text", "")
                }
                
                # Send email
                email = resend.Emails.send(params)
                
                logger.info(f"Email sent successfully: {email['id']}")
                successful_sends += 1
                
                # Update task progress
                current_task.update_state(
                    state='PROGRESS',
                    meta={'current': idx + 1, 'total': total_emails, 'status': f'Sent {idx + 1}/{total_emails}'}
                )
                
            except Exception as e:
                logger.error(f"Failed to send email to {email_data.get('to', 'unknown')}: {str(e)}")
                continue
        
        return {
            'status': 'completed',
            'successful_sends': successful_sends,
            'total_emails': total_emails,
            'failed_sends': total_emails - successful_sends
        }
        
    except Exception as e:
        logger.error(f"Bulk email task failed: {str(e)}")
        raise
