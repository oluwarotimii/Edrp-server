import hashlib
import secrets
import string
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import re
import ipaddress
from fastapi import Request
import hashlib
import secrets

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    salt = hashed_password[:32]
    key = hashed_password[32:]
    new_key = hashlib.pbkdf2_hmac(
        'sha256',
        plain_password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return new_key.hex() == key

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return f"{salt}{key}"


class SecurityUtils:
    """Utility class for security-related operations"""
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a cryptographically secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_numeric_code(length: int = 6) -> str:
        """Generate a numeric code for OTP, join codes, etc."""
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    @staticmethod
    def generate_alphanumeric_code(length: int = 8) -> str:
        """Generate an alphanumeric code"""
        alphabet = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def hash_sensitive_data(data: str, salt: Optional[str] = None) -> Dict[str, str]:
        """Hash sensitive data with salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        combined = f"{salt}{data}"
        hashed = hashlib.sha256(combined.encode()).hexdigest()
        
        return {
            "hash": hashed,
            "salt": salt
        }
    
    @staticmethod
    def verify_hashed_data(data: str, stored_hash: str, salt: str) -> bool:
        """Verify hashed data"""
        combined = f"{salt}{data}"
        computed_hash = hashlib.sha256(combined.encode()).hexdigest()
        return secrets.compare_digest(computed_hash, stored_hash)
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone_number(phone: str, country_code: str = "NG") -> bool:
        """Validate phone number format"""
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        if country_code == "NG":  # Nigeria
            # Nigerian numbers: 11 digits starting with 0, or 10 digits without 0
            # or 13 digits with +234, or 14 digits with 234
            if len(digits_only) == 11 and digits_only.startswith('0'):
                return True
            elif len(digits_only) == 10:
                return True
            elif len(digits_only) == 13 and digits_only.startswith('234'):
                return True
            elif len(digits_only) == 14 and digits_only.startswith('234'):
                return True
        
        return False
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 1000) -> str:
        """Sanitize user input to prevent XSS and other attacks"""
        if not text:
            return ""
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length]
        
        # Remove control characters except newlines and tabs
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        return text.strip()
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength and return detailed feedback"""
        result = {
            "is_strong": False,
            "score": 0,
            "feedback": []
        }
        
        if len(password) < 8:
            result["feedback"].append("Password must be at least 8 characters long")
        else:
            result["score"] += 1
        
        if not re.search(r'[a-z]', password):
            result["feedback"].append("Password must contain at least one lowercase letter")
        else:
            result["score"] += 1
        
        if not re.search(r'[A-Z]', password):
            result["feedback"].append("Password must contain at least one uppercase letter")
        else:
            result["score"] += 1
        
        if not re.search(r'\d', password):
            result["feedback"].append("Password must contain at least one number")
        else:
            result["score"] += 1
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            result["feedback"].append("Password should contain at least one special character")
        else:
            result["score"] += 1
        
        # Check for common patterns
        if re.search(r'(.)\1{2,}', password):
            result["feedback"].append("Avoid repeating characters more than twice")
            result["score"] -= 1
        
        if re.search(r'(012|123|234|345|456|567|678|789|890)', password):
            result["feedback"].append("Avoid sequential numbers")
            result["score"] -= 1
        
        if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
            result["feedback"].append("Avoid sequential letters")
            result["score"] -= 1
        
        # Common passwords check
        common_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        ]
        if password.lower() in common_passwords:
            result["feedback"].append("Avoid common passwords")
            result["score"] -= 2
        
        result["score"] = max(0, result["score"])
        result["is_strong"] = result["score"] >= 4 and len(result["feedback"]) == 0
        
        return result
    
    @staticmethod
    def get_client_ip(request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, get the first one
            ip = forwarded_for.split(",")[0].strip()
            try:
                ipaddress.ip_address(ip)
                return ip
            except ValueError:
                pass
        
        # Check other common headers
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            try:
                ipaddress.ip_address(real_ip)
                return real_ip
            except ValueError:
                pass
        
        # Fall back to client host
        client_host = request.client.host if request.client else "unknown"
        return client_host
    
    @staticmethod
    def is_safe_redirect_url(url: str, allowed_hosts: List[str]) -> bool:
        """Check if a redirect URL is safe"""
        if not url:
            return False
        
        # Check for protocol-relative URLs
        if url.startswith("//"):
            return False
        
        # Check for absolute URLs with different hosts
        if url.startswith(("http://", "https://")):
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc in allowed_hosts
        
        # Relative URLs are generally safe
        if url.startswith("/"):
            return True
        
        return False
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def verify_csrf_token(token: str, session_token: str) -> bool:
        """Verify CSRF token"""
        return secrets.compare_digest(token, session_token)
    
    @staticmethod
    def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
        """Mask sensitive data like phone numbers, email addresses"""
        if not data or len(data) <= visible_chars:
            return data
        
        if "@" in data:  # Email
            username, domain = data.split("@", 1)
            if len(username) <= 2:
                masked_username = mask_char * len(username)
            else:
                masked_username = username[:1] + mask_char * (len(username) - 2) + username[-1:]
            return f"{masked_username}@{domain}"
        else:  # Phone or other data
            visible_start = min(2, visible_chars // 2)
            visible_end = min(2, visible_chars - visible_start)
            masked_middle = mask_char * (len(data) - visible_start - visible_end)
            return data[:visible_start] + masked_middle + data[-visible_end:] if visible_end > 0 else data[:visible_start] + masked_middle
    
    @staticmethod
    def rate_limit_key(identifier: str, action: str, window: str = "1h") -> str:
        """Generate rate limiting key"""
        return f"rate_limit:{action}:{identifier}:{window}"
    
    @staticmethod
    def calculate_rate_limit_window(window: str) -> int:
        """Calculate rate limit window in seconds"""
        if window.endswith('s'):
            return int(window[:-1])
        elif window.endswith('m'):
            return int(window[:-1]) * 60
        elif window.endswith('h'):
            return int(window[:-1]) * 3600
        elif window.endswith('d'):
            return int(window[:-1]) * 86400
        else:
            return 3600  # Default to 1 hour
    
    @staticmethod
    def validate_file_upload(
        filename: str,
        file_size: int,
        allowed_extensions: List[str],
        max_size: int = 10 * 1024 * 1024  # 10MB
    ) -> Dict[str, Any]:
        """Validate file upload"""
        result = {
            "is_valid": True,
            "errors": []
        }
        
        if not filename:
            result["is_valid"] = False
            result["errors"].append("Filename is required")
            return result
        
        # Check file extension
        if '.' not in filename:
            result["is_valid"] = False
            result["errors"].append("File must have an extension")
        else:
            extension = filename.rsplit('.', 1)[1].lower()
            if extension not in [ext.lower() for ext in allowed_extensions]:
                result["is_valid"] = False
                result["errors"].append(f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}")
        
        # Check file size
        if file_size > max_size:
            result["is_valid"] = False
            result["errors"].append(f"File size exceeds maximum limit of {max_size // (1024*1024)}MB")
        
        # Check for potentially dangerous filenames
        dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
        if any(char in filename for char in dangerous_chars):
            result["is_valid"] = False
            result["errors"].append("Filename contains invalid characters")
        
        return result
    
    @staticmethod
    def generate_secure_filename(original_filename: str) -> str:
        """Generate a secure filename"""
        import uuid
        import os
        
        # Get file extension
        if '.' in original_filename:
            extension = original_filename.rsplit('.', 1)[1].lower()
        else:
            extension = 'bin'
        
        # Generate UUID-based filename
        secure_name = f"{uuid.uuid4().hex}.{extension}"
        
        return secure_name
    
    @staticmethod
    def audit_log_entry(
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[int],
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create audit log entry"""
        return {
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def constant_time_compare(a: str, b: str) -> bool:
        """Constant time string comparison to prevent timing attacks"""
        return secrets.compare_digest(a, b)
