import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import date, datetime

# Import the FastAPI app instance from your main application file
# Adjust the import path if your main.py is in a different location relative to the tests folder
from main import app
from database import get_db
from models.user import User, Role, Permission
from models.school import School
from models.global_settings import GlobalSetting
from models.fee import StudentFee
from schemas.user import UserResponse
from schemas.school import SchoolCreate
from schemas.fee import PaystackPaymentInit, StudentStatusUpdate

client = TestClient(app)

# --- Fixtures for Mocking Dependencies ---

@pytest.fixture
def mock_db_session():
    """Fixture to mock the database session."""
    mock_session = MagicMock()
    yield mock_session
    mock_session.close()

@pytest.fixture
def mock_super_admin_user():
    """Fixture to create a mock super_admin user."""
    user = User(
        id=1,
        email="superadmin@example.com",
        username="superadmin",
        hashed_password="hashedpassword",
        is_active=True,
        is_approved=True,
        school_id=None # Super admin is not tied to a specific school
    )
    # Mock roles and permissions for the super_admin
    super_admin_role = Role(id=1, name="super_admin")
    super_admin_role.permissions = [
        Permission(name="global_settings:view"),
        Permission(name="global_settings:update"),
        Permission(name="schools:create"),
        Permission(name="students:update_status"),
        Permission(name="payments:create") # Needed for payment initialization
    ]
    user.roles = [super_admin_role]
    return user

@pytest.fixture(autouse=True)
def override_dependencies(mock_db_session, mock_super_admin_user):
    """Override FastAPI dependencies for testing."""
    def _get_db_override():
        yield mock_db_session

    def _get_current_user_override():
        return mock_super_admin_user

    app.dependency_overrides[get_db] = _get_db_override
    # Assuming get_current_user is imported from utils.dependencies
    # You might need to adjust this import path based on your project structure
    with patch('utils.dependencies.get_current_user', new=_get_current_user_override):
        yield
    app.dependency_overrides.clear()

# --- Tests for Global Settings ---

def test_update_global_setting(mock_db_session):
    """Test updating a global setting."""
    mock_setting = GlobalSetting(id=1, key="platform_fee", value="100.0", description="Old description")
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_setting

    response = client.put(
        "/api/super-admin/global-settings/platform_fee",
        headers={"Content-Type": "application/json"},
        json={"value": "150.0", "description": "New description"}
    )

    assert response.status_code == 200
    assert response.json()["value"] == "150.0"
    assert response.json()["description"] == "New description"
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(mock_setting)

def test_get_global_settings(mock_db_session):
    """Test getting all global settings."""
    mock_settings = [
        GlobalSetting(id=1, key="platform_fee", value="150.0"),
        GlobalSetting(id=2, key="another_setting", value="test")
    ]
    mock_db_session.query.return_value.all.return_value = mock_settings

    response = client.get("/api/super-admin/global-settings")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["key"] == "platform_fee"
    assert response.json()[1]["key"] == "another_setting"

# --- Tests for School Creation (with Paystack Subaccount Mocking) ---

