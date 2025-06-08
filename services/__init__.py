"""
Services module for the Education ERP system.

This module contains business logic services that handle complex operations
across multiple models and provide reusable functionality.
"""

from .auth import AuthService
from .permissions import PermissionService
from .notifications import NotificationService
from .paystack import PaystackService
from .offline_sync import OfflineSyncService

__all__ = [
    "AuthService",
    "PermissionService", 
    "NotificationService",
    "PaystackService",
    "OfflineSyncService"
]
