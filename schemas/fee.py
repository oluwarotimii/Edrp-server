from pydantic import BaseModel, field_validator
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, date

# --- Enums for Fee Schemas ---
class FeeFrequencyEnum(str, Enum):
    ONE_TIME = "one_time"
    TERMLY = "termly"
    ANNUALLY = "annually"
    MONTHLY = "monthly"

class FeeDueDateTypeEnum(str, Enum):
    FIXED = "fixed"
    RELATIVE = "relative"

class StudentFeeStatusEnum(str, Enum):
    PENDING = "Pending"
    PAID = "Paid"
    PARTIALLY_PAID = "Partially Paid"
    OVERDUE = "Overdue"

class PaymentMethodEnum(str, Enum):
    CASH = "Cash"
    BANK_TRANSFER = "Bank Transfer"
    CARD = "Card"
    ONLINE = "Online"

class PaymentStatusEnum(str, Enum):
    COMPLETED = "Completed"
    PENDING = "Pending"
    FAILED = "Failed"

class FeeTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    amount: float
    is_mandatory: bool = True
    frequency: FeeFrequencyEnum = FeeFrequencyEnum.ONE_TIME
    due_date_type: FeeDueDateTypeEnum = FeeDueDateTypeEnum.FIXED

    @field_validator('frequency', 'due_date_type', mode='before')
    @classmethod
    def lower_case_fields(cls, v: str) -> str:
        if isinstance(v, str):
            return v.lower()
        return v

class FeeTypeCreate(FeeTypeBase):
    pass

class FeeTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    is_mandatory: Optional[bool] = None
    frequency: Optional[FeeFrequencyEnum] = None
    due_date_type: Optional[FeeDueDateTypeEnum] = None

    @field_validator('frequency', 'due_date_type', mode='before')
    @classmethod
    def lower_case_fields(cls, v: str) -> str:
        if isinstance(v, str):
            return v.lower()
        return v

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
    status: Optional[StudentFeeStatusEnum] = None

    @field_validator('status', mode='before')
    @classmethod
    def title_case_status(cls, v: str) -> str:
        if isinstance(v, str):
            return v.title()
        return v

class StudentFee(StudentFeeBase):
    id: int
    school_id: int
    status: StudentFeeStatusEnum = StudentFeeStatusEnum.PENDING

    @field_validator('status', mode='before')
    @classmethod
    def title_case_status(cls, v: str) -> str:
        if isinstance(v, str):
            return v.title()
        return v
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
    payment_method: PaymentMethodEnum

    @field_validator('payment_method', mode='before')
    @classmethod
    def title_case_payment_method(cls, v: str) -> str:
        if isinstance(v, str):
            return v.title()
        return v
    reference_number: Optional[str] = None
    notes: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatusEnum] = None

    @field_validator('status', mode='before')
    @classmethod
    def title_case_status(cls, v: str) -> str:
        if isinstance(v, str):
            return v.title()
        return v
    notes: Optional[str] = None

class Payment(PaymentBase):
    id: int
    school_id: int
    paystack_reference: Optional[str] = None
    status: PaymentStatusEnum = PaymentStatusEnum.COMPLETED

    @field_validator('status', mode='before')
    @classmethod
    def title_case_status(cls, v: str) -> str:
        if isinstance(v, str):
            return v.title()
        return v
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
