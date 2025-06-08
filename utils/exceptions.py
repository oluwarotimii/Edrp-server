from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

# Setup logging
logger = logging.getLogger(__name__)

class ERPException(Exception):
    """Base exception class for ERP-specific errors"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationException(ERPException):
    """Exception for validation errors"""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )
        self.field = field

class NotFoundException(ERPException):
    """Exception for resource not found errors"""
    
    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[Any] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details={
                "resource_type": resource_type,
                "resource_id": resource_id
            }
        )

class UnauthorizedException(ERPException):
    """Exception for unauthorized access"""
    
    def __init__(
        self,
        message: str = "Unauthorized access",
        required_permission: Optional[str] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details={"required_permission": required_permission}
        )

class ForbiddenException(ERPException):
    """Exception for forbidden access"""
    
    def __init__(
        self,
        message: str = "Access forbidden",
        required_role: Optional[str] = None,
        required_permission: Optional[str] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details={
                "required_role": required_role,
                "required_permission": required_permission
            }
        )

class ConflictException(ERPException):
    """Exception for resource conflicts"""
    
    def __init__(
        self,
        message: str = "Resource conflict",
        conflicting_resource: Optional[str] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details={"conflicting_resource": conflicting_resource}
        )

class BusinessLogicException(ERPException):
    """Exception for business logic violations"""
    
    def __init__(
        self,
        message: str,
        rule: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details={
                "rule": rule,
                "context": context or {}
            }
        )

class ExternalServiceException(ERPException):
    """Exception for external service errors"""
    
    def __init__(
        self,
        message: str,
        service_name: str,
        service_error: Optional[str] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details={
                "service_name": service_name,
                "service_error": service_error
            }
        )

class RateLimitException(ERPException):
    """Exception for rate limiting"""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"retry_after": retry_after}
        )

class MaintenanceException(ERPException):
    """Exception for maintenance mode"""
    
    def __init__(
        self,
        message: str = "System is under maintenance",
        estimated_duration: Optional[str] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"estimated_duration": estimated_duration}
        )

class DataIntegrityException(ERPException):
    """Exception for data integrity violations"""
    
    def __init__(
        self,
        message: str,
        table: Optional[str] = None,
        constraint: Optional[str] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details={
                "table": table,
                "constraint": constraint
            }
        )

class OfflineSyncException(ERPException):
    """Exception for offline synchronization errors"""
    
    def __init__(
        self,
        message: str,
        sync_type: Optional[str] = None,
        conflict_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details={
                "sync_type": sync_type,
                "conflict_data": conflict_data or {}
            }
        )

class PaymentException(ERPException):
    """Exception for payment processing errors"""
    
    def __init__(
        self,
        message: str,
        payment_gateway: Optional[str] = None,
        gateway_error: Optional[str] = None,
        transaction_reference: Optional[str] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            details={
                "payment_gateway": payment_gateway,
                "gateway_error": gateway_error,
                "transaction_reference": transaction_reference
            }
        )

# Exception handlers
async def erp_exception_handler(request: Request, exc: ERPException):
    """Handle custom ERP exceptions"""
    
    logger.error(
        f"ERP Exception: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "details": exc.details,
            "type": exc.__class__.__name__,
            "path": request.url.path,
            "timestamp": None  # Could add timestamp if needed
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(x) for x in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    logger.warning(
        f"Validation error on {request.method} {request.url.path}",
        extra={"errors": errors}
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "message": "Validation failed",
            "details": {
                "validation_errors": errors
            },
            "type": "ValidationError",
            "path": request.url.path
        }
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle standard HTTP exceptions"""
    
    logger.warning(
        f"HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "details": {},
            "type": "HTTPException",
            "path": request.url.path
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    
    logger.error(
        f"Unexpected error on {request.method} {request.url.path}",
        exc_info=True,
        extra={
            "exception_type": exc.__class__.__name__,
            "exception_message": str(exc)
        }
    )
    
    # Don't expose internal error details in production
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "An unexpected error occurred",
            "details": {},
            "type": "InternalServerError",
            "path": request.url.path
        }
    )

