import httpx
import json
from typing import Dict, Any, Optional
from config import settings

class PaystackService:
    """Service for Paystack payment integration"""
    
    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.public_key = settings.PAYSTACK_PUBLIC_KEY
        self.base_url = "https://api.paystack.co"
        
        if not self.secret_key:
            raise ValueError("PAYSTACK_SECRET_KEY environment variable is required")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Paystack API requests"""
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
    
    async def initialize_payment(
        self,
        email: str,
        amount: int,  # Amount in kobo (smallest currency unit)
        reference: str,
        callback_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Initialize a payment transaction"""
        
        payload = {
            "email": email,
            "amount": amount,
            "reference": reference,
            "currency": "NGN"
        }
        
        if callback_url:
            payload["callback_url"] = callback_url
        
        if metadata:
            payload["metadata"] = metadata
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/transaction/initialize",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                
                if result.get("status"):
                    return {
                        "status": "success",
                        "data": result.get("data", {}),
                        "message": result.get("message", "Payment initialized successfully")
                    }
                else:
                    return {
                        "status": "error",
                        "message": result.get("message", "Failed to initialize payment")
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
    
    async def verify_payment(self, reference: str) -> Dict[str, Any]:
        """Verify a payment transaction"""
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/transaction/verify/{reference}",
                    headers=self._get_headers(),
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                
                if result.get("status"):
                    return {
                        "status": "success",
                        "data": result.get("data", {}),
                        "message": result.get("message", "Payment verified successfully")
                    }
                else:
                    return {
                        "status": "error",
                        "message": result.get("message", "Failed to verify payment")
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
    
    async def create_transfer_recipient(
        self,
        name: str,
        account_number: str,
        bank_code: str,
        currency: str = "NGN"
    ) -> Dict[str, Any]:
        """Create a transfer recipient"""
        
        payload = {
            "type": "nuban",
            "name": name,
            "account_number": account_number,
            "bank_code": bank_code,
            "currency": currency
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/transferrecipient",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                
                if result.get("status"):
                    return {
                        "status": "success",
                        "data": result.get("data", {}),
                        "message": result.get("message", "Recipient created successfully")
                    }
                else:
                    return {
                        "status": "error",
                        "message": result.get("message", "Failed to create recipient")
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
    
    async def initiate_transfer(
        self,
        amount: int,  # Amount in kobo
        recipient_code: str,
        reason: str,
        reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """Initiate a transfer"""
        
        payload = {
            "source": "balance",
            "amount": amount,
            "recipient": recipient_code,
            "reason": reason
        }
        
        if reference:
            payload["reference"] = reference
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/transfer",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                
                if result.get("status"):
                    return {
                        "status": "success",
                        "data": result.get("data", {}),
                        "message": result.get("message", "Transfer initiated successfully")
                    }
                else:
                    return {
                        "status": "error",
                        "message": result.get("message", "Failed to initiate transfer")
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
    
    async def list_banks(self) -> Dict[str, Any]:
        """Get list of supported banks"""
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/bank",
                    headers=self._get_headers(),
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                
                if result.get("status"):
                    return {
                        "status": "success",
                        "data": result.get("data", []),
                        "message": result.get("message", "Banks retrieved successfully")
                    }
                else:
                    return {
                        "status": "error",
                        "message": result.get("message", "Failed to retrieve banks")
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
    
    async def verify_account_number(
        self,
        account_number: str,
        bank_code: str
    ) -> Dict[str, Any]:
        """Verify account number and get account name"""
        
        params = {
            "account_number": account_number,
            "bank_code": bank_code
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/bank/resolve",
                    headers=self._get_headers(),
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                
                if result.get("status"):
                    return {
                        "status": "success",
                        "data": result.get("data", {}),
                        "message": result.get("message", "Account verified successfully")
                    }
                else:
                    return {
                        "status": "error",
                        "message": result.get("message", "Failed to verify account")
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
    
    async def create_subscription(
        self,
        customer_email: str,
        plan_code: str,
        authorization_code: str
    ) -> Dict[str, Any]:
        """Create a subscription"""
        
        payload = {
            "customer": customer_email,
            "plan": plan_code,
            "authorization": authorization_code
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/subscription",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                
                if result.get("status"):
                    return {
                        "status": "success",
                        "data": result.get("data", {}),
                        "message": result.get("message", "Subscription created successfully")
                    }
                else:
                    return {
                        "status": "error",
                        "message": result.get("message", "Failed to create subscription")
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