@patch('services.paystack.PaystackService.create_subaccount')
def test_create_school_with_paystack_subaccount(mock_create_subaccount, mock_db_session):
    """Test creating a school, including Paystack subaccount creation."""
    # Mock PaystackService.create_subaccount response
    mock_create_subaccount.return_value = {
        "status": True,
        "data": {"subaccount_code": "SUB_testcode123"}
    }

    # Mock database queries for user and school existence checks
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    mock_db_session.query.return_value.filter.return_value.scalar.return_value = False # For subdomain check

    # Mock the User and Role objects that would be created/queried
    mock_admin_role = Role(id=1, name="Admin")
    mock_db_session.query.return_value.filter.return_value.first.side_effect = [
        mock_admin_role, # For admin role lookup
        None, # For existing user check
        None, # For existing school check
        None, # For existing user check again (in register_school)
        None, # For existing school check again (in register_school)
        None, # For school subscription check
        MagicMock(max_students=100) # For school subscription plan
    ]
    
    # Mock the count for student limit check
    mock_db_session.query.return_value.filter.return_value.count.return_value = 0

    school_data = {
        "name": "Test School",
        "email": "test@school.com",
        "admin_first_name": "John",
        "admin_last_name": "Doe",
        "admin_email": "admin@testschool.com",
        "admin_password": "password123",
        "school_type": "Day",
        "bank_name": "Test Bank",
        "account_number": "1234567890"
    }

    response = client.post(
        "/api/schools",
        headers={"Content-Type": "application/json"},
        json=school_data
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Test School"
    assert response.json()["paystack_subaccount_id"] == "SUB_testcode123"
    mock_create_subaccount.assert_called_once_with(
        business_name="Test School",
        settlement_bank="Test Bank",
        account_number="1234567890"
    )
    mock_db_session.commit.assert_called() # Ensure commit is called

# --- Tests for Fee Payment Initialization (with Paystack Mocking) ---

@patch('services.paystack.PaystackService.initialize_payment')
def test_initialize_paystack_payment(mock_initialize_payment, mock_db_session):
    """Test initializing a Paystack payment with split settlement."""
    # Mock PaystackService.initialize_payment response
    mock_initialize_payment.return_value = {
        "status": True,
        "data": {
            "authorization_url": "https://paystack.com/pay/test",
            "reference": "fee-1-1234567890"
        }
    }

    # Mock database queries for student fee, school, and global setting
    mock_student_fee = MagicMock(spec=StudentFee)
    mock_student_fee.id = 1
    mock_student_fee.amount = 1000.0
    mock_student_fee.discount_amount = 0.0
    mock_student_fee.status = "pending"

    mock_school = MagicMock(spec=School)
    mock_school.id = 1
    mock_school.paystack_subaccount_id = "SUB_school123"

    mock_platform_fee_setting = MagicMock(spec=GlobalSetting)
    mock_platform_fee_setting.value = "150.0" # Platform fee of 150 NGN

    # Configure side_effect for sequential calls to first()
    mock_db_session.query.return_value.filter.return_value.first.side_effect = [
        mock_student_fee, # For student_fee lookup
        mock_school,      # For school lookup
        mock_platform_fee_setting # For platform_fee setting lookup
    ]
    # Mock total payments for outstanding calculation
    mock_db_session.query.return_value.filter.return_value.all.return_value = [] # No prior payments

    payment_init_data = PaystackPaymentInit(
        student_fee_id=1,
        email="parent@example.com",
        callback_url="http://localhost:3000/payment-success"
    )

    response = client.post(
        "/api/fees/payments/paystack/initialize",
        headers={"Content-Type": "application/json"},
        json=payment_init_data.model_dump()
    )

    assert response.status_code == 200
    assert response.json()["status"] is True
    assert response.json()["data"]["authorization_url"] == "https://paystack.com/pay/test"
    
    # Expected amount: (student_fee.amount - discount) + platform_fee = 1000 + 150 = 1150 NGN = 115000 kobo
    mock_initialize_payment.assert_called_once_with(
        email="parent@example.com",
        amount=115000, # 1150 NGN in kobo
        reference=f"fee-{mock_student_fee.id}-{int(datetime.now().timestamp())}", # Reference will vary by timestamp
        callback_url="http://localhost:3000/payment-success",
        subaccount="SUB_school123",
        transaction_charge=15000 # 150 NGN in kobo
    )

# --- Tests for Student Status Update ---

def test_update_student_status_graduated(mock_db_session):
    """Test updating student status to 'Graduated'."""
    mock_student = MagicMock(spec=StudentFee) # Using StudentFee as a mock for Student for simplicity
    mock_student.id = 1
    mock_student.status = "active"
    mock_student.graduation_date = None
    mock_student.withdrawal_date = None
    mock_student.withdrawal_reason = None

    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_student

    status_update_data = StudentStatusUpdate(
        status="Graduated",
        effective_date=date(2025, 7, 1),
        notes="Completed program"
    )

    response = client.put(
        "/api/students/1/status",
        headers={"Content-Type": "application/json"},
        json=status_update_data.model_dump()
    )

    assert response.status_code == 200
    assert mock_student.status == "Graduated"
    assert mock_student.graduation_date == date(2025, 7, 1)
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(mock_student)

def test_update_student_status_withdrawn(mock_db_session):
    """Test updating student status to 'Withdrawn'."""
    mock_student = MagicMock(spec=StudentFee) # Using StudentFee as a mock for Student for simplicity
    mock_student.id = 2
    mock_student.status = "active"
    mock_student.graduation_date = None
    mock_student.withdrawal_date = None
    mock_student.withdrawal_reason = None

    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_student

    status_update_data = StudentStatusUpdate(
        status="Withdrawn",
        effective_date=date(2025, 6, 15),
        notes="Moved to another city"
    )

    response = client.put(
        "/api/students/2/status",
        headers={"Content-Type": "application/json"},
        json=status_update_data.model_dump()
    )

    assert response.status_code == 200
    assert mock_student.status == "Withdrawn"
    assert mock_student.withdrawal_date == date(2025, 6, 15)
    assert mock_student.withdrawal_reason == "Moved to another city"
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(mock_student)

def test_update_student_status_not_found(mock_db_session):
    """Test updating status for a non-existent student."""
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    status_update_data = StudentStatusUpdate(
        status="Suspended",
        effective_date=date(2025, 1, 1)
    )

    response = client.put(
        "/api/students/999/status",
        headers={"Content-Type": "application/json"},
        json=status_update_data.model_dump()
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"
    mock_db_session.commit.assert_not_called()
