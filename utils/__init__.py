"""
Utilities module for the Education ERP system.

This module contains utility functions, dependencies, exceptions, and other
helper functions used throughout the application.
"""

from .dependencies import get_current_user, get_current_school, require_permission
from .exceptions import (
    ERPException, NotFoundException, ValidationException, 
    UnauthorizedException, setup_exception_handlers
)
from .security import SecurityUtils
from .location import verify_location, calculate_distance

__all__ = [
    "get_current_user",
    "get_current_school", 
    "require_permission",
    "ERPException",
    "NotFoundException",
    "ValidationException",
    "UnauthorizedException",
    "setup_exception_handlers",
    "SecurityUtils",
    "verify_location",
    "calculate_distance"
]
