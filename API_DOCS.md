# EDRP Backend API - Integration Guideline

This document provides a comprehensive guide for integrating with the Education ERP backend API. It covers authentication, available endpoints, and data validation rules, including all recent schema-hardening updates.

**Base URL for Local Development:** `http://127.0.0.1:8000`
**Production Base URL:** `https://api.yourdomain.com`

## Table of Contents
- [Authentication](#authentication)
- [Subdomain Management](#subdomain-management)
- [Email Template System](#email-template-system)
- [Subscription System](#subscription-system)
- [Data Validation and Enums](#data-validation-and-enums)
- [API Endpoints](#api-endpoints)
  - [Schools](#schools)
  - [Subdomains](#subdomains)
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

## Subdomain Management

The Education ERP system supports multi-tenancy through a sophisticated subdomain system. Each school gets a unique subdomain that serves as their dedicated access point.

### Subdomain Structure
- Format: `{subdomain}.{root_domain}` (e.g., `yourschool.edrp.app`)
- Root domain is configurable via `ROOT_DOMAIN` environment variable
- Default root domain for local development: `localhost`

### Subdomain Requirements
- Must be 3-63 characters long
- Can only contain lowercase letters, numbers, and hyphens
- Cannot start or end with a hyphen
- Must be unique across all schools
- Cannot be a reserved subdomain (e.g., www, api, admin)
- Must be URL-safe and DNS-compliant

### Subdomain API Endpoints

#### Check Subdomain Availability
```bash
GET /api/subdomains/check-availability?subdomain=myschool
```

**Response:**
```json
{
  "available": true,
  "suggestions": ["myschool1", "myschool2"],
  "message": "Subdomain is available"
}
```

#### Generate Subdomain Suggestions
```bash
GET /api/subdomains/suggest?name=My%20School&length=3
```

**Response:**
```json
{
  "suggestions": ["myschool", "my-school", "myschool1"],
  "base_name": "myschool"
}
```

#### Register New School with Subdomain
```bash
POST /api/schools/register
Content-Type: application/json

{
  "name": "My School",
  "subdomain": "myschool",
  "email": "admin@myschool.edu",
  "phone": "+1234567890",
  "address": "123 School St, City, Country",
  "admin_email": "admin@myschool.edu",
  "admin_password": "securepassword123"
}
```

**Response:**
```json
{
  "id": 1,
  "name": "My School",
  "subdomain": "myschool",
  "email": "admin@myschool.edu",
  "status": "active",
  "created_at": "2023-01-01T12:00:00Z"
}
```

#### Update School Subdomain (Admin Only)
```bash
PATCH /api/schools/{school_id}/subdomain
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "subdomain": "newschoolname"
}
```

### Custom Domain Support
Schools can use their own domain by configuring a CNAME record:

1. School admin adds custom domain in their settings
2. System provides DNS verification token
3. School adds CNAME record for their domain pointing to the root domain
4. System verifies DNS configuration
5. Once verified, the custom domain is activated

### Subdomain Middleware
- All API requests include the subdomain in the `X-Subdomain` header
- The system validates the subdomain on each request
- Invalid or non-existent subdomains return a 404 response
- Subdomain information is available in the request state for route handlers

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ROOT_DOMAIN` | Root domain for subdomains | Yes | `localhost` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | Yes | `*` |
| `ENABLE_SUBDOMAINS` | Enable subdomain routing | No | `true` |
| `DEFAULT_SCHEME` | Default URL scheme | No | `https` |

## Email Template System

The Email Template System provides a flexible way to manage and send dynamic, templated emails throughout the Education ERP platform. This system supports both system-generated emails (like notifications) and custom emails, with full HTML support and variable substitution.

### Key Features

- **Dynamic Templates**: Create templates with variables that get replaced at send time
- **HTML Support**: Rich email formatting with full HTML support
- **Template Management**: CRUD operations for email templates
- **Email Tracking**: Log all sent emails with delivery status
- **Preview & Testing**: Preview templates and send test emails
- **Background Processing**: Non-blocking email sending
- **Multi-tenant Support**: Templates can be scoped to specific schools or global

### Template Variables

Templates can include variables in double curly braces, like `{{variable_name}}`. All variables used in the template must be defined in the `variables` object when creating or updating a template.

### Template Types

| Type | Description |
|------|-------------|
| `trial_started` | Sent when a new trial starts |
| `trial_ending_soon` | Sent when a trial is about to end |
| `subscription_confirmation` | Sent after successful subscription |
| `payment_failed` | Sent when a payment fails |
| `payment_received` | Sent when a payment is received |
| `subscription_cancelled` | Sent when a subscription is cancelled |
| `password_reset` | For password reset emails |
| `welcome_email` | Welcome email for new users |
| `custom` | For custom email templates |

### API Endpoints

#### List All Templates
```http
GET /api/admin/email-templates/
```

**Query Parameters:**
- `type`: Filter by template type
- `is_active`: Filter by active status (true/false)
- `search`: Search in name or subject
- `skip`: Pagination offset
- `limit`: Items per page (default: 10, max: 100)

**Response:**
```json
{
  "items": [
    {
      "id": "tpl_welcome",
      "name": "Welcome Email",
      "subject": "Welcome to {{school_name}}",
      "template_type": "welcome_email",
      "is_active": true,
      "created_at": "2024-06-25T12:00:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 10
}
```

#### Create New Template
```http
POST /api/admin/email-templates/
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "New Student Welcome",
  "subject": "Welcome to {{school_name}}, {{student_name}}!",
  "body": "<p>Hello {{student_name}},</p><p>Welcome to {{school_name}}!</p>",
  "template_type": "custom",
  "variables": {
    "student_name": "Name of the student",
    "school_name": "Name of the school"
  },
  "is_active": true
}
```

**Required Fields:**
- `name`: Template name (unique)
- `subject`: Email subject (can include variables)
- `body`: Email body (HTML supported)
- `template_type`: One of the template types listed above

#### Get Template by ID
```http
GET /api/admin/email-templates/{template_id}
```

#### Update Template
```http
PUT /api/admin/email-templates/{template_id}
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "Updated Template Name",
  "subject": "Updated subject",
  "body": "<p>Updated content</p>",
  "is_active": true
}
```

#### Delete Template (Soft Delete)
```http
DELETE /api/admin/email-templates/{template_id}
Authorization: Bearer <token>
```

#### Preview Template
```http
POST /api/admin/email-templates/preview
Content-Type: application/json
Authorization: Bearer <token>

{
  "template_id": "tpl_welcome",
  "variables": {
    "user_name": "John Doe",
    "school_name": "Example School"
  }
}
```

#### Send Test Email
```http
POST /api/admin/email-templates/test
Content-Type: application/json
Authorization: Bearer <token>

{
  "template_id": "tpl_welcome",
  "recipient_email": "test@example.com",
  "variables": {
    "user_name": "Test User",
    "school_name": "Test School"
  }
}
```

#### Send Custom Email
```http
POST /api/admin/email-templates/send-custom
Content-Type: application/json
Authorization: Bearer <token>

{
  "recipient_email": "user@example.com",
  "subject": "Custom Email Subject",
  "body": "<p>Hello {{name}},</p><p>This is a custom email.</p>",
  "variables": {
    "name": "Recipient Name"
  }
}
```

#### View Sent Emails
```http
GET /api/admin/email-templates/sent-emails/
```

**Query Parameters:**
- `status`: Filter by status (sent/delivered/failed)
- `template_id`: Filter by template ID
- `recipient_email`: Filter by recipient email
- `start_date`: Filter by sent date (ISO format)
- `end_date`: Filter by sent date (ISO format)
- `skip`: Pagination offset
- `limit`: Items per page (default: 10, max: 100)

### Integration Guidelines

1. **Creating Templates**
   - Define all variables used in the template in the `variables` object
   - Use the `preview` endpoint to test templates before sending
   - Set appropriate `template_type` for better organization

2. **Sending Emails**
   - Use the `test` endpoint to verify email delivery
   - For system-generated emails, use background tasks to avoid blocking
   - Handle email sending errors gracefully

3. **Best Practices**
   - Keep templates DRY (Don't Repeat Yourself)
   - Use responsive HTML for email clients
   - Include a plain-text version for better deliverability
   - Test templates with different email clients

4. **Error Handling**
   - Check for 4xx/5xx status codes
   - Log email sending failures
   - Implement retry logic for transient failures

## Subscription System

The Subscription System manages school subscriptions, billing cycles, and payment processing. It integrates with Paystack for payment processing and supports trial periods, multiple billing cycles, and automated email notifications.

### Key Features

- **Multiple Subscription Plans**: Create and manage different subscription tiers
- **Trial Periods**: Support for free trials with configurable durations
- **Flexible Billing**: Monthly and annual billing cycles
- **Payment Processing**: Secure payment processing via Paystack
- **Automatic Invoicing**: Generate and send invoices automatically
- **Email Notifications**: Automatic emails for trial periods, renewals, and payment failures
- **Usage Tracking**: Monitor feature usage against subscription limits
- **Upgrade/Downgrade**: Seamless plan changes with prorated billing

### Subscription Lifecycle

1. **Trial Period** (if applicable)
   - School signs up and starts a trial
   - System sends welcome email with trial details
   - Reminder emails sent before trial ends

2. **Subscription Activation**
   - School selects a plan and provides payment method
   - Initial payment processed
   - Subscription activated
   - Welcome email with subscription details sent

3. **Active Subscription**
   - Regular billing according to plan
   - Usage tracking and enforcement of limits
   - Notifications for upcoming renewals

4. **Renewal**
   - Automatic payment processing
   - Invoice generated and sent
   - Confirmation email with receipt

5. **Payment Failure**
   - Payment retry mechanism
   - Dunning emails for failed payments
   - Grace period before suspension

6. **Cancellation**
   - Immediate or end-of-billing period
   - Confirmation email
   - Data retention according to policy

### API Endpoints

#### Subscription Plans

##### List All Plans
```http
GET /api/subscriptions/plans
```

**Query Parameters:**
- `is_active`: Filter by active status (true/false)
- `billing_cycle`: Filter by billing cycle (monthly/yearly)

**Response:**
```json
{
  "items": [
    {
      "id": "plan_basic",
      "name": "Basic Plan",
      "description": "For small schools with basic needs",
      "price": 2999,
      "billing_cycle": "monthly",
      "features": ["100 Students", "10 Staff", "Basic Support"],
      "is_active": true,
      "trial_days": 14,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

##### Create Plan (Admin Only)
```http
POST /api/subscriptions/plans
Content-Type: application/json
Authorization: Bearer <admin_token>

{
  "name": "Pro Plan",
  "description": "For growing schools with advanced needs",
  "price": 5999,
  "billing_cycle": "monthly",
  "features": ["500 Students", "50 Staff", "Priority Support"],
  "is_active": true,
  "trial_days": 7,
  "metadata": {"max_students": 500, "max_staff": 50}
}
```

#### School Subscriptions

##### Get Current Subscription
```http
GET /api/subscriptions/current
```

**Response:**
```json
{
  "id": "sub_123",
  "plan_id": "plan_basic",
  "school_id": "school_123",
  "status": "active",
  "current_period_start": "2024-06-01T00:00:00Z",
  "current_period_end": "2024-07-01T00:00:00Z",
  "trial_start": "2024-05-15T00:00:00Z",
  "trial_end": "2024-05-29T00:00:00Z",
  "cancel_at_period_end": false,
  "canceled_at": null,
  "ended_at": null,
  "created_at": "2024-05-15T00:00:00Z"
}
```

##### Subscribe to Plan
```http
POST /api/subscriptions/subscribe
Content-Type: application/json
Authorization: Bearer <token>

{
  "plan_id": "plan_basic",
  "payment_method": {
    "type": "card",
    "card": {
      "number": "4111111111111111",
      "exp_month": 12,
      "exp_year": 2025,
      "cvc": "123"
    }
  },
  "billing_details": {
    "email": "billing@school.edu",
    "name": "School Name"
  }
}
```

##### Update Subscription
```http
POST /api/subscriptions/update
Content-Type: application/json
Authorization: Bearer <token>

{
  "plan_id": "plan_pro",
  "prorate": true
}
```

##### Cancel Subscription
```http
POST /api/subscriptions/cancel
Content-Type: application/json
Authorization: Bearer <token>

{
  "cancel_at_period_end": true
}
```

#### Invoices

##### List Invoices
```http
GET /api/subscriptions/invoices
```

**Query Parameters:**
- `status`: Filter by status (paid/unpaid/void)
- `start_date`: Filter by issue date
- `end_date`: Filter by issue date

##### Get Invoice PDF
```http
GET /api/subscriptions/invoices/{invoice_id}/pdf
```

### Webhooks

#### Paystack Webhook
```http
POST /api/webhooks/paystack
X-Paystack-Signature: <signature>

{
  "event": "charge.success",
  "data": {
    "reference": "7c7rpkqpc0tijs8",
    "amount": 10000,
    "metadata": {
      "subscription_id": "sub_123"
    }
  }
}
```

### Integration Guidelines

#### 1. Subscription Flow

1. **Trial Signup**
   - Create school account with trial
   - Show available plans
   - Track trial expiration

2. **Subscription**
   - Collect payment method
   - Process initial payment
   - Activate features

3. **Ongoing Management**
   - Show current usage
   - Allow plan changes
   - Handle payment failures

#### 2. Webhook Implementation

1. **Set Up Webhook Endpoint**
   - Secure with signature verification
   - Handle events asynchronously
   - Implement idempotency

2. **Handle Events**
   - `subscription.created`
   - `subscription.updated`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`

#### 3. Error Handling

- **Payment Failures**
  - Retry logic
  - Grace periods
  - Dunning emails

- **API Errors**
  - Rate limiting
  - Validation errors
  - Authentication issues

#### 4. Testing

1. **Test Cards**
   - Success: 4084084084084081
   - 3D Secure: 5060666666666666666
   - Insufficient Funds: 4084080000005405

2. **Webhook Testing**
   - Use test webhook endpoint
   - Verify signature validation
   - Test all event types

### Best Practices

1. **Security**
   - Use HTTPS for all requests
   - Validate webhook signatures
   - Never expose API keys in client-side code

2. **UX**
   - Clear pricing
   - Easy upgrade/downgrade
   - Transparent billing

3. **Monitoring**
   - Track subscription metrics
   - Monitor payment failures
   - Set up alerts for critical events

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `PAYSTACK_SECRET_KEY` | Paystack secret key | Yes | - |
| `PAYSTACK_PUBLIC_KEY` | Paystack public key | Yes | - |
| `PAYSTACK_WEBHOOK_SECRET` | Webhook signing secret | Yes | - |
| `DEFAULT_TRIAL_DAYS` | Default trial period | No | 14 |
| `GRACE_PERIOD_DAYS` | Grace period for failed payments | No | 7 |
| `INVOICE_PREFIX` | Prefix for invoice numbers | No | INV- |

### Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| 402 | Payment Required | Update payment method |
| 403 | Forbidden | Check permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resolve conflict |
| 422 | Validation Error | Check request body |
| 429 | Too Many Requests | Rate limiting |
| 500 | Server Error | Contact support |

### Error Responses

#### 400 Bad Request
```json
{
  "detail": "Invalid subdomain format. Must be 3-63 characters, lowercase alphanumeric with hyphens"
}
```

#### 403 Forbidden
```json
{
  "detail": "Subdomain is reserved and cannot be used"
}
```

#### 404 Not Found
```json
{
  "detail": "Subdomain not found"
}
```

#### 409 Conflict
```json
{
  "detail": "Subdomain is already taken"
}
```

#### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "subdomain"],
      "msg": "Subdomain contains invalid characters",
      "type": "value_error"
    }
  ]
}
```

### Security Considerations

1. **Cookie Security**
   - Cookies are scoped to the root domain to enable SSO across subdomains
   - Set `Secure`, `HttpOnly`, and `SameSite=Lax` flags on all cookies
   - Consider `__Host-` prefix for additional security

2. **CORS Configuration**
   - Configure CORS to allow requests from all subdomains
   - Example: `Access-Control-Allow-Origin: *.yourdomain.com`
   - Use `Vary: Origin` header to prevent cache poisoning

3. **Rate Limiting**
   - Implement rate limiting per subdomain to prevent abuse
   - Consider stricter limits for subdomain registration endpoints

4. **Subdomain Takeover Protection**
   - Validate DNS records before allowing custom domain association
   - Implement periodic verification of DNS configurations

5. **Session Management**
   - Ensure sessions are properly isolated between subdomains
   - Implement session timeouts and rotation

6. **Logging and Monitoring**
   - Log all subdomain-related actions for audit purposes
   - Monitor for unusual patterns in subdomain creation/usage

7. **Data Isolation**
   - Ensure database queries always include the subdomain filter
   - Use row-level security where possible

### Deployment Considerations

1. **Wildcard SSL Certificate**
   - Required to support dynamic subdomains
   - Can be obtained from Let's Encrypt or other CAs
   - Example: `*.yourdomain.com`

2. **DNS Configuration**
   - Add a wildcard DNS A record: `*.yourdomain.com` → your server IP
   - For Railway deployment, use their provided domain or configure a custom domain

3. **Railway Configuration**
   ```bash
   # Set environment variables in Railway
   railway variables set ROOT_DOMAIN=yourdomain.com
   railway variables set ALLOWED_HOSTS=yourdomain.com,*.yourdomain.com
   railway variables set ENABLE_SUBDOMAINS=true
   ```

4. **Load Balancer/Reverse Proxy**
   - Configure to pass through the `Host` header
   - Example Nginx configuration:
     ```nginx
     server {
         listen 80;
         server_name ~^(?<subdomain>.+)\.yourdomain\.com$;
         
         location / {
             proxy_pass http://localhost:8000;
             proxy_set_header Host $host;
             proxy_set_header X-Real-IP $remote_addr;
             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
             proxy_set_header X-Forwarded-Proto $scheme;
             proxy_set_header X-Subdomain $subdomain;
         }
     }
     ```

5. **Health Checks**
   - Implement health check endpoints for monitoring
   - Example: `GET /health` should return 200 OK

6. **Backup Strategy**
   - Regular database backups including the schools table
   - Test restoration process periodically

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

### Teachers

Endpoints for managing teacher profiles, assignments, and status.

#### Create Teacher
*   **Endpoint:** `POST /teachers`
*   **Permission:** `teachers:create`
*   **Description:** Creates a new teacher record and links it to an existing user.
*   **Body:** `TeacherCreate` schema.
*   **cURL Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/teachers" \
    -H "Authorization: Bearer <your_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "user_id": 123,
          "employee_id": "T-101",
          "department_id": 1,
          "hire_date": "2023-09-01",
          "teaching_qualification": "M.Ed",
          "specialization": "Physics",
          "years_experience": 10,
          "contract_type": "Full-Time"
        }'
    ```

#### Get Teachers
*   **Endpoint:** `GET /teachers`
*   **Permission:** `teachers:view`
*   **Description:** Retrieves a list of all teachers within the user's school. Supports filtering by department and status.
*   **cURL Example:**
    ```bash
    curl -X GET "http://localhost:8000/api/teachers?department_id=1&status=Active" \
    -H "Authorization: Bearer <your_token>"
    ```

#### Get Teacher by ID
*   **Endpoint:** `GET /teachers/{teacher_id}`
*   **Permission:** `teachers:view` (Note: Teachers can always view their own profile without this permission).
*   **Description:** Retrieves the profile of a specific teacher.
*   **cURL Example:**
    ```bash
    curl -X GET "http://localhost:8000/api/teachers/1" \
    -H "Authorization: Bearer <your_token>"
    ```

#### Update Teacher
*   **Endpoint:** `PUT /teachers/{teacher_id}`
*   **Permission:** `teachers:update`
*   **Description:** Updates a teacher's profile information.
*   **Body:** `TeacherUpdate` schema.
*   **cURL Example:**
    ```bash
    curl -X PUT "http://localhost:8000/api/teachers/1" \
    -H "Authorization: Bearer <your_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "specialization": "Quantum Physics",
          "salary_grade": "Grade 5"
        }'
    ```

#### Update Teacher Status
*   **Endpoint:** `PUT /teachers/{teacher_id}/status`
*   **Permission:** `teachers:update_status`
*   **Description:** Updates the employment status of a teacher (e.g., "Active", "On Leave").
*   **Body:** `TeacherStatusUpdate` schema.
*   **cURL Example:**
    ```bash
    curl -X PUT "http://localhost:8000/api/teachers/1/status" \
    -H "Authorization: Bearer <your_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "status": "On Leave"
        }'
    ```

#### Assign Teacher to Class/Subject
*   **Endpoint:** `POST /teachers/assignments`
*   **Permission:** `teachers:assign`
*   **Description:** Assigns a teacher to a specific subject and class for an academic session.
*   **Body:** `TeacherAssignmentCreate` schema.
*   **cURL Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/teachers/assignments" \
    -H "Authorization: Bearer <your_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "teacher_id": 1,
          "subject_id": 10,
          "class_id": 5,
          "academic_session_id": 2
        }'
    ```

#### Get Teacher Assignments
*   **Endpoint:** `GET /teachers/{teacher_id}/assignments`
*   **Permission:** `teachers:view` (Note: Teachers can always view their own assignments).
*   **Description:** Retrieves all class/subject assignments for a specific teacher.
*   **cURL Example:**
    ```bash
    curl -X GET "http://localhost:8000/api/teachers/1/assignments?academic_session_id=2" \
    -H "Authorization: Bearer <your_token>"
    ```

#### Remove Teacher Assignment
*   **Endpoint:** `DELETE /teachers/assignments/{teacher_id}/{subject_id}/{class_id}`
*   **Permission:** `teachers:unassign`
*   **Description:** Removes a single class/subject assignment from a teacher.
*   **cURL Example:**
    ```bash
    curl -X DELETE "http://localhost:8000/api/teachers/assignments/1/10/5?academic_session_id=2" \
    -H "Authorization: Bearer <your_token>"
    ```

#### Remove All Teacher Assignments
*   **Endpoint:** `POST /teachers/{teacher_id}/unassign-all`
*   **Permission:** `teachers:unassign_all`
*   **Description:** Removes all assignments for a teacher, optionally filtered by academic session.
*   **cURL Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/teachers/1/unassign-all?academic_session_id=2" \
    -H "Authorization: Bearer <your_token>"
    ```

### Attendance Management

### Authentic Locations

Authentic Locations are GPS-defined areas where teachers can mark their attendance. This ensures that attendance is only recorded when teachers are physically present at the school premises.

#### Key Concepts
- **Geofencing**: Teachers must be within a defined radius of an authentic location to mark attendance
- **School-Specific**: Each school can define multiple valid locations (e.g., main gate, staff room)
- **Verification**: System verifies the teacher's location before recording attendance

#### Manage Authentic Locations

*   **Endpoint:** `POST /api/authentic-locations`
*   **Permission:** `locations:create`
*   **Description:** Define a new valid location for teacher attendance
*   **Body:** `AuthenticLocationCreate` schema
*   **cURL Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/authentic-locations" \
    -H "Authorization: Bearer <your_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "name": "Main Staff Entrance",
          "description": "Primary entrance for staff attendance",
          "latitude": 6.5244,
          "longitude": 3.3792,
          "radius_meters": 100,
          "is_default": true
        }'
    ```

*   **Endpoint:** `GET /api/authentic-locations`
*   **Permission:** `locations:view`
*   **Description:** List all authentic locations for the current school
*   **cURL Example:**
    ```bash
    curl -X GET "http://localhost:8000/api/authentic-locations" \
    -H "Authorization: Bearer <your_token>"
    ```

#### Verify Location

*   **Endpoint:** `POST /api/attendance/verify-location`
*   **Permission:** `attendance:take`
*   **Description:** Check if current GPS coordinates are within any valid location
*   **Body:** `LocationVerificationRequest`
*   **cURL Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/attendance/verify-location" \
    -H "Authorization: Bearer <your_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "latitude": 6.5245,
          "longitude": 3.3791
        }'
    ```
    **Response:**
    ```json
    {
      "valid": true,
      "location_name": "Main Staff Entrance",
      "distance_meters": 12.5
    }
    ```

### Teacher Attendance

#### Mark Attendance (Clock In/Out)

*   **Endpoint:** `POST /api/teacher-attendance`
*   **Permission:** `attendance:take`
*   **Description:** Record teacher attendance (clock in)
*   **Body:** `TeacherAttendanceCreate` schema
*   **cURL Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/teacher-attendance" \
    -H "Authorization: Bearer <your_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "teacher_id": 45,
          "date": "2025-06-25",
          "status": "Present",
          "clock_in_latitude": 6.5245,
          "clock_in_longitude": 3.3791
        }'
    ```

*   **Endpoint:** `PUT /api/teacher-attendance/{attendance_id}`
*   **Permission:** `attendance:take`
*   **Description:** Update teacher attendance (clock out)
*   **Body:** `TeacherAttendanceUpdate` schema
*   **cURL Example:**
    ```bash
    curl -X PUT "http://localhost:8000/api/teacher-attendance/123" \
    -H "Authorization: Bearer <your_token>" \
    -H "Content-Type: application/json" \
    -d '{
          "clock_out_time": "2025-06-25T16:30:00",
          "clock_out_latitude": 6.5245,
          "clock_out_longitude": 3.3791
        }'
    ```

#### View Attendance Records

*   **Endpoint:** `GET /api/teacher-attendance`
*   **Permission:** `attendance:view`
*   **Description:** Get teacher attendance records (filterable by date range, teacher)
*   **Query Parameters:**
    - `teacher_id` (optional)
    - `start_date` (optional)
    - `end_date` (optional)
*   **cURL Example:**
    ```bash
    curl -X GET "http://localhost:8000/api/teacher-attendance?start_date=2025-06-01&end_date=2025-06-30" \
    -H "Authorization: Bearer <your_token>"
    ```

## Super Admin
This section outlines endpoints that are restricted to users with the 'Super Admin' role. These endpoints provide system-wide data and analytics.

### Grading Profiles (Super Admin Only)

The Super Admin is responsible for creating and managing Grading Profiles, which act as high-level rulebooks for how schools can configure their grading systems.

#### Get All Grading Profiles
```bash
curl -X GET http://127.0.0.1:8000/api/system/grading-profiles 
  -H "Authorization: Bearer <super_admin_access_token>"
```

#### Create Grading Profile
```bash
curl -X POST http://127.0.0.1:8000/api/system/grading-profiles 
  -H "Authorization: Bearer <super_admin_access_token>" 
  -H "Content-Type: application/json" 
  -d '{
    "name": "US GPA System",
    "description": "A standard 4.0 GPA system.",
    "uses_gpa": true,
    "gpa_scale": 4.0,
    "allows_astar_grade": false,
    "remarks_are_mandatory": false
  }'
```

### Assessments

The assessment module is highly flexible, allowing schools to define their own assessment schemes and grading scales, all within the framework of a Grading Profile selected by the school.

#### Assessment Schemes
Schools can create their own assessment schemes to define how final scores are calculated.

#### Grading Scales
Schools can create their own grading scales to map scores to grades. The creation and updating of these scales are validated against the school's chosen Grading Profile.

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

## School Setup Guide

### Setting Up Authentic Locations

1. **Add Authentic Locations**
   - School administrators should define all valid locations where teachers can mark attendance
   - Each location requires:
     - Name (e.g., "Main Gate", "Staff Room")
     - GPS coordinates (latitude/longitude)
     - Radius in meters (e.g., 100 meters)
     - Optional: Set as default location

2. **Mobile App Integration**
   - The mobile app will automatically detect when teachers are within a valid location
   - Teachers must enable location services for the app
   - The app will show which location is being used for verification

3. **Troubleshooting**
   - If a teacher can't mark attendance:
     1. Verify they have the `attendance:take` permission
     2. Check if their device's location services are enabled
     3. Ensure they are within the defined radius of an authentic location
     4. Verify the school has at least one active authentic location

## Super Admin Setup

The Super Admin role is a system-level role with unrestricted access to all data across all schools. This role is intended for system maintenance and global analytics.

**Role Creation and Permissions (Automated)**

The `Super Admin` role is now created and granted all permissions **automatically** when you run your database migrations (`alembic upgrade head`). The system is designed to ensure that upon initial setup, the Super Admin is fully empowered without needing manual SQL commands.

If you ever add new permissions to the system, you will need to re-run the permission-granting logic to update the Super Admin role. A helper script (`scripts/fix_super_admin_permissions.py`) is provided for this purpose.
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
~
