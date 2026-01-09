import resend
from config import settings
import logging
from typing import List, Dict, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class EmailData(BaseModel):
    to: List[str] | str
    subject: str
    html: Optional[str] = None
    text: Optional[str] = None
    from_email: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    reply_to: Optional[str] = None

class ResendClient:
    def __init__(self):
        if settings.RESEND_API_KEY:
            resend.api_key = settings.RESEND_API_KEY
        else:
            logger.warning("RESEND_API_KEY not configured")
    
    async def send_email(self, email_data: EmailData) -> Dict:
        """Send a single email using Resend"""
        if not settings.RESEND_API_KEY:
            raise ValueError("RESEND_API_KEY not configured")
        
        try:
            params = {
                "from": email_data.from_email or "onboarding@resend.dev",
                "to": email_data.to,
                "subject": email_data.subject,
            }
            
            if email_data.html:
                params["html"] = email_data.html
            if email_data.text:
                params["text"] = email_data.text
            if email_data.cc:
                params["cc"] = email_data.cc
            if email_data.bcc:
                params["bcc"] = email_data.bcc
            if email_data.reply_to:
                params["reply_to"] = email_data.reply_to
            
            email = resend.Emails.send(params)
            logger.info(f"Email sent successfully: {email['id']}")
            
            return {
                "success": True,
                "email_id": email["id"],
                "status": "sent"
            }
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status": "failed"
            }
    
    async def send_bulk_emails(self, emails_data: List[EmailData]) -> Dict:
        """Send multiple emails using Resend"""
        if not settings.RESEND_API_KEY:
            raise ValueError("RESEND_API_KEY not configured")
        
        results = []
        successful_sends = 0
        failed_sends = 0
        
        for email_data in emails_data:
            result = await self.send_email(email_data)
            results.append(result)
            
            if result["success"]:
                successful_sends += 1
            else:
                failed_sends += 1
        
        return {
            "total_emails": len(emails_data),
            "successful_sends": successful_sends,
            "failed_sends": failed_sends,
            "results": results
        }

# Global Resend client instance
resend_client = ResendClient()
