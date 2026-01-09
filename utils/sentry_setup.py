import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from config import settings
import logging

def init_sentry():
    """Initialize Sentry for error tracking and performance monitoring"""
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=1.0,  # Capture 100% of transactions for performance monitoring
            profiles_sample_rate=1.0,  # Profile 100% of transactions
            environment=settings.SENTRY_ENVIRONMENT,
            release="education-erp@1.0.0",  # Version of your application
            enable_tracing=True,
            # Set sampling rates for different environments
            traces_sampler=lambda context: 0.1 if settings.SENTRY_ENVIRONMENT == "development" else 1.0,
        )
        
        logging.info("Sentry initialized successfully")
        return True
    else:
        logging.warning("SENTRY_DSN not configured, skipping Sentry initialization")
        return False

def capture_exception(exception: Exception, extra_context: dict = None):
    """Capture an exception with optional extra context"""
    if settings.SENTRY_DSN:
        with sentry_sdk.configure_scope() as scope:
            if extra_context:
                for key, value in extra_context.items():
                    scope.set_extra(key, value)
            sentry_sdk.capture_exception(exception)

def add_breadcrumb(category: str, message: str, level: str = "info"):
    """Add a breadcrumb to the current scope"""
    if settings.SENTRY_DSN:
        sentry_sdk.add_breadcrumb(
            category=category,
            message=message,
            level=level,
        )

def set_user_context(user_id: int, email: str = None, username: str = None):
    """Set user context for better error tracking"""
    if settings.SENTRY_DSN:
        sentry_sdk.set_user({
            "id": user_id,
            "email": email,
            "username": username,
        })
