import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from jinja2 import Environment, BaseLoader, TemplateError
from typing import Dict, Any, List, Optional, Union
from fastapi import BackgroundTasks, HTTPException, status
from pathlib import Path
import os
from datetime import datetime
import uuid

from database import get_db
from models.email_template import EmailTemplate, SentEmail
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self, db: Session = None):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@edrp.com')
        self.reply_to = os.getenv('REPLY_TO_EMAIL', 'support@edrp.com')
        self.db = db or next(get_db())
        
        # Initialize Jinja2 environment
        self.env = Environment(loader=BaseLoader())
    
    # Template Management
    async def get_template(self, template_id: str) -> EmailTemplate:
        """Get template by ID"""
        template = self.db.query(EmailTemplate).filter(
            (EmailTemplate.id == template_id) & 
            (EmailTemplate.is_active == True)
        ).first()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with ID {template_id} not found"
            )
        return template
    
    async def render_template(
        self, 
        template_id: str, 
        variables: Dict[str, Any] = None,
        locale: str = "en" # New: locale parameter
    ) -> Dict[str, str]:
        """Render template with variables"""
        template = await self.get_template(template_id)
        
        try:
            # Get subject and body based on locale, fallback to default
            rendered_subject = template.subject_translations.get(locale, template.subject)
            rendered_body = template.body_translations.get(locale, template.body)

            subject_template = self.env.from_string(rendered_subject)
            body_template = self.env.from_string(rendered_body)
            
            # Add default variables
            context = {
                'current_date': datetime.now().strftime('%B %d, %Y'),
                'current_year': datetime.now().year,
                'support_email': 'support@edrp.com',
                'support_phone': '+234 800 000 0000',
                **(variables or {})
            }
            
            return {
                'subject': subject_template.render(**context),
                'body': body_template.render(**context)
            }
            
        except TemplateError as e:
            logger.error(f"Template rendering error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template rendering error: {str(e)}"
            )
    
    # Email Sending
    async def send_email(
        self,
        to_emails: Union[str, List[str]],
        subject: str,
        body: str,
        template_id: str = None,
        cc: List[str] = None,
        bcc: List[str] = None,
        reply_to: str = None,
        attachments: List[Dict[str, Any]] = None,
        background_tasks: BackgroundTasks = None
    ) -> Dict[str, Any]:
        """Send an email with optional attachments"""
        if isinstance(to_emails, str):
            to_emails = [to_emails]
            
        if not to_emails:
            raise ValueError("At least one recipient email is required")
            
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)
            if reply_to:
                msg['Reply-To'] = reply_to
            elif self.reply_to:
                msg['Reply-To'] = self.reply_to
                
            # Attach HTML body
            msg.attach(MIMEText(body, 'html'))
            
            # Add attachments if any
            if attachments:
                for attachment in attachments:
                    file_data = attachment.get('data')
                    filename = attachment.get('filename', 'attachment.bin')
                    content_type = attachment.get('content_type', 'application/octet-stream')
                    
                    part = MIMEApplication(file_data, Name=filename)
                    part['Content-Disposition'] = f'attachment; filename="{filename}"'
                    part['Content-Type'] = content_type
                    msg.attach(part)
            
            if background_tasks:
                # Schedule email sending in background
                background_tasks.add_task(self._send_emails, to_emails, msg, template_id)
                return {"message": "Email queued for sending", "status": "queued"}
            else:
                # Send immediately
                return await self._send_emails(to_emails, msg, template_id)
                
        except Exception as e:
            logger.error(f"Error preparing email: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to prepare email: {str(e)}"
            )
    
    async def _send_emails(
        self, 
        to_emails: List[str], 
        msg: MIMEMultipart,
        template_id: str = None
    ) -> Dict[str, Any]:
        """Internal method to send emails and log them"""
        sent_email_ids = []
        
        try:
            # Send the email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                
                # Send to each recipient individually for tracking
                for email in to_emails:
                    msg.replace_header('To', email)
                    try:
                        server.send_message(msg)
                        status = "delivered"
                        error_msg = None
                    except Exception as e:
                        logger.error(f"Failed to send to {email}: {str(e)}")
                        status = "failed"
                        error_msg = str(e)
                    
                    # Log the sent email
                    sent_email = self._log_sent_email(
                        template_id=template_id,
                        recipient_email=email,
                        subject=msg['Subject'],
                        body=msg.get_payload(),
                        status=status,
                        error_message=error_msg
                    )
                    sent_email_ids.append(sent_email.id)
            
            return {
                "message": f"Email sent to {len(to_emails)} recipients",
                "status": "sent",
                "sent_email_ids": sent_email_ids
            }
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send email: {str(e)}"
            )
    
    def _log_sent_email(
        self,
        template_id: str,
        recipient_email: str,
        subject: str,
        body: str,
        status: str,
        error_message: str = None,
        delivery_status_code: str = None,
        delivery_details: Dict[str, Any] = None,
        opened_at: datetime = None,
        clicked_at: datetime = None
    ) -> SentEmail:
        """Log sent email to database"""
        try:
            sent_email = SentEmail(
                id=f"email_{uuid.uuid4()}",
                template_id=template_id,
                recipient_email=recipient_email,
                subject=subject,
                body=body,
                status=status,
                error_message=error_message,
                delivery_status_code=delivery_status_code,
                delivery_details=delivery_details,
                sent_at=datetime.utcnow(),
                delivered_at=datetime.utcnow() if status == "delivered" else None,
                opened_at=opened_at,
                clicked_at=clicked_at
            )
            
            self.db.add(sent_email)
            self.db.commit()
            self.db.refresh(sent_email)
            
            return sent_email
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to log sent email: {str(e)}")
            # Don't fail the whole operation if logging fails
            return None
    
    # High-level email methods
    async def send_templated_email(
        self,
        template_id: str,
        to_emails: Union[str, List[str]],
        variables: Dict[str, Any] = None,
        locale: str = "en", # New: locale parameter
        cc: List[str] = None,
        bcc: List[str] = None,
        reply_to: str = None,
        attachments: List[Dict[str, Any]] = None, # Explicit attachments for this send
        background_tasks: BackgroundTasks = None
    ) -> Dict[str, Any]:
        """Send email using a template"""
        # Get the template object
        template = await self.get_template(template_id)

        # Render template
        rendered = await self.render_template(template_id, variables, locale)
        
        # Combine predefined attachments with any provided for this send
        all_attachments = []
        if template.predefined_attachments:
            all_attachments.extend(template.predefined_attachments)
        if attachments:
            all_attachments.extend(attachments)

        # Send email
        return await self.send_email(
            to_emails=to_emails,
            subject=rendered['subject'],
            body=rendered['body'],
            template_id=template_id,
            cc=cc,
            bcc=bcc,
            reply_to=reply_to,
            attachments=all_attachments, # Pass combined attachments
            background_tasks=background_tasks
        )
    
    async def send_custom_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        cc: List[str] = None,
        bcc: List[str] = None,
        reply_to: str = None,
        attachments: List[Dict[str, Any]] = None,
        background_tasks: BackgroundTasks = None
    ) -> Dict[str, Any]:
        """Send a custom email without using a template"""
        return await self.send_email(
            to_emails=to_emails,
            subject=subject,
            body=body,
            cc=cc,
            bcc=bcc,
            reply_to=reply_to,
            attachments=attachments,
            background_tasks=background_tasks
        )
