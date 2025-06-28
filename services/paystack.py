import os
import httpx
import hashlib
import hmac
import json

from fastapi import HTTPException, status

class PaystackService:
    def __init__(self):
        self.base_url = "https://api.paystack.co"
        self.secret_key = os.environ.get("PAYSTACK_SECRET_KEY")
        self.public_key = os.environ.get("PAYSTACK_PUBLIC_KEY")

        if not self.secret_key or not self.public_key:
            raise ValueError("Paystack API keys are not set in environment variables")

        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }

    async def _make_request(self, method: str, endpoint: str, data: dict = None):
        url = f"{self.base_url}/{endpoint}"
        async with httpx.AsyncClient() as client:
            try:
                if method == "POST":
                    response = await client.post(url, headers=self.headers, json=data)
                elif method == "GET":
                    response = await client.get(url, headers=self.headers)
                else:
                    raise ValueError("Unsupported HTTP method")

                response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
                return response.json()
            except httpx.RequestError as exc:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"An error occurred while requesting {exc.request.url!r}."
                ) from exc
            except httpx.HTTPStatusError as exc:
                raise HTTPException(
                    status_code=exc.response.status_code,
                    detail=f"Error response {exc.response.status_code} while requesting {exc.request.url!r}: {exc.response.text}"
                ) from exc

    async def initialize_payment(self, email: str, amount: int, reference: str, callback_url: str = None, subaccount: str = None, transaction_charge: int = None):
        """Initialize a payment transaction with Paystack."""
        data = {
            "email": email,
            "amount": amount,  # amount in kobo
            "reference": reference,
            "callback_url": callback_url
        }
        
        if subaccount:
            data["subaccount"] = subaccount
            data["transaction_charge"] = transaction_charge
            data["bearer"] = "subaccount" # This ensures the transaction charge is borne by the subaccount
            
        return await self._make_request("POST", "transaction/initialize", data)

    async def create_subaccount(self, business_name: str, settlement_bank: str, account_number: str, percentage_charge: float = 0.0):
        """Create a subaccount with Paystack."""
        data = {
            "business_name": business_name,
            "settlement_bank": settlement_bank,
            "account_number": account_number,
            "percentage_charge": percentage_charge,
            "primary_contact_email": "info@edrp.com" # Placeholder, can be dynamic
        }
        return await self._make_request("POST", "subaccount", data)

    async def verify_payment(self, reference: str):
        """Verify a payment transaction with Paystack."""
        return await self._make_request("GET", f"transaction/verify/{reference}")

    async def create_plan(self, name: str, amount: int, interval: str, plan_code: str = None):
        """Create a subscription plan with Paystack."""
        data = {
            "name": name,
            "amount": amount,  # amount in kobo
            "interval": interval,
            "plan_code": plan_code
        }
        return await self._make_request("POST", "plan", data)

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify the Paystack webhook signature."""
        if not self.secret_key:
            return False
        
        hash_object = hmac.new(self.secret_key.encode('utf-8'), msg=payload, digestmod=hashlib.sha512)
        return hash_object.hexdigest() == signature
