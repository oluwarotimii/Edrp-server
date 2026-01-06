# Education ERP API Endpoints Reference

## Base URL
```
http://localhost:5000
```

## Authentication
All authenticated endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

---

## 🏫 School Management

### Register School
```http
POST /api/schools
```
**Body:**
```json
{
  "name": "Springfield High School",
  "email": "admin@springfield.edu",
  "phone": "+1-555-0123",
  "address": "123 Education St, Springfield, ST 12345",
  "website": "https://springfield.edu",
  "admin_first_name": "John",
  "admin_last_name": "Principal",
  "admin_email": "john.principal@springfield.edu",
  "admin_phone": "+1-555-0124"
}
```

### Get School Details
```http
GET /api/schools/{school_id}
Authorization: Bearer <token>
```

### Update School
```http
PUT /api/schools/{school_id}
Authorization: Bearer <token>
```

---

## 🔐 Authentication & Authorization

### Login
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded
```
**Body:**
```
username=john.doe@school.edu&password=secretpassword
```

### Get Current User
```http
GET /api/auth/me
Authorization: Bearer <token>
```

### Change Password
```http
POST /api/auth/change-password
Authorization: Bearer <token>
```
**Body:**
```json
{
  "current_password": "oldpassword",
  "new_password": "newpassword"
}
```

### Refresh Token
```http
POST /api/auth/refresh
Authorization: Bearer <token>
```

---

## 👥 User Management

### Create User
```http
POST /api/users
Authorization: Bearer <token>
```
**Body:**
```json
{
  "email": "teacher@school.edu",
  "username": "teacher123",
  "first_name": "Sarah",
  "last_name": "Johnson",
  "middle_name": "Marie",
  "phone": "+1-555-0125",
  "address": "456 Teacher Lane, City, ST 67890",
  "date_of_birth": "1985-03-15",
  "gender": "female",
  "role_ids": [2]
}
```

### List Users
```http
GET /api/users?skip=0&limit=10&role=teacher&search=sarah
Authorization: Bearer <token>
```

### Get User by ID
```http
GET /api/users/{user_id}
Authorization: Bearer <token>
```

### Update User
```http
PUT /api/users/{user_id}
Authorization: Bearer <token>
```

### Delete User
```http
DELETE /api/users/{user_id}
Authorization: Bearer <token>
```

### Assign Role to User
```http
POST /api/users/{user_id}/roles
Authorization: Bearer <token>
```
**Body:**
```json
{
  "role_id": 3
}
```

---

## 🎓 Student Management

### Create Student
```http
POST /api/students
Authorization: Bearer <token>
```
**Body:**
```json
{
  "first_name": "Emma",
  "last_name": "Wilson",
  "middle_name": "Grace",
  "date_of_birth": "2008-09-12",
  "gender": "female",
  "email": "emma.wilson@student.school.edu",
  "phone": "+1-555-0126",
  "address": "789 Student St, City, ST 11111",
  "admission_number": "STU2024001",
  "admission_date": "2024-01-15",
  "class_id": 1,
  "blood_group": "O+",
  "medical_conditions": "None",
  "parent_first_name": "David",
  "parent_last_name": "Wilson",
  "parent_phone": "+1-555-0127",
  "parent_email": "david.wilson@email.com",
  "parent_occupation": "Engineer",
  "parent_address": "789 Student St, City, ST 11111",
  "relationship_to_student": "father"
}
```

### List Students
```http
GET /api/students?skip=0&limit=10&class_id=1&status=active&search=emma
Authorization: Bearer <token>
```

### Get Student by ID
```http
GET /api/students/{student_id}
Authorization: Bearer <token>
```

### Update Student
```http
PUT /api/students/{student_id}
Authorization: Bearer <token>
```

### Get Student Academic Record
```http
GET /api/students/{student_id}/academic-record
Authorization: Bearer <token>
```

### Get Student Attendance Summary
```http
GET /api/students/{student_id}/attendance-summary?start_date=2024-01-01&end_date=2024-12-31
Authorization: Bearer <token>
```

---

## 👨‍🏫 Teacher Management

### Create Teacher
```http
POST /api/teachers
Authorization: Bearer <token>
```
**Body:**
```json
{
  "user_id": 5,
  "employee_id": "EMP2024001",
  "department_id": 1,
  "hire_date": "2024-01-15",
  "status": "active",
  "teaching_qualification": "Master of Science in Mathematics",
  "specialization": "Advanced Algebra and Calculus",
  "years_experience": 8,
  "salary_grade": "Grade 5",
  "contract_type": "permanent",
  "emergency_contact_name": "Jane Johnson",
  "emergency_contact_phone": "+1-555-0128",
  "bank_details": {
    "account_number": "1234567890",
    "bank_name": "First National Bank",
    "routing_number": "123456789"
  },
  "certifications": {
    "teaching_license": "TL123456",
    "subject_certification": "MATH-ADV-2023"
  }
}
```

### List Teachers
```http
GET /api/teachers?skip=0&limit=10&department_id=1&status=active
Authorization: Bearer <token>
```

### Get Teacher by ID
```http
GET /api/teachers/{teacher_id}
Authorization: Bearer <token>
```

### Update Teacher
```http
PUT /api/teachers/{teacher_id}
Authorization: Bearer <token>
```

### Get Teacher Assignments
```http
GET /api/teachers/{teacher_id}/assignments
Authorization: Bearer <token>
```

### Assign Teacher to Subject/Class
```http
POST /api/teachers/{teacher_id}/assignments
Authorization: Bearer <token>
```
**Body:**
```json
{
  "subject_id": 1,
  "class_id": 1,
  "academic_session_id": 1,
  "is_class_teacher": false
}
```

---

## 📚 Academic Management

### Departments

#### Create Department
```http
POST /api/academic/departments
Authorization: Bearer <token>
```
**Body:**
```json
{
  "name": "Mathematics Department",
  "description": "Handles all mathematics subjects from basic arithmetic to advanced calculus"
}
```

#### List Departments
```http
GET /api/academic/departments
Authorization: Bearer <token>
```

#### Update Department
```http
PUT /api/academic/departments/{department_id}
Authorization: Bearer <token>
```

### Classes

#### Create Class
```http
POST /api/academic/classes
Authorization: Bearer <token>
```
**Body:**
```json
{
  "name": "Grade 10A",
  "description": "Grade 10 Section A - Science Track",
  "class_teacher_id": 2,
  "capacity": 35,
  "room_number": "Room 201",
  "grade_level": 10
}
```

#### List Classes
```http
GET /api/academic/classes?grade_level=10
Authorization: Bearer <token>
```

#### Get Class Details
```http
GET /api/academic/classes/{class_id}
Authorization: Bearer <token>
```

### Subjects

#### Create Subject
```http
POST /api/academic/subjects
Authorization: Bearer <token>
```
**Body:**
```json
{
  "name": "Advanced Algebra",
  "code": "MATH201",
  "description": "Advanced algebraic concepts including polynomials and functions",
  "department_id": 1,
  "is_core": true,
  "credit_units": 4
}
```

#### List Subjects
```http
GET /api/academic/subjects?department_id=1&is_core=true
Authorization: Bearer <token>
```

#### Assign Subject to Class
```http
POST /api/academic/subjects/{subject_id}/classes
Authorization: Bearer <token>
```
**Body:**
```json
{
  "class_id": 1
}
```

### Academic Sessions

#### Create Academic Session
```http
POST /api/academic/sessions
Authorization: Bearer <token>
```
**Body:**
```json
{
  "name": "2024-2025 Academic Year",
  "start_date": "2024-09-01",
  "end_date": "2025-06-30",
  "is_current": true
}
```

#### Create Term
```http
POST /api/academic/terms
Authorization: Bearer <token>
```
**Body:**
```json
{
  "name": "First Term",
  "academic_session_id": 1,
  "start_date": "2024-09-01",
  "end_date": "2024-12-15",
  "is_current": true
}
```

---

## 📊 Assessment Management

### Assessment Schemes

#### Create Assessment Scheme
```http
POST /api/assessments/schemes
Authorization: Bearer <token>
```
**Body:**
```json
{
  "name": "Standard Assessment Scheme",
  "description": "Standard assessment breakdown for all subjects",
  "is_default": true
}
```

#### Create Assessment Component
```http
POST /api/assessments/components
Authorization: Bearer <token>
```
**Body:**
```json
{
  "scheme_id": 1,
  "name": "Continuous Assessment",
  "weight_percentage": 40.0,
  "max_score": 40.0
}
```

### Grading Scales

#### Create Grading Scale
```http
POST /api/assessments/grading-scales
Authorization: Bearer <token>
```
**Body:**
```json
{
  "grade": "A",
  "min_score": 90.0,
  "max_score": 100.0,
  "description": "Excellent",
  "gpa_value": 4.0
}
```

### Assessments

#### Create Assessment
```http
POST /api/assessments
Authorization: Bearer <token>
```
**Body:**
```json
{
  "name": "Mid-Term Mathematics Exam",
  "description": "Comprehensive mid-term examination covering algebra and geometry",
  "subject_id": 1,
  "class_id": 1,
  "term_id": 1,
  "component_id": 1,
  "max_score": 100.0,
  "date_conducted": "2024-02-15",
  "duration_minutes": 120,
  "instructions": "Answer all questions. Show all working clearly."
}
```

#### List Assessments
```http
GET /api/assessments?subject_id=1&class_id=1&term_id=1
Authorization: Bearer <token>
```

#### Record Assessment Score
```http
POST /api/assessments/{assessment_id}/scores
Authorization: Bearer <token>
```
**Body:**
```json
{
  "student_id": 1,
  "score": 87.5,
  "remarks": "Excellent performance in all sections"
}
```

#### Get Assessment Results
```http
GET /api/assessments/{assessment_id}/results
Authorization: Bearer <token>
```

---

## ✅ Attendance Management

### Authentic Locations

#### Create Authentic Location
```http
POST /api/attendance/locations
Authorization: Bearer <token>
```
**Body:**
```json
{
  "name": "Main School Building",
  "description": "Primary school building for attendance marking",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "radius_meters": 100,
  "is_default": true
}
```

### Student Attendance

#### Mark Student Attendance
```http
POST /api/attendance/students
Authorization: Bearer <token>
```
**Body:**
```json
{
  "student_id": 1,
  "date": "2024-01-15",
  "session_name": "morning",
  "status": "present",
  "period_id": 1,
  "subject_id": 1,
  "notes": "Present for mathematics class",
  "latitude": 40.7128,
  "longitude": -74.0060
}
```

#### Get Student Attendance
```http
GET /api/attendance/students/{student_id}?start_date=2024-01-01&end_date=2024-01-31
Authorization: Bearer <token>
```

#### Get Class Attendance
```http
GET /api/attendance/classes/{class_id}?date=2024-01-15
Authorization: Bearer <token>
```

### Teacher Attendance

#### Teacher Clock In
```http
POST /api/attendance/teachers/clock-in
Authorization: Bearer <token>
```
**Body:**
```json
{
  "teacher_id": 1,
  "latitude": 40.7128,
  "longitude": -74.0060,
  "notes": "Arrived on time"
}
```

#### Teacher Clock Out
```http
POST /api/attendance/teachers/clock-out
Authorization: Bearer <token>
```
**Body:**
```json
{
  "teacher_id": 1,
  "latitude": 40.7128,
  "longitude": -74.0060,
  "notes": "End of regular hours"
}
```

#### Get Teacher Attendance
```http
GET /api/attendance/teachers/{teacher_id}?start_date=2024-01-01&end_date=2024-01-31
Authorization: Bearer <token>
```

---

## 💰 Fee Management

### Fee Structures

#### Create Fee Structure
```http
POST /api/fees/structures
Authorization: Bearer <token>
```
**Body:**
```json
{
  "name": "Grade 10 Annual Fees",
  "description": "Complete fee structure for Grade 10 students",
  "class_id": 1,
  "academic_session_id": 1,
  "amount": 15000.00,
  "currency": "USD",
  "due_date": "2024-02-01",
  "late_fee_amount": 50.00,
  "installment_allowed": true,
  "installment_count": 3
}
```

#### List Fee Structures
```http
GET /api/fees/structures?class_id=1&academic_session_id=1
Authorization: Bearer <token>
```

### Payments

#### Process Payment
```http
POST /api/fees/payments
Authorization: Bearer <token>
```
**Body:**
```json
{
  "student_id": 1,
  "fee_structure_id": 1,
  "amount": 5000.00,
  "payment_method": "paystack",
  "payment_reference": "PAY123456789",
  "notes": "First installment payment"
}
```

#### Get Student Payment History
```http
GET /api/fees/students/{student_id}/payments
Authorization: Bearer <token>
```

#### Get Payment Summary
```http
GET /api/fees/summary?start_date=2024-01-01&end_date=2024-12-31
Authorization: Bearer <token>
```

### Paystack Integration

#### Initialize Payment
```http
POST /api/fees/paystack/initialize
Authorization: Bearer <token>
```
**Body:**
```json
{
  "student_id": 1,
  "fee_structure_id": 1,
  "amount": 5000.00,
  "email": "parent@email.com"
}
```

#### Verify Payment
```http
POST /api/fees/paystack/verify
Authorization: Bearer <token>
```
**Body:**
```json
{
  "reference": "paystack_reference_here"
}
```

---

## 💬 Communication

### Messages

#### Send Message
```http
POST /api/communication/messages
Authorization: Bearer <token>
```
**Body:**
```json
{
  "recipient_id": 5,
  "subject": "Parent-Teacher Conference",
  "content": "We would like to schedule a meeting to discuss Emma's progress in mathematics.",
  "message_type": "direct",
  "priority": "normal",
  "attachments": {}
}
```

#### Get Messages
```http
GET /api/communication/messages?type=received&skip=0&limit=10
Authorization: Bearer <token>
```

#### Mark Message as Read
```http
PUT /api/communication/messages/{message_id}/read
Authorization: Bearer <token>
```

### Behavior Reports

#### Create Behavior Report
```http
POST /api/communication/behavior-reports
Authorization: Bearer <token>
```
**Body:**
```json
{
  "student_id": 1,
  "incident_date": "2024-01-15T10:30:00",
  "incident_type": "academic",
  "severity": "minor",
  "title": "Assignment Not Submitted",
  "description": "Student failed to submit mathematics homework for the third consecutive day.",
  "location": "Mathematics Classroom",
  "action_taken": "Verbal warning given and parent contacted",
  "follow_up_required": true,
  "follow_up_date": "2024-01-20T09:00:00"
}
```

#### Get Behavior Reports
```http
GET /api/communication/behavior-reports?student_id=1&severity=minor
Authorization: Bearer <token>
```

### Happenings (Events/Announcements)

#### Create Happening
```http
POST /api/communication/happenings
Authorization: Bearer <token>
```
**Body:**
```json
{
  "title": "Science Fair 2024",
  "description": "Annual science fair showcasing student projects and innovations",
  "category": "event",
  "target_audience": "all",
  "event_date": "2024-03-15T09:00:00",
  "location": "Main Auditorium",
  "is_published": true,
  "attachments": {}
}
```

#### Get Happenings
```http
GET /api/communication/happenings?category=event&target_audience=students
Authorization: Bearer <token>
```

---

## 📅 Timetable Management

### Periods

#### Create Period
```http
POST /api/timetables/periods
Authorization: Bearer <token>
```
**Body:**
```json
{
  "name": "Period 1",
  "start_time": "08:00:00",
  "end_time": "08:45:00",
  "period_number": 1,
  "is_break": false
}
```

### Timetable Entries

#### Create Timetable Entry
```http
POST /api/timetables/entries
Authorization: Bearer <token>
```
**Body:**
```json
{
  "subject_id": 1,
  "teacher_id": 2,
  "class_id": 1,
  "period_id": 1,
  "day_of_week": "monday",
  "academic_session_id": 1,
  "room_number": "Room 201"
}
```

#### Get Class Timetable
```http
GET /api/timetables/classes/{class_id}?academic_session_id=1
Authorization: Bearer <token>
```

#### Get Teacher Timetable
```http
GET /api/timetables/teachers/{teacher_id}?academic_session_id=1
Authorization: Bearer <token>
```

#### Check Timetable Conflicts
```http
POST /api/timetables/check-conflicts
Authorization: Bearer <token>
```
**Body:**
```json
{
  "teacher_id": 2,
  "period_id": 1,
  "day_of_week": "monday",
  "academic_session_id": 1
}
```

---

## 🎓 Admissions

### Applications

#### Submit Application
```http
POST /api/admissions/applications
```
**Body:**
```json
{
  "first_name": "Michael",
  "last_name": "Brown",
  "middle_name": "James",
  "date_of_birth": "2009-04-22",
  "gender": "male",
  "address": "321 Applicant Avenue, City, ST 33333",
  "phone": "+1-555-0129",
  "email": "michael.brown@email.com",
  "parent_first_name": "Robert",
  "parent_last_name": "Brown",
  "parent_phone": "+1-555-0130",
  "parent_email": "robert.brown@email.com",
  "parent_occupation": "Doctor",
  "parent_address": "321 Applicant Avenue, City, ST 33333",
  "relationship_to_student": "father",
  "previous_school": "Lincoln Elementary School",
  "class_applying_for": 1,
  "academic_session_id": 1,
  "medical_conditions": "Mild asthma",
  "special_needs": "None",
  "additional_info": {
    "extracurricular_interests": ["soccer", "chess"],
    "academic_achievements": ["Honor Roll 2023"]
  }
}
```

#### List Applications
```http
GET /api/admissions/applications?status=submitted&class_id=1
Authorization: Bearer <token>
```

#### Review Application
```http
PUT /api/admissions/applications/{application_id}/review
Authorization: Bearer <token>
```
**Body:**
```json
{
  "status": "accepted",
  "notes": "Excellent academic record and strong recommendation letters"
}
```

### Application Documents

#### Upload Document
```http
POST /api/admissions/applications/{application_id}/documents
Authorization: Bearer <token>
Content-Type: multipart/form-data
```
**Form Data:**
- `file`: Document file
- `document_type`: "birth_certificate" | "transcript" | "passport" | "recommendation"

#### Verify Document
```http
PUT /api/admissions/documents/{document_id}/verify
Authorization: Bearer <token>
```

---

## 📊 Analytics & Reports

### School Analytics

#### Get School Dashboard
```http
GET /api/analytics/dashboard
Authorization: Bearer <token>
```

#### Get Enrollment Statistics
```http
GET /api/analytics/enrollment?academic_session_id=1
Authorization: Bearer <token>
```

#### Get Attendance Statistics
```http
GET /api/analytics/attendance?start_date=2024-01-01&end_date=2024-01-31
Authorization: Bearer <token>
```

#### Get Financial Reports
```http
GET /api/analytics/financial?start_date=2024-01-01&end_date=2024-12-31
Authorization: Bearer <token>
```

### Academic Reports

#### Get Class Performance
```http
GET /api/analytics/performance/classes/{class_id}?term_id=1
Authorization: Bearer <token>
```

#### Get Subject Performance
```http
GET /api/analytics/performance/subjects/{subject_id}?term_id=1
Authorization: Bearer <token>
```

#### Generate Report Card
```http
GET /api/analytics/report-cards/{student_id}?term_id=1
Authorization: Bearer <token>
```

---

## 🔧 Admin Tools

### Data Management

#### Bulk Import Students
```http
POST /api/admin/import/students
Authorization: Bearer <token>
Content-Type: multipart/form-data
```
**Form Data:**
- `file`: CSV file with student data

#### Export Data
```http
GET /api/admin/export/{data_type}?format=csv&start_date=2024-01-01
Authorization: Bearer <token>
```
**Data Types:** `students`, `teachers`, `attendance`, `payments`, `assessments`

### System Settings

#### Update School Settings
```http
PUT /api/admin/settings
Authorization: Bearer <token>
```
**Body:**
```json
{
  "academic_year_start_month": 9,
  "attendance_grace_period_minutes": 15,
  "late_fee_grace_days": 7,
  "notification_preferences": {
    "email_enabled": true,
    "sms_enabled": false,
    "push_enabled": true
  }
}
```

#### Get System Health
```http
GET /api/admin/health
Authorization: Bearer <token>
```

### Backup & Maintenance

#### Create Backup
```http
POST /api/admin/backup
Authorization: Bearer <token>
```

#### Get Audit Logs
```http
GET /api/admin/audit-logs?start_date=2024-01-01&user_id=1
Authorization: Bearer <token>
```

---

## 🔄 Sync Management

### Offline Sync

#### Upload Offline Data
```http
POST /api/sync/upload
Authorization: Bearer <token>
```
**Body:**
```json
{
  "sync_data": {
    "attendance_records": [
      {
        "student_id": 1,
        "date": "2024-01-15",
        "status": "present",
        "offline_timestamp": "2024-01-15T08:30:00"
      }
    ],
    "assessments": [],
    "messages": []
  },
  "device_id": "device_123",
  "last_sync_timestamp": "2024-01-14T18:00:00"
}
```

#### Download Sync Data
```http
GET /api/sync/download?last_sync=2024-01-14T18:00:00
Authorization: Bearer <token>
```

#### Resolve Sync Conflicts
```http
POST /api/sync/resolve-conflicts
Authorization: Bearer <token>
```
**Body:**
```json
{
  "conflict_id": "conflict_123",
  "resolution": "server_wins",
  "resolved_data": {}
}
```

---

## 📱 Push Notifications

### Send Notification
```http
POST /api/notifications/send
Authorization: Bearer <token>
```
**Body:**
```json
{
  "recipient_ids": [1, 2, 3],
  "title": "Assignment Due Tomorrow",
  "body": "Don't forget to submit your mathematics assignment by 5 PM tomorrow.",
  "data": {
    "type": "assignment_reminder",
    "assignment_id": 123
  },
  "schedule_time": "2024-01-16T08:00:00"
}
```

### Get Notification History
```http
GET /api/notifications/history?user_id=1&skip=0&limit=10
Authorization: Bearer <token>
```

---

## 📄 File Management

### Upload File
```http
POST /api/files/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data
```
**Form Data:**
- `file`: File to upload
- `category`: "documents" | "images" | "profiles"
- `description`: "Optional file description"

### Get File
```http
GET /api/files/{file_id}
Authorization: Bearer <token>
```

### Delete File
```http
DELETE /api/files/{file_id}
Authorization: Bearer <token>
```

---

## ⚙️ System Information

### API Health Check
```http
GET /health
```

### API Documentation
```http
GET /docs
```

### OpenAPI Schema
```http
GET /openapi.json
```

---

## 📝 Response Codes

### Success Codes
- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `204 No Content` - Request successful, no content returned

### Client Error Codes
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict
- `422 Unprocessable Entity` - Validation error

### Server Error Codes
- `500 Internal Server Error` - Server error
- `502 Bad Gateway` - External service error
- `503 Service Unavailable` - Service temporarily unavailable

---

## 🔍 Query Parameters

### Common Parameters
- `skip` - Number of records to skip (pagination)
- `limit` - Maximum number of records to return
- `search` - Search term for filtering
- `sort_by` - Field to sort by
- `sort_order` - Sort direction (`asc` or `desc`)
- `start_date` - Start date for date-range queries
- `end_date` - End date for date-range queries

### Filtering
Most list endpoints support filtering by relevant fields:
```http
GET /api/students?class_id=1&status=active&gender=female
GET /api/teachers?department_id=2&contract_type=permanent
GET /api/assessments?subject_id=1&term_id=1&is_published=true
```

---

This comprehensive API reference covers all major endpoints in the Education ERP system. For interactive testing and detailed request/response schemas, visit the automatically generated documentation at `/docs` when the server is running.