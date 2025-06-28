from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from database import get_db
from models.fee import FeeType, StudentFee, Payment
from models.student import Student
from models.user import User
from models.school import School
from models.global_settings import GlobalSetting
from schemas.fee import (
    FeeType as FeeTypeSchema, FeeTypeCreate, FeeTypeUpdate,
    StudentFee as StudentFeeSchema, StudentFeeCreate, StudentFeeUpdate, BulkStudentFeeCreate,
    Payment as PaymentSchema, PaymentCreate, PaymentUpdate,
    PaystackPaymentInit, PaystackPaymentVerify, FeeSummary
)
from services.paystack import PaystackService
from utils.dependencies import get_current_user, require_permission, get_current_school
from utils.exceptions import NotFoundException, ValidationException

router = APIRouter()

# Fee Type endpoints
@router.post("/fee-types", response_model=FeeTypeSchema)
async def create_fee_type(
    fee_type: FeeTypeCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create a new fee type"""
    require_permission("fee_types:create")(current_user)
    
    db_fee_type = FeeType(
        name=fee_type.name,
        description=fee_type.description,
        amount=fee_type.amount,
        is_mandatory=fee_type.is_mandatory,
        frequency=fee_type.frequency,
        due_date_type=fee_type.due_date_type,
        school_id=school_id
    )
    
    db.add(db_fee_type)
    db.commit()
    db.refresh(db_fee_type)
    
    return db_fee_type

@router.get("/fee-types", response_model=List[FeeTypeSchema])
async def get_fee_types(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get fee types"""
    require_permission("fee_types:view")(current_user)
    
    fee_types = db.query(FeeType).filter(
        FeeType.school_id == school_id
    ).offset(skip).limit(limit).all()
    
    return fee_types

@router.get("/fee-types/{fee_type_id}", response_model=FeeTypeSchema)
async def get_fee_type(
    fee_type_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get a specific fee type"""
    require_permission("fee_types:view")(current_user)
    
    fee_type = db.query(FeeType).filter(
        FeeType.id == fee_type_id,
        FeeType.school_id == school_id
    ).first()
    
    if not fee_type:
        raise NotFoundException("Fee type not found")
    
    return fee_type

@router.put("/fee-types/{fee_type_id}", response_model=FeeTypeSchema)
async def update_fee_type(
    fee_type_id: int,
    fee_type_update: FeeTypeUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update a fee type"""
    require_permission("fee_types:update")(current_user)
    
    fee_type = db.query(FeeType).filter(
        FeeType.id == fee_type_id,
        FeeType.school_id == school_id
    ).first()
    
    if not fee_type:
        raise NotFoundException("Fee type not found")
    
    # Update fields
    for field, value in fee_type_update.dict(exclude_unset=True).items():
        setattr(fee_type, field, value)
    
    db.commit()
    db.refresh(fee_type)
    
    return fee_type

# Student Fee endpoints
@router.post("/student-fees", response_model=StudentFeeSchema)
async def create_student_fee(
    student_fee: StudentFeeCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create a student fee"""
    require_permission("student_fees:create")(current_user)
    
    # Verify student exists
    student = db.query(Student).filter(
        Student.id == student_fee.student_id,
        Student.school_id == school_id
    ).first()
    
    if not student:
        raise NotFoundException("Student not found")
    
    # Verify fee type exists
    fee_type = db.query(FeeType).filter(
        FeeType.id == student_fee.fee_type_id,
        FeeType.school_id == school_id
    ).first()
    
    if not fee_type:
        raise NotFoundException("Fee type not found")
    
    db_student_fee = StudentFee(
        student_id=student_fee.student_id,
        fee_type_id=student_fee.fee_type_id,
        amount=student_fee.amount,
        due_date=student_fee.due_date,
        discount_amount=student_fee.discount_amount,
        discount_reason=student_fee.discount_reason,
        academic_session_id=student_fee.academic_session_id,
        term_id=student_fee.term_id,
        school_id=school_id
    )
    
    db.add(db_student_fee)
    db.commit()
    db.refresh(db_student_fee)
    
    return db_student_fee

@router.get("/student-fees", response_model=List[StudentFeeSchema])
async def get_student_fees(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get student fees"""
    require_permission("student_fees:view")(current_user)
    
    query = db.query(StudentFee).filter(StudentFee.school_id == school_id)
    
    if student_id:
        query = query.filter(StudentFee.student_id == student_id)
    
    if status:
        query = query.filter(StudentFee.status == status)
    
    fees = query.offset(skip).limit(limit).all()
    return fees

@router.post("/student-fees/bulk", response_model=List[StudentFeeSchema])
async def create_bulk_student_fees(
    bulk_fees: BulkStudentFeeCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create bulk student fees"""
    require_permission("student_fees:create")(current_user)
    
    # Verify fee type exists
    fee_type = db.query(FeeType).filter(
        FeeType.id == bulk_fees.fee_type_id,
        FeeType.school_id == school_id
    ).first()
    
    if not fee_type:
        raise NotFoundException("Fee type not found")
    
    created_fees = []
    
    for student_id in bulk_fees.student_ids:
        # Verify student exists
        student = db.query(Student).filter(
            Student.id == student_id,
            Student.school_id == school_id
        ).first()
        
        if not student:
            continue  # Skip invalid students
        
        # Check if fee already exists
        existing_fee = db.query(StudentFee).filter(
            StudentFee.student_id == student_id,
            StudentFee.fee_type_id == bulk_fees.fee_type_id,
            StudentFee.academic_session_id == bulk_fees.academic_session_id,
            StudentFee.term_id == bulk_fees.term_id
        ).first()
        
        if existing_fee:
            continue  # Skip if already exists
        
        db_fee = StudentFee(
            student_id=student_id,
            fee_type_id=bulk_fees.fee_type_id,
            amount=bulk_fees.amount or fee_type.amount,
            due_date=bulk_fees.due_date,
            academic_session_id=bulk_fees.academic_session_id,
            term_id=bulk_fees.term_id,
            school_id=school_id
        )
        
        db.add(db_fee)
        created_fees.append(db_fee)
    
    db.commit()
    
    for fee in created_fees:
        db.refresh(fee)
    
    return created_fees

@router.get("/student-fees/{fee_id}", response_model=StudentFeeSchema)
async def get_student_fee(
    fee_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get a specific student fee"""
    fee = db.query(StudentFee).filter(
        StudentFee.id == fee_id,
        StudentFee.school_id == school_id
    ).first()
    
    if not fee:
        raise NotFoundException("Student fee not found")
    
    # Check permissions - students/parents can view their own fees
    if not _can_access_student_fee(current_user, fee, db):
        require_permission("student_fees:view")(current_user)
    
    return fee

@router.put("/student-fees/{fee_id}", response_model=StudentFeeSchema)
async def update_student_fee(
    fee_id: int,
    fee_update: StudentFeeUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update a student fee"""
    require_permission("student_fees:update")(current_user)
    
    fee = db.query(StudentFee).filter(
        StudentFee.id == fee_id,
        StudentFee.school_id == school_id
    ).first()
    
    if not fee:
        raise NotFoundException("Student fee not found")
    
    # Update fields
    for field, value in fee_update.dict(exclude_unset=True).items():
        setattr(fee, field, value)
    
    db.commit()
    db.refresh(fee)
    
    return fee

@router.get("/student-fees/summary/{student_id}", response_model=FeeSummary)
async def get_fee_summary(
    student_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get fee summary for a student"""
    # Verify student exists
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.school_id == school_id
    ).first()
    
    if not student:
        raise NotFoundException("Student not found")
    
    # Check permissions
    if not _can_access_student_data(current_user, student, db):
        require_permission("student_fees:view")(current_user)
    
    # Get all fees for the student
    fees = db.query(StudentFee).filter(
        StudentFee.student_id == student_id
    ).all()
    
    total_fees = sum(fee.amount for fee in fees)
    total_discount = sum(fee.discount_amount for fee in fees)
    
    # Get all payments
    payments = db.query(Payment).join(StudentFee).filter(
        StudentFee.student_id == student_id,
        Payment.status == "completed"
    ).all()
    
    total_paid = sum(payment.amount for payment in payments)
    total_outstanding = total_fees - total_discount - total_paid
    
    # Get fee details
    fee_details = []
    for fee in fees:
        fee_payments = [p for p in payments if p.student_fee_id == fee.id]
        paid_amount = sum(p.amount for p in fee_payments)
        balance = fee.amount - fee.discount_amount - paid_amount
        
        fee_details.append({
            "fee_id": fee.id,
            "fee_type_name": fee.fee_type.name,
            "amount": fee.amount,
            "discount": fee.discount_amount,
            "paid": paid_amount,
            "balance": balance,
            "status": fee.status,
            "due_date": fee.due_date
        })
    
    return FeeSummary(
        student_id=student_id,
        total_fees=total_fees,
        total_paid=total_paid,
        total_outstanding=total_outstanding,
        total_discount=total_discount,
        fee_details=fee_details
    )

# Payment endpoints
@router.post("/payments", response_model=PaymentSchema)
async def create_payment(
    payment: PaymentCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create a payment record"""
    require_permission("payments:create")(current_user)
    
    # Verify student fee exists
    student_fee = db.query(StudentFee).filter(
        StudentFee.id == payment.student_fee_id,
        StudentFee.school_id == school_id
    ).first()
    
    if not student_fee:
        raise NotFoundException("Student fee not found")
    
    # Generate receipt number
    from datetime import datetime
    receipt_number = f"RCP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{payment.student_fee_id}"
    
    db_payment = Payment(
        student_fee_id=payment.student_fee_id,
        amount=payment.amount,
        payment_date=payment.payment_date,
        payment_method=payment.payment_method,
        reference_number=payment.reference_number,
        notes=payment.notes,
        recorded_by=current_user.id,
        receipt_number=receipt_number,
        school_id=school_id
    )
    
    db.add(db_payment)
    
    # Update fee status if fully paid
    total_payments = db.query(Payment).filter(
        Payment.student_fee_id == payment.student_fee_id,
        Payment.status == "completed"
    ).all()
    
    total_paid = sum(p.amount for p in total_payments) + payment.amount
    balance = student_fee.amount - student_fee.discount_amount - total_paid
    
    if balance <= 0:
        student_fee.status = "paid"
    elif total_paid > 0:
        student_fee.status = "partial"
    
    db.commit()
    db.refresh(db_payment)
    
    return db_payment

@router.get("/payments", response_model=List[PaymentSchema])
async def get_payments(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = Query(None),
    payment_method: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get payments"""
    require_permission("payments:view")(current_user)
    
    query = db.query(Payment).filter(Payment.school_id == school_id)
    
    if student_id:
        query = query.join(StudentFee).filter(StudentFee.student_id == student_id)
    
    if payment_method:
        query = query.filter(Payment.payment_method == payment_method)
    
    payments = query.offset(skip).limit(limit).all()
    return payments

# Paystack integration endpoints
@router.post("/payments/paystack/initialize")
async def initialize_paystack_payment(
    payment_init: PaystackPaymentInit,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Initialize Paystack payment"""
    # Verify student fee exists
    student_fee = db.query(StudentFee).filter(
        StudentFee.id == payment_init.student_fee_id,
        StudentFee.school_id == school_id
    ).first()
    
    if not student_fee:
        raise NotFoundException("Student fee not found")
    
    # Check permissions
    if not _can_access_student_fee(current_user, student_fee, db):
        require_permission("payments:create")(current_user)
    
    # Calculate outstanding amount
    total_payments = db.query(Payment).filter(
        Payment.student_fee_id == payment_init.student_fee_id,
        Payment.status == "completed"
    ).all()
    
    total_paid = sum(p.amount for p in total_payments)
    outstanding = student_fee.amount - student_fee.discount_amount - total_paid
    
    if outstanding <= 0:
        raise ValidationException("Fee is already fully paid")
    
    # Get school's Paystack subaccount ID
    school = db.query(School).filter(School.id == school_id).first()
    if not school or not school.paystack_subaccount_id:
        raise ValidationException("School Paystack subaccount not configured.")

    # Get platform fee from global settings
    platform_fee_setting = db.query(GlobalSetting).filter(GlobalSetting.key == "platform_fee").first()
    platform_fee = float(platform_fee_setting.value) if platform_fee_setting else 0.0 # Default to 0 if not set

    # Calculate total amount including platform fee
    total_amount_kobo = int((outstanding + platform_fee) * 100)

    # Initialize payment with Paystack
    paystack = PaystackService()
    result = await paystack.initialize_payment(
        email=payment_init.email,
        amount=total_amount_kobo,  # Convert to kobo
        reference=f"fee-{student_fee.id}-{int(datetime.now().timestamp())}",
        callback_url=payment_init.callback_url,
        subaccount=school.paystack_subaccount_id,
        transaction_charge=int(platform_fee * 100) # Platform fee in kobo
    )
    
    return result

@router.post("/payments/paystack/verify")
async def verify_paystack_payment(
    payment_verify: PaystackPaymentVerify,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Verify Paystack payment"""
    # Verify payment with Paystack
    paystack = PaystackService()
    result = await paystack.verify_payment(payment_verify.reference)
    
    if result["status"] == "success" and result["data"]["status"] == "success":
        # Extract fee ID from reference
        reference_parts = payment_verify.reference.split("-")
        if len(reference_parts) >= 2 and reference_parts[0] == "fee":
            fee_id = int(reference_parts[1])
            
            # Verify student fee exists
            student_fee = db.query(StudentFee).filter(
                StudentFee.id == fee_id,
                StudentFee.school_id == school_id
            ).first()
            
            if student_fee:
                # Check if payment already recorded
                existing_payment = db.query(Payment).filter(
                    Payment.paystack_reference == payment_verify.reference
                ).first()
                
                if not existing_payment:
                    # Create payment record
                    amount = result["data"]["amount"] / 100  # Convert from kobo
                    
                    # Get platform fee from global settings
                    platform_fee_setting = db.query(GlobalSetting).filter(GlobalSetting.key == "platform_fee").first()
                    platform_fee = float(platform_fee_setting.value) if platform_fee_setting else 0.0 # Default to 0 if not set

                    # Calculate amounts
                    total_amount_paid = result["data"]["amount"] / 100  # Total amount paid by customer
                    paystack_transaction_fees = result["data"]["fees"] / 100 if "fees" in result["data"] else 0.0
                    
                    # The amount that went to the school is total_amount_paid - platform_fee - paystack_transaction_fees
                    school_net_amount = total_amount_paid - platform_fee - paystack_transaction_fees

                    db_payment = Payment(
                        student_fee_id=fee_id,
                        amount=total_amount_paid, # Total amount paid by the parent
                        payment_date=date.today(),
                        payment_method="online",
                        paystack_reference=payment_verify.reference,
                        status="completed",
                        recorded_by=current_user.id,
                        receipt_number=f"RCP-{payment_verify.reference}",
                        gateway_response=result["data"],
                        platform_fee_amount=platform_fee,
                        school_net_amount=school_net_amount,
                        school_id=school_id
                    )
                    
                    db.add(db_payment)
                    
                    # Update fee status
                    total_payments = db.query(Payment).filter(
                        Payment.student_fee_id == fee_id,
                        Payment.status == "completed"
                    ).all()
                    
                    total_paid = sum(p.amount for p in total_payments) + amount
                    balance = student_fee.amount - student_fee.discount_amount - total_paid
                    
                    if balance <= 0:
                        student_fee.status = "paid"
                    else:
                        student_fee.status = "partial"
                    
                    db.commit()
                    db.refresh(db_payment)
                    
                    return {"message": "Payment verified and recorded successfully", "payment": db_payment}
    
    return {"message": "Payment verification failed or already processed"}

def _can_access_student_fee(current_user: User, student_fee: StudentFee, db: Session) -> bool:
    """Check if current user can access student fee data"""
    # Get the student
    student = db.query(Student).filter(Student.id == student_fee.student_id).first()
    if not student:
        return False
    
    # If user is the student themselves
    if current_user.id == student.user_id:
        return True
    
    # If user is a parent of the student
    from models.student import StudentParent
    parent_link = db.query(StudentParent).filter(
        StudentParent.student_id == student.id,
        StudentParent.parent_user_id == current_user.id
    ).first()
    
    return parent_link is not None

def _can_access_student_data(current_user: User, student: Student, db: Session) -> bool:
    """Check if current user can access student data"""
    # If user is the student themselves
    if current_user.id == student.user_id:
        return True
    
    # If user is a parent of the student
    from models.student import StudentParent
    parent_link = db.query(StudentParent).filter(
        StudentParent.student_id == student.id,
        StudentParent.parent_user_id == current_user.id
    ).first()
    
    return parent_link is not None
