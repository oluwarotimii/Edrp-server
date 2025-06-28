from __future__ import annotations
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, Date, JSON
from sqlalchemy.orm import relationship, Mapped
from .base import TenantBaseModel
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .student import Student
    from .user import User

class FeeType(TenantBaseModel):
    __tablename__ = "fee_types"
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    amount = Column(Float, nullable=False)
    is_mandatory = Column(Boolean, default=True)
    frequency = Column(String(20), default="one_time")  # one_time, monthly, termly, annually
    due_date_type = Column(String(20), default="fixed")  # fixed, rolling
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    student_fees: Mapped[List["StudentFee"]] = relationship("StudentFee", back_populates="fee_type")

class StudentFee(TenantBaseModel):
    __tablename__ = "student_fees"
    
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    fee_type_id = Column(Integer, ForeignKey("fee_types.id"), nullable=False)
    amount = Column(Float, nullable=False)
    due_date = Column(Date)
    status = Column(String(20), default="pending")  # pending, paid, overdue, waived
    discount_amount = Column(Float, default=0.0)
    discount_reason = Column(Text)
    academic_session_id = Column(Integer, ForeignKey("academic_sessions.id"))
    term_id = Column(Integer, ForeignKey("terms.id"))
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="fees")
    fee_type: Mapped["FeeType"] = relationship("FeeType", back_populates="student_fees")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="student_fee")

class Payment(TenantBaseModel):
    __tablename__ = "payments"
    
    student_fee_id = Column(Integer, ForeignKey("student_fees.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=False)
    payment_method = Column(String(50), nullable=False)  # cash, bank_transfer, online, cheque
    reference_number = Column(String(100))
    paystack_reference = Column(String(100))
    status = Column(String(20), default="completed")  # pending, completed, failed, refunded
    recorded_by = Column(Integer, ForeignKey("users.id"))
    receipt_number = Column(String(100))
    notes = Column(Text)
    gateway_response = Column(JSON, default={})
    platform_fee_amount = Column(Float, nullable=True)
    school_net_amount = Column(Float, nullable=True)
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    student_fee: Mapped["StudentFee"] = relationship("StudentFee", back_populates="payments")
    recorder: Mapped["User"] = relationship("User")
