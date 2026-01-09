import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
# This ensures that they are available before any other modules import and use them.
load_dotenv()

class Settings:
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/education_erp")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Super Admin
    SUPER_ADMIN_EMAIL: str = os.getenv("SUPER_ADMIN_EMAIL", "admin@localhost")
    SUPER_ADMIN_USERNAME: str = os.getenv("SUPER_ADMIN_USERNAME", "superadmin")
    SUPER_ADMIN_PASSWORD: str = os.getenv("SUPER_ADMIN_PASSWORD", "SuperAdmin123!")
    SUPER_ADMIN_FIRST_NAME: str = os.getenv("SUPER_ADMIN_FIRST_NAME", "Super")
    SUPER_ADMIN_LAST_NAME: str = os.getenv("SUPER_ADMIN_LAST_NAME", "Admin")

    # Paystack
    PAYSTACK_SECRET_KEY: str = os.getenv("PAYSTACK_SECRET_KEY", "")
    PAYSTACK_PUBLIC_KEY: str = os.getenv("PAYSTACK_PUBLIC_KEY", "")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Celery
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    # Resend
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")

    # Sentry
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    SENTRY_ENVIRONMENT: str = os.getenv("SENTRY_ENVIRONMENT", "development")

    # File uploads
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "uploads"

    # Notifications
    FCM_SERVER_KEY: str = os.getenv("FCM_SERVER_KEY", "")

    # Location verification
    LOCATION_TOLERANCE_METERS: int = 100

    # Domain configuration
    ROOT_DOMAIN: str = os.getenv("ROOT_DOMAIN", "localhost")
    PLATFORM_CHARGE_PER_TRANSACTION: float = float(os.getenv("PLATFORM_CHARGE_PER_TRANSACTION", 100.0))

settings = Settings()
