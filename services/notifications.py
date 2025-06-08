import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import httpx

from config import settings
from models.user import User
from models.student import Student, StudentParent
from models.communication import Message

class NotificationService:
    """Service for handling push notifications and real-time alerts"""
    
    def __init__(self):
        self.fcm_server_key = settings.FCM_SERVER_KEY
        self.fcm_url = "https://fcm.googleapis.com/fcm/send"
        
    def _get_fcm_headers(self) -> Dict[str, str]:
        """Get headers for FCM requests"""
        return {
            "Authorization": f"key={self.fcm_server_key}",
            "Content-Type": "application/json"
        }
    
    async def send_push_notification(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """Send push notification via FCM"""
        
        if not self.fcm_server_key:
            return {"status": "error", "message": "FCM server key not configured"}
        
        if not tokens:
            return {"status": "error", "message": "No device tokens provided"}
        
        payload = {
            "registration_ids": tokens,
            "notification": {
                "title": title,
                "body": body,
                "sound": "default",
                "badge": 1
            },
            "priority": priority,
            "content_available": True
        }
        
        if data:
            payload["data"] = data
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.fcm_url,
                    headers=self._get_fcm_headers(),
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                
                return {
                    "status": "success",
                    "data": result,
                    "sent_count": result.get("success", 0),
                    "failed_count": result.get("failure", 0)
                }
                
            except httpx.RequestError as e:
                return {
                    "status": "error",
                    "message": f"Network error: {str(e)}"
                }
            except httpx.HTTPStatusError as e:
                return {
                    "status": "error",
                    "message": f"HTTP error: {e.response.status_code}"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Unexpected error: {str(e)}"
                }
    
    async def send_message_notification(
        self,
        recipient_id: int,
        sender_name: str,
        subject: str,
        priority: str = "normal"
    ) -> None:
        """Send notification for new message"""
        
        # In a real implementation, you would:
        # 1. Get recipient's device tokens from a user_devices table
        # 2. Send push notification
        
        title = f"New message from {sender_name}"
        body = subject
        
        # Placeholder for device tokens - in real implementation, 
        # fetch from user_devices table
        tokens = []  # Would be populated from database
        
        if tokens:
            await self.send_push_notification(
                tokens=tokens,
                title=title,
                body=body,
                data={
                    "type": "message",
                    "sender_name": sender_name,
                    "priority": priority
                },
                priority="high" if priority in ["high", "urgent"] else "normal"
            )
    
    async def send_attendance_alert(
        self,
        student_id: int,
        student_name: str,
        status: str,
        date: str,
        db: Session
    ) -> None:
        """Send attendance alert to parents"""
        
        # Get student's parents
        parents = db.query(StudentParent).filter(
            StudentParent.student_id == student_id
        ).all()
        
        if not parents:
            return
        
        title = f"Attendance Alert - {student_name}"
        body = f"Your child was marked {status} on {date}"
        
        for parent_link in parents:
            # Get parent's device tokens
            tokens = []  # Would be populated from user_devices table
            
            if tokens:
                await self.send_push_notification(
                    tokens=tokens,
                    title=title,
                    body=body,
                    data={
                        "type": "attendance",
                        "student_id": student_id,
                        "student_name": student_name,
                        "status": status,
                        "date": date
                    },
                    priority="high"
                )
    
    async def send_behavior_report_notification(
        self,
        student_id: int,
        incident_title: str,
        severity: str,
        db: Session
    ) -> None:
        """Send behavior report notification to parents"""
        
        # Get student and parents
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return
        
        parents = db.query(StudentParent).filter(
            StudentParent.student_id == student_id
        ).all()
        
        if not parents:
            return
        
        student_name = f"{student.user.first_name} {student.user.last_name}"
        title = f"Behavior Report - {student_name}"
        body = f"New {severity} incident: {incident_title}"
        
        for parent_link in parents:
            tokens = []  # Would be populated from user_devices table
            
            if tokens:
                await self.send_push_notification(
                    tokens=tokens,
                    title=title,
                    body=body,
                    data={
                        "type": "behavior_report",
                        "student_id": student_id,
                        "student_name": student_name,
                        "incident_title": incident_title,
                        "severity": severity
                    },
                    priority="high"
                )
    
    async def send_fee_reminder(
        self,
        student_id: int,
        student_name: str,
        fee_type: str,
        amount: float,
        due_date: str,
        db: Session
    ) -> None:
        """Send fee payment reminder to parents"""
        
        parents = db.query(StudentParent).filter(
            StudentParent.student_id == student_id
        ).all()
        
        if not parents:
            return
        
        title = f"Fee Reminder - {student_name}"
        body = f"{fee_type} payment of ₦{amount:,.2f} is due on {due_date}"
        
        for parent_link in parents:
            tokens = []  # Would be populated from user_devices table
            
            if tokens:
                await self.send_push_notification(
                    tokens=tokens,
                    title=title,
                    body=body,
                    data={
                        "type": "fee_reminder",
                        "student_id": student_id,
                        "student_name": student_name,
                        "fee_type": fee_type,
                        "amount": amount,
                        "due_date": due_date
                    },
                    priority="normal"
                )
    
    async def send_assessment_results_notification(
        self,
        student_id: int,
        student_name: str,
        assessment_name: str,
        subject: str,
        score: float,
        max_score: float,
        db: Session
    ) -> None:
        """Send assessment results notification"""
        
        parents = db.query(StudentParent).filter(
            StudentParent.student_id == student_id
        ).all()
        
        if not parents:
            return
        
        percentage = (score / max_score) * 100 if max_score > 0 else 0
        title = f"Assessment Results - {student_name}"
        body = f"{assessment_name} ({subject}): {score}/{max_score} ({percentage:.1f}%)"
        
        for parent_link in parents:
            tokens = []  # Would be populated from user_devices table
            
            if tokens:
                await self.send_push_notification(
                    tokens=tokens,
                    title=title,
                    body=body,
                    data={
                        "type": "assessment_results",
                        "student_id": student_id,
                        "student_name": student_name,
                        "assessment_name": assessment_name,
                        "subject": subject,
                        "score": score,
                        "max_score": max_score,
                        "percentage": percentage
                    },
                    priority="normal"
                )
    
    async def send_happening_notification(
        self,
        happening_id: int,
        title: str,
        category: str,
        target_audience: str,
        school_id: int,
        db: Session
    ) -> None:
        """Send happening/event notification to target audience"""
        
        # Determine target users based on audience
        target_users = []
        
        if target_audience == "all":
            target_users = db.query(User).filter(
                User.school_id == school_id,
                User.is_active == True
            ).all()
        elif target_audience == "students":
            target_users = db.query(User).join(Student).filter(
                User.school_id == school_id,
                User.is_active == True,
                Student.status == "active"
            ).all()
        elif target_audience == "teachers":
            from models.teacher import Teacher
            target_users = db.query(User).join(Teacher).filter(
                User.school_id == school_id,
                User.is_active == True,
                Teacher.status == "active"
            ).all()
        elif target_audience == "parents":
            parent_user_ids = db.query(StudentParent.parent_user_id).distinct().all()
            target_users = db.query(User).filter(
                User.id.in_([uid[0] for uid in parent_user_ids]),
                User.school_id == school_id,
                User.is_active == True
            ).all()
        
        if not target_users:
            return
        
        notification_title = f"School {category.title()}"
        notification_body = title
        
        # Send notifications in batches to avoid overwhelming FCM
        batch_size = 500
        for i in range(0, len(target_users), batch_size):
            batch = target_users[i:i + batch_size]
            tokens = []  # Would be populated from user_devices table for each user
            
            if tokens:
                await self.send_push_notification(
                    tokens=tokens,
                    title=notification_title,
                    body=notification_body,
                    data={
                        "type": "happening",
                        "happening_id": happening_id,
                        "category": category,
                        "target_audience": target_audience
                    },
                    priority="high" if category == "emergency" else "normal"
                )
    
    async def send_bulk_notification(
        self,
        user_ids: List[int],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """Send bulk notification to multiple users"""
        
        # In a real implementation, you would:
        # 1. Get device tokens for all user_ids
        # 2. Send in batches to respect FCM limits
        
        all_tokens = []  # Would be populated from user_devices table
        
        if not all_tokens:
            return {"status": "error", "message": "No device tokens found"}
        
        # Send in batches
        batch_size = 500
        total_sent = 0
        total_failed = 0
        
        for i in range(0, len(all_tokens), batch_size):
            batch_tokens = all_tokens[i:i + batch_size]
            result = await self.send_push_notification(
                tokens=batch_tokens,
                title=title,
                body=body,
                data=data,
                priority=priority
            )
            
            if result["status"] == "success":
                total_sent += result.get("sent_count", 0)
                total_failed += result.get("failed_count", 0)
        
        return {
            "status": "success",
            "total_sent": total_sent,
            "total_failed": total_failed
        }
    
    async def send_emergency_notification(
        self,
        school_id: int,
        title: str,
        message: str,
        db: Session
    ) -> None:
        """Send emergency notification to all school users"""
        
        users = db.query(User).filter(
            User.school_id == school_id,
            User.is_active == True
        ).all()
        
        user_ids = [user.id for user in users]
        
        await self.send_bulk_notification(
            user_ids=user_ids,
            title=f"🚨 EMERGENCY: {title}",
            body=message,
            data={
                "type": "emergency",
                "school_id": school_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            priority="high"
        )
    
    def create_notification_data(
        self,
        notification_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Create standardized notification data payload"""
        
        base_data = {
            "type": notification_type,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0"
        }
        
        base_data.update(kwargs)
        return base_data
    
    async def schedule_notification(
        self,
        scheduled_time: datetime,
        user_ids: List[int],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Schedule a notification for future delivery"""
        
        # In a real implementation, this would:
        # 1. Store the notification in a scheduled_notifications table
        # 2. Use a background task scheduler (like Celery) to send at scheduled time
        # 3. Return a unique job ID for tracking
        
        import uuid
        job_id = str(uuid.uuid4())
        
        # Placeholder for scheduling logic
        # This would typically use a task queue like Celery or APScheduler
        
        return job_id
    
    async def cancel_scheduled_notification(self, job_id: str) -> bool:
        """Cancel a scheduled notification"""
        
        # In a real implementation, this would:
        # 1. Find the scheduled notification by job_id
        # 2. Cancel the scheduled task
        # 3. Update the database record
        
        return True
    
    def validate_notification_data(self, data: Dict[str, Any]) -> bool:
        """Validate notification data structure"""
        
        required_fields = ["type", "timestamp"]
        
        for field in required_fields:
            if field not in data:
                return False
        
        # Additional validation based on notification type
        notification_type = data.get("type")
        
        if notification_type == "message":
            return "sender_name" in data
        elif notification_type == "attendance":
            return all(field in data for field in ["student_id", "status", "date"])
        elif notification_type == "fee_reminder":
            return all(field in data for field in ["student_id", "fee_type", "amount"])
        
        return True
