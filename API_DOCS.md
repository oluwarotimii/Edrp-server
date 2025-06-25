# EDRP Backend API - Integration Guideline

This document provides a comprehensive guide for integrating with the Education ERP backend API. It covers authentication, available endpoints, and data validation rules, including all recent schema-hardening updates.

**Base URL for Local Development:** `http://127.0.0.1:8000`

## Table of Contents
- [Authentication](#authentication)
- [Data Validation and Enums](#data-validation-and-enums)
- [API Endpoints](#api-endpoints)
  - [Schools](#schools)
  - [Users](#users)
  - [Roles & Permissions](#roles--permissions)
  - [Super Admin](#super-admin)
- [Super Admin Setup](#super-admin-setup)
- [Environment Variables](#environment-variables)
- [Running Tests](#running-tests)

---

## Authentication

### Login

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin@test.school.com", "password": "SecurePass123"}'
```

### Refresh Token

```bash
curl -X POST http://127.0.0.1:8000/api/auth/refresh \
  -H "Authorization: Bearer <refresh_token>"
```

---

## Data Validation and Enums

To ensure data integrity and consistency, the API uses strict `Enum` types for many fields. The API performs **case-insensitive validation** and automatically normalizes input to the correct format (e.g., Title Case or lowercase). For example, sending `"gender": "male"` is valid and will be stored as `"Male"`.

Below is a comprehensive list of all `Enum` fields and their accepted values.

| Schema File | Field | Enum Type | Accepted Values (Case-Insensitive) |
|---|---|---|---|
| `schemas/school.py` | `school_type` | `SchoolTypeEnum` | `"Day"`, `"Boarding"` |
| `schemas/user.py` | `gender` | `GenderEnum` | `"Male"`, `"Female"`, `"Other"` |
| `schemas/admission.py` | `status` | `ApplicationStatusEnum` | `"Submitted"`, `"Reviewing"`, `"Approved"`, `"Rejected"`, `"Waitlisted"` |
| `schemas/assessment.py`| `grade` | (Validator) | Any string, normalized to **UPPERCASE**. |
| `schemas/attendance.py`| `status` | `AttendanceStatusEnum` | `"Present"`, `"Absent"`, `"Late"`, `"Excused"` |
| `schemas/attendance.py`| `period` | `AttendancePeriodEnum` | `"daily"`, `"weekly"`, `"monthly"`, `"termly"` (lowercase) |
| `schemas/communication.py`| `message_type` | `MessageTypeEnum` | `"Direct"`, `"Broadcast"` |
| `schemas/communication.py`| `priority` | `MessagePriorityEnum` | `"Normal"`, `"High"`, `"Low"` |
| `schemas/communication.py`| `severity` | `BehaviorSeverityEnum`| `"Low"`, `"Medium"`, `"High"`, `"Critical"` |
| `schemas/communication.py`| `status` | `BehaviorStatusEnum` | `"Open"`, `"Investigating"`, `"Resolved"`, `"Closed"` |
| `schemas/fee.py` | `frequency` | `FeeFrequencyEnum` | `"one_time"`, `"termly"`, `"annually"`, `"monthly"` (lowercase) |
| `schemas/fee.py` | `due_date_type`| `FeeDueDateTypeEnum` | `"fixed"`, `"relative"` (lowercase) |
| `schemas/fee.py` | `status` | `StudentFeeStatusEnum`| `"Pending"`, `"Paid"`, `"Partially Paid"`, `"Overdue"` |
| `schemas/fee.py` | `payment_method`| `PaymentMethodEnum` | `"Cash"`, `"Bank Transfer"`, `"Card"`, `"Online"` |
| `schemas/fee.py` | `status` | `PaymentStatusEnum` | `"Completed"`, `"Pending"`, `"Failed"` |
| `schemas/student.py` | `boarding_status`| `BoardingStatusEnum`| `"Day"`, `"Boarding"` |
| `schemas/student.py` | `status` | `StudentStatusEnum` | `"Active"`, `"Inactive"`, `"Graduated"`, `"Withdrawn"` |
| `schemas/student.py` | `relationship_type`| `RelationshipTypeEnum`| `"Father"`, `"Mother"`, `"Guardian"`, `"Other"` |
| `schemas/student.py` | `blood_group` | `BloodGroupEnum` | `"A+"`, `"A-"`, `"B+"`, `"B-"`, `"AB+"`, `"AB-"`, `"O+"`, `"O-"` (uppercase) |

---

## API Endpoints

### Schools

#### Register New School
*Note the `school_type` field must be one of the accepted `Enum` values.* 
```bash
curl -X POST http://127.0.0.1:8000/api/schools \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Innovation Academy",
    "address": "123 Future Way, Tech City",
    "email": "contact@innovationacademy.edu",
    "principal_name": "Dr. Evelyn Reed",
    "school_type": "Day",
    "admin_first_name": "Sam",
    "admin_last_name": "Wilson",
    "admin_email": "admin@innovationacademy.edu",
    "admin_password": "SecurePass123!"
  }'
```

#### Get All Schools (Admin Only)
```bash
curl -X GET http://127.0.0.1:8000/api/schools \
  -H "Authorization: Bearer <access_token>"
```

#### Get School by ID
```bash
curl -X GET http://127.0.0.1:8000/api/schools/1 \
  -H "Authorization: Bearer <access_token>"
```

### Users

#### Get Current User
```bash
curl -X GET http://127.0.0.1:8000/api/users/me \
  -H "Authorization: Bearer <access_token>"
```

#### Get All Users (Admin Only)
```bash
curl -X GET http://127.0.0.1:8000/api/users \
  -H "Authorization: Bearer <access_token>"
```

### Roles & Permissions

#### Get All Roles
```bash
curl -X GET http://127.0.0.1:8000/api/roles \
  -H "Authorization: Bearer <access_token>"
```

#### Get Role by ID
```bash
curl -X GET http://127.0.0.1:8000/api/roles/1 \
  -H "Authorization: Bearer <access_token>"
```

### Super Admin
This section outlines endpoints that are restricted to users with the 'Super Admin' role. These endpoints provide system-wide data and analytics.

#### Get Global Analytics
Provides a global overview of the entire system, including statistics across all schools, such as total users, students, and recent activities.

- **Method**: `GET`
- **Endpoint**: `/api/super-admin/analytics/global`
- **Permissions**: `Super Admin`

**Example Request:**
```bash
curl -X GET http://127.0.0.1:8000/api/super-admin/analytics/global \
  -H "Authorization: Bearer <super_admin_access_token>"
```

**Example Response:**
```json
{
  "total_schools": 15,
  "total_users": 2500,
  "total_students": 1800,
  "total_staff": 700,
  "active_admissions": 120,
  "recent_enrollments": [
    { "student_id": "STU-2024-0123", "name": "Alice Johnson", "school": "Innovation Academy" },
    { "student_id": "STU-2024-0124", "name": "Bob Williams", "school": "Horizon High" }
  ]
}
```

---

## Super Admin Setup

To create a super admin user for system-wide management, follow these steps. This user will have access to all resources across all schools.

1.  **Create the Super Admin Role and Assign Permissions**:
    This SQL script first creates the `Super Admin` role if it does not already exist. It then intelligently assigns all available permissions from the `permissions` table to this role, ensuring the Super Admin has full system access. The `LEFT JOIN` ensures that only permissions not already assigned are added, making the script safe to run multiple times.

    ```sql
    -- Step 1: Insert the 'Super Admin' role if it doesn't exist.
    -- This role is marked as a system role, protecting it from accidental deletion.
    INSERT INTO roles (name, description, is_system_role, created_at, updated_at)
    VALUES ('Super Admin', 'System administrator with full access', true, NOW(), NOW())
    ON CONFLICT (name) DO NOTHING;

    -- Step 2: Assign all existing permissions to the 'Super Admin' role.
    -- This query finds all permissions that are not yet assigned to the Super Admin
    -- and creates the association in the `role_permissions` table.
    INSERT INTO role_permissions (role_id, permission_id, created_at, updated_at)
    SELECT
      (SELECT id FROM roles WHERE name = 'Super Admin') as role_id,
      p.id as permission_id,
      NOW(),
      NOW()
    FROM permissions p
    LEFT JOIN role_permissions rp ON rp.permission_id = p.id AND rp.role_id = (SELECT id FROM roles WHERE name = 'Super Admin')
    WHERE rp.permission_id IS NULL;
    ```

2.  **Create a Super Admin User via API**:

    ```bash
    # First, create a dedicated school for system administration
    curl -X POST http://127.0.0.1:8000/api/schools \
      -H "Content-Type: application/json" \
      -d '{
        "name": "System Administration",
        "address": "1 System Lane",
        "email": "system@edrp.com",
        "principal_name": "Sys Admin",
        "school_type": "Day",
        "admin_first_name": "Super",
        "admin_last_name": "Admin",
        "admin_email": "superadmin@edrp.com",
        "admin_password": "aVerySecurePassword123!"
      }'

    # Then, assign the 'Super Admin' role to this new user in your database
    UPDATE user_roles
    SET role_id = (SELECT id FROM roles WHERE name = 'Super Admin')
    WHERE user_id = (SELECT id FROM users WHERE email = 'superadmin@edrp.com');
    ```

---

## Environment Variables

Ensure the following environment variables are configured (e.g., in a `.env` file for local development):

```
DATABASE_URL="postgresql://user:password@host:port/dbname"
SECRET_KEY="your_super_secret_key_of_at_least_32_chars"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## Running Tests

To test the API endpoints, use the provided `cURL` commands or an API client like Postman.

1.  Ensure the base URL is correct for your environment (`http://127.0.0.1:8000` for local).
2.  Replace `<access_token>` and `<refresh_token>` with valid JWTs obtained from the login endpoint.
3.  Replace path parameters like `/api/schools/:id` with actual resource IDs.
