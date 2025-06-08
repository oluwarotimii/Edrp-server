from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date

class FeeTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    amount: float
    is_mandatory: bool = True
    frequency: str = "one_time"
    due_date_type: str = "fixed"

class FeeTypeCreate(FeeTypeBase):
    pass

class FeeTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    is_mandatory: Optional[bool] = None
    frequency: Optional[str] = None
    due_date_type: Optional[str] = None

class FeeType(FeeTypeBase):
    id: int
    school_id: int
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class StudentFeeBase(BaseModel):
    student_id: int
    fee_type_id: int
    amount: float
    due_date: Optional[date] = None
    discount_amount: float = 0.0
    discount_reason: Optional[str] = None
    academic_session_id: Optional[int] = None
    term_id: Optional[int] = None

class StudentFeeCreate(StudentFeeBase):
    pass

class StudentFeeUpdate(BaseModel):
    amount: Optional[float] = None
    due_date: Optional[date] = None
    discount_amount: Optional[float] = None
    discount_reason: Optional[str] = None
    status: Optional[str] = None

class StudentFee(StudentFeeBase):
    id: int
    school_id: int
    status: str = "pending"
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class BulkStudentFeeCreate(BaseModel):
    fee_type_id: int
    student_ids: List[int]
    amount: Optional[float] = None  # If None, use fee type default
    due_date: Optional[date] = None
    academic_session_id: Optional[int] = None
    term_id: Optional[int] = None

class PaymentBase(BaseModel):
    student_fee_id: int
    amount: float
    payment_date: date
    payment_method: str
    reference_number: Optional[str] = None
    notes: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class Payment(PaymentBase):
    id: int
    school_id: int
    paystack_reference: Optional[str] = None
    status: str = "completed"
    recorded_by: Optional[int] = None
    receipt_number: Optional[str] = None
    gateway_response: Dict[str, Any] = {}
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class PaystackPaymentInit(BaseModel):
    student_fee_id: int
    email: str
    callback_url: Optional[str] = None

class PaystackPaymentVerify(BaseModel):
    reference: str

class FeeSummary(BaseModel):
    student_id: int
    total_fees: float
    total_paid: float
    total_outstanding: float
    total_discount: float
    fee_details: List[Dict[str, Any]]