def setup_exception_handlers(app):
    """Setup all exception handlers for the FastAPI app"""
    
    # Custom ERP exceptions
    app.add_exception_handler(ERPException, erp_exception_handler)
    app.add_exception_handler(ValidationException, erp_exception_handler)
    app.add_exception_handler(NotFoundException, erp_exception_handler)
    app.add_exception_handler(UnauthorizedException, erp_exception_handler)
    app.add_exception_handler(ForbiddenException, erp_exception_handler)
    app.add_exception_handler(ConflictException, erp_exception_handler)
    app.add_exception_handler(BusinessLogicException, erp_exception_handler)
    app.add_exception_handler(ExternalServiceException, erp_exception_handler)
    app.add_exception_handler(RateLimitException, erp_exception_handler)
    app.add_exception_handler(MaintenanceException, erp_exception_handler)
    app.add_exception_handler(DataIntegrityException, erp_exception_handler)
    app.add_exception_handler(OfflineSyncException, erp_exception_handler)
    app.add_exception_handler(PaymentException, erp_exception_handler)
    
    # Standard exceptions
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

# Utility functions for creating exceptions with context
def raise_not_found(resource_type: str, resource_id: Any):
    """Raise a not found exception with context"""
    raise NotFoundException(
        message=f"{resource_type} not found",
        resource_type=resource_type,
        resource_id=resource_id
    )

def raise_validation_error(message: str, field: Optional[str] = None):
    """Raise a validation exception"""
    raise ValidationException(message=message, field=field)

def raise_permission_denied(required_permission: str):
    """Raise an unauthorized exception for missing permission"""
    raise UnauthorizedException(
        message=f"Permission required: {required_permission}",
        required_permission=required_permission
    )

def raise_forbidden(message: str = "Access forbidden"):
    """Raise a forbidden exception"""
    raise ForbiddenException(message=message)

def raise_conflict(message: str, conflicting_resource: Optional[str] = None):
    """Raise a conflict exception"""
    raise ConflictException(message=message, conflicting_resource=conflicting_resource)

def raise_business_logic_error(message: str, rule: Optional[str] = None):
    """Raise a business logic exception"""
    raise BusinessLogicException(message=message, rule=rule)

def raise_external_service_error(service_name: str, error_message: str):
    """Raise an external service exception"""
    raise ExternalServiceException(
        message=f"Error from {service_name}: {error_message}",
        service_name=service_name,
        service_error=error_message
    )

def raise_payment_error(message: str, gateway: Optional[str] = None, reference: Optional[str] = None):
    """Raise a payment exception"""
    raise PaymentException(
        message=message,
        payment_gateway=gateway,
        transaction_reference=reference
    )

# Context managers for error handling
class ErrorContext:
    """Context manager for handling errors in specific operations"""
    
    def __init__(
        self,
        operation: str,
        logger_name: Optional[str] = None,
        reraise: bool = True
    ):
        self.operation = operation
        self.logger = logging.getLogger(logger_name or __name__)
        self.reraise = reraise
    
    def __enter__(self):
        self.logger.debug(f"Starting operation: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(
                f"Error in operation '{self.operation}': {exc_val}",
                exc_info=True
            )
            
            if self.reraise:
                if isinstance(exc_val, ERPException):
                    return False  # Re-raise ERP exceptions as-is
                else:
                    # Wrap other exceptions
                    raise ERPException(
                        message=f"Error in {self.operation}: {str(exc_val)}",
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                    ) from exc_val
        else:
            self.logger.debug(f"Completed operation: {self.operation}")
        
        return False

# Decorator for error handling
def handle_errors(operation_name: str):
    """Decorator to handle errors in functions"""
    
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            with ErrorContext(operation_name):
                return await func(*args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            with ErrorContext(operation_name):
                return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

import asyncio  # Add this import at the top
