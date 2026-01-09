from celery import Celery
from config import settings

# Create Celery instance
celery_app = Celery(
    "education_erp",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "tasks.email_tasks",
        "tasks.report_tasks",
        "tasks.attendance_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,  # Results expire after 1 hour
    task_routes={
        "tasks.email_tasks.send_bulk_email": {"queue": "email"},
        "tasks.report_tasks.generate_pdf_report": {"queue": "reports"},
        "tasks.attendance_tasks.process_attendance_sync": {"queue": "attendance"},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

if __name__ == "__main__":
    celery_app.start()
