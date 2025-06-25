import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
import os
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import BackgroundTasks

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@edrp.com')
        self.template_dir = Path(__file__).parent.parent / 'templates' / 'emails'
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))

    async def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        background_tasks: Optional[BackgroundTasks] = None
    ) -> bool:
        """Send an email using a template"""
        try:
            # Render email template
            template = self.env.get_template(f"{template_name}.html")
            html_content = template.render(**context)
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(html_content, 'html'))
            
            if background_tasks:
                # Schedule email sending in background
                background_tasks.add_task(self._send_sync, msg)
                return True
            else:
                # Send immediately
                return await self._send_async(msg)
                
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def _send_sync(self, msg: MIMEMultipart) -> bool:
        """Synchronous email sending for background tasks"""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Error in background email sending: {e}")
            return False
    
    async def _send_async(self, msg: MIMEMultipart) -> bool:
        """Asynchronous email sending"""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

# Email templates for subscription events
class SubscriptionEmails:
    @staticmethod
    async def trial_started(
        email_service: EmailService,
        to_email: str,
        school_name: str,
        trial_days: int,
        background_tasks: BackgroundTasks
    ) -> bool:
        """Send trial started email"""
        subject = f"🎉 Your {trial_days}-Day Trial of EDRP Has Started!"
        return await email_service.send_email(
            to_email=to_email,
            subject=subject,
            template_name="trial_started",
            context={
                "school_name": school_name,
                "trial_days": trial_days,
                "support_email": "support@edrp.com"
            },
            background_tasks=background_tasks
        )
    
    @staticmethod
    async def trial_ending_soon(
        email_service: EmailService,
        to_email: str,
        school_name: str,
        days_left: int,
        background_tasks: BackgroundTasks
    ) -> bool:
        """Send trial ending soon reminder"""
        subject = f"⏳ Your EDRP Trial Ends in {days_left} Day{'s' if days_left > 1 else ''}"
        return await email_service.send_email(
            to_email=to_email,
            subject=subject,
            template_name="trial_ending_soon",
            context={
                "school_name": school_name,
                "days_left": days_left
            },
            background_tasks=background_tasks
        )
    
    @staticmethod
    async def subscription_confirmation(
        email_service: EmailService,
        to_email: str,
        school_name: str,
        plan_name: str,
        amount: float,
        billing_cycle: str,
        next_billing_date: str,
        background_tasks: BackgroundTasks
    ) -> bool:
        """Send subscription confirmation email"""
        subject = f"✅ Your {plan_name} Subscription is Active!"
        return await email_service.send_email(
            to_email=to_email,
            subject=subject,
            template_name="subscription_confirmation",
            context={
                "school_name": school_name,
                "plan_name": plan_name,
                "amount": amount,
                "billing_cycle": billing_cycle,
                "next_billing_date": next_billing_date
            },
            background_tasks=background_tasks
        )
    
    @staticmethod
    async def payment_failed(
        email_service: EmailService,
        to_email: str,
        school_name: str,
        plan_name: str,
        retry_date: str,
        background_tasks: BackgroundTasks
    ) -> bool:
        """Send payment failed notification"""
        subject = "⚠️ Payment Failed - Update Your Payment Method"
        return await email_service.send_email(
            to_email=to_email,
            subject=subject,
            template_name="payment_failed",
            context={
                "school_name": school_name,
                "plan_name": plan_name,
                "retry_date": retry_date
            },
            background_tasks=background_tasks
        )
