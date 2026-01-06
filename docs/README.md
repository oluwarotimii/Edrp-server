# Education ERP System

A comprehensive multi-tenant Education Enterprise Resource Planning (ERP) system built with FastAPI and PostgreSQL. This system provides complete school management functionality including student information management, teacher administration, academic tracking, attendance monitoring, fee management, and much more.

## 🏷️ Subdomain Support

Each school gets a unique subdomain (e.g., `yourschool.edrp.app`) with the following features:
- Custom subdomain selection during school registration
- Automatic subdomain generation from school name
- Subdomain availability checking
- Support for custom domains (configured at the DNS level)
- Subdomain-based routing for multi-tenancy

## 🚀 Features

### Core Modules
- **Multi-tenant Architecture** - Support multiple schools in a single deployment
- **User Management** - Role-based access control with comprehensive permissions
- **Student Management** - Complete student lifecycle management
- **Teacher Administration** - Staff management with assignments and qualifications
- **Academic Management** - Departments, classes, subjects, and sessions
- **Attendance Tracking** - GPS-verified attendance for students and teachers
- **Assessment & Grading** - Flexible assessment schemes and grading systems
- **Fee Management** - Integrated payment processing with Paystack
- **Communication System** - Internal messaging and notifications
- **Timetable Management** - Automated scheduling and conflict resolution
- **Admissions Processing** - Application management and document verification
- **Behavior Reporting** - Student behavior tracking and intervention
- **Analytics & Reports** - Comprehensive reporting and insights
- **Offline Support** - Offline data synchronization capabilities
- **Push Notifications** - Real-time notifications for important events

### Technical Features
- **RESTful API** - Complete REST API with OpenAPI/Swagger documentation
- **Authentication & Authorization** - JWT-based authentication with role permissions
- **Database Management** - PostgreSQL with SQLAlchemy ORM
- **Location Services** - GPS verification for attendance and security
- **File Management** - Document upload and management
- **Payment Integration** - Paystack payment gateway integration
- **Data Validation** - Comprehensive input validation and error handling
- **Logging & Monitoring** - Detailed logging and error tracking

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL database
- Redis (for caching and background tasks)
- Internet connection for payment processing

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd education-erp
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file with the following variables:
```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/education_erp

# Security
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Payment Gateway (Paystack)
PAYSTACK_SECRET_KEY=your-paystack-secret-key
PAYSTACK_PUBLIC_KEY=your-paystack-public-key

# Redis Configuration
REDIS_URL=redis://localhost:6379

# File Upload Settings
MAX_FILE_SIZE=10485760  # 10MB in bytes
UPLOAD_DIR=uploads

# Firebase Cloud Messaging (for push notifications)
FCM_SERVER_KEY=your-fcm-server-key

# Location Services
LOCATION_TOLERANCE_METERS=100
```

### 4. Database Setup
```bash
# The system will automatically create tables on first run
python main.py
```

### 5. Access the Application
- **API Documentation**: http://localhost:5000/docs
- **Alternative API Docs**: http://localhost:5000/redoc
- **Web Interface**: http://localhost:5000

## 📚 API Documentation

### Authentication

#### Register School
```http
POST /api/schools
Content-Type: application/json

{
  "name": "Example High School",
  "email": "admin@exampleschool.edu",
  "phone": "+1234567890",
  "address": "123 School Street, City, State",
  "admin_first_name": "John",
  "admin_last_name": "Doe",
  "admin_email": "john.doe@exampleschool.edu",
  "admin_phone": "+1234567890"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=john.doe@exampleschool.edu&password=your-password
```

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer <your-jwt-token>
```

### User Management

#### Create User
```http
POST /api/users
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "email": "teacher@school.edu",
  "username": "teacher1",
  "first_name": "Jane",
  "last_name": "Smith",
  "phone": "+1234567890",
  "role_ids": [2]
}
```

#### List Users
```http
GET /api/users?skip=0&limit=10
Authorization: Bearer <your-jwt-token>
```

#### Update User
```http
PUT /api/users/{user_id}
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "first_name": "Updated Name",
  "phone": "+0987654321"
}
```

### Student Management

#### Create Student
```http
POST /api/students
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "first_name": "Alice",
  "last_name": "Johnson",
  "date_of_birth": "2005-06-15",
  "gender": "female",
  "email": "alice.johnson@student.school.edu",
  "phone": "+1234567890",
  "address": "456 Student Ave, City, State",
  "admission_number": "STU2024001",
  "class_id": 1,
  "parent_first_name": "Robert",
  "parent_last_name": "Johnson",
  "parent_phone": "+1234567890",
  "parent_email": "robert.johnson@email.com"
}
```

#### List Students
```http
GET /api/students?skip=0&limit=10&class_id=1
Authorization: Bearer <your-jwt-token>
```

#### Get Student by ID
```http
GET /api/students/{student_id}
Authorization: Bearer <your-jwt-token>
```

### Teacher Management

#### Create Teacher
```http
POST /api/teachers
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "user_id": 2,
  "employee_id": "EMP2024001",
  "department_id": 1,
  "hire_date": "2024-01-15",
  "teaching_qualification": "Master's in Mathematics",
  "specialization": "Advanced Mathematics",
  "years_experience": 5,
  "contract_type": "permanent"
}
```

#### List Teachers
```http
GET /api/teachers?skip=0&limit=10&department_id=1
Authorization: Bearer <your-jwt-token>
```

### Academic Management

#### Create Department
```http
POST /api/academic/departments
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "name": "Mathematics Department",
  "description": "Handles all mathematics subjects"
}
```

#### Create Class
```http
POST /api/academic/classes
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "name": "Grade 10A",
  "description": "Grade 10 Section A",
  "capacity": 30,
  "room_number": "101",
  "grade_level": 10
}
```

#### Create Subject
```http
POST /api/academic/subjects
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "name": "Algebra",
  "code": "MATH101",
  "description": "Introduction to Algebra",
  "department_id": 1,
  "is_core": true,
  "credit_units": 3
}
```

### Attendance Management

#### Mark Student Attendance
```http
POST /api/attendance/students
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "student_id": 1,
  "date": "2024-01-15",
  "status": "present",
  "latitude": 40.7128,
  "longitude": -74.0060
}
```

#### Mark Teacher Attendance
```http
POST /api/attendance/teachers/clock-in
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "teacher_id": 1,
  "latitude": 40.7128,
  "longitude": -74.0060
}
```

### Assessment Management

#### Create Assessment
```http
POST /api/assessments
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "name": "Mid-term Exam",
  "description": "Mathematics mid-term examination",
  "subject_id": 1,
  "class_id": 1,
  "term_id": 1,
  "component_id": 1,
  "max_score": 100,
  "date_conducted": "2024-01-20"
}
```

#### Record Score
```http
POST /api/assessments/{assessment_id}/scores
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "student_id": 1,
  "score": 85.5,
  "remarks": "Good performance"
}
```

### Fee Management

#### Create Fee Structure
```http
POST /api/fees/structures
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "name": "Grade 10 Fees",
  "description": "Fee structure for Grade 10 students",
  "class_id": 1,
  "academic_session_id": 1,
  "amount": 5000.00,
  "due_date": "2024-02-01"
}
```

#### Process Payment
```http
POST /api/fees/payments
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "student_id": 1,
  "fee_structure_id": 1,
  "amount": 5000.00,
  "payment_method": "paystack"
}
```

### Communication

#### Send Message
```http
POST /api/communication/messages
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "recipient_id": 2,
  "subject": "Assignment Reminder",
  "content": "Please submit your mathematics assignment by Friday.",
  "message_type": "direct",
  "priority": "normal"
}
```

#### Create Behavior Report
```http
POST /api/communication/behavior-reports
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "student_id": 1,
  "incident_type": "academic",
  "severity": "minor",
  "title": "Late Assignment",
  "description": "Student submitted assignment 2 days late",
  "incident_date": "2024-01-15T09:00:00"
}
```

### Timetable Management

#### Create Timetable Entry
```http
POST /api/timetables/entries
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "subject_id": 1,
  "teacher_id": 1,
  "class_id": 1,
  "period_id": 1,
  "day_of_week": "monday",
  "academic_session_id": 1
}
```

#### Get Class Timetable
```http
GET /api/timetables/classes/{class_id}
Authorization: Bearer <your-jwt-token>
```

### Admissions

#### Submit Application
```http
POST /api/admissions/applications
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Smith",
  "date_of_birth": "2008-05-10",
  "gender": "male",
  "address": "789 Applicant Street",
  "phone": "+1234567890",
  "email": "john.smith@email.com",
  "parent_first_name": "Michael",
  "parent_last_name": "Smith",
  "parent_phone": "+1234567890",
  "parent_email": "michael.smith@email.com",
  "relationship_to_student": "father",
  "class_applying_for": 1,
  "previous_school": "Elementary School"
}
```

## 🔧 Configuration

### Database Models

The system includes the following main models:

#### User Management
- `User` - System users (students, teachers, staff, parents)
- `Role` - User roles with permissions
- `Permission` - Granular permissions for system access

#### School Management
- `School` - School/institution information
- `Department` - Academic departments
- `Class` - Student classes/grades
- `Subject` - Academic subjects

#### Student Management
- `Student` - Student information and records
- `Guardian` - Parent/guardian information

#### Teacher Management
- `Teacher` - Teacher profiles and information
- `TeacherAssignment` - Subject and class assignments

#### Academic Management
- `AcademicSession` - School years/sessions
- `Term` - Academic terms within sessions
- `Assessment` - Exams and evaluations
- `Score` - Student assessment scores

#### Attendance
- `AttendanceRecord` - Student attendance tracking
- `TeacherAttendance` - Teacher attendance tracking
- `AuthenticLocation` - Approved GPS locations

#### Financial Management
- `FeeStructure` - Fee definitions and amounts
- `Payment` - Payment records and transactions

#### Communication
- `Message` - Internal messaging system
- `BehaviorReport` - Student behavior tracking
- `Happening` - School events and announcements

### Permission System

The system uses a role-based permission system with the following default roles:

#### Super Admin
- Full system access
- Multi-school management
- System configuration

#### School Admin
- School-level administration
- User management within school
- Academic configuration

#### Teacher
- Class and subject management
- Student assessment
- Attendance marking

#### Student
- View personal information
- Access assignments and grades
- Submit applications

#### Parent
- View child's information
- Communication with teachers
- Fee payment

#### Accountant
- Financial management
- Fee structures
- Payment processing

### Location Verification

The system includes GPS-based location verification for:
- Student attendance marking
- Teacher clock-in/clock-out
- Secure access control

Configure location settings in environment variables:
```env
LOCATION_TOLERANCE_METERS=100  # Acceptable GPS accuracy
```

### Payment Integration

Paystack integration for fee payments:
1. Set up Paystack account
2. Configure API keys in environment
3. Test with Paystack test keys
4. Switch to live keys for production

### File Uploads

Configure file upload settings:
```env
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=uploads
```

Supported file types:
- Documents: PDF, DOC, DOCX
- Images: JPG, PNG, GIF
- Spreadsheets: XLS, XLSX, CSV

## 🔒 Security

### Authentication
- JWT token-based authentication
- Configurable token expiration
- Secure password hashing with bcrypt

### Authorization
- Role-based access control
- Granular permissions system
- Multi-tenant data isolation

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CORS configuration

### Location Security
- GPS verification for attendance
- Location-based access control
- Authentic location management

## 📊 API Response Format

### Success Response
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Example Data"
  },
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "error": true,
  "message": "Error description",
  "details": {
    "field": "error details"
  },
  "type": "ValidationError",
  "path": "/api/endpoint"
}
```

### Paginated Response
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Item 1"
    }
  ],
  "pagination": {
    "total": 100,
    "page": 1,
    "per_page": 10,
    "pages": 10
  }
}
```

## 🧪 Testing

### Manual Testing
Use the interactive API documentation at `/docs` to test endpoints.

### Automated Testing
```bash
# Run tests (when test suite is available)
pytest tests/
```

### API Testing with curl

#### Test Authentication
```bash
# Register school
curl -X POST "http://localhost:5000/api/schools" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test School",
    "email": "admin@testschool.edu",
    "phone": "+1234567890",
    "address": "123 Test Street",
    "admin_first_name": "Admin",
    "admin_last_name": "User",
    "admin_email": "admin@testschool.edu",
    "admin_phone": "+1234567890"
  }'

# Login
curl -X POST "http://localhost:5000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@testschool.edu&password=defaultpassword"
```

## 🚀 Deployment

### Production Deployment
1. Set up production PostgreSQL database
2. Configure Redis server
3. Set production environment variables
4. Use production WSGI server (Gunicorn)
5. Set up reverse proxy (Nginx)
6. Configure SSL certificates

### Docker Deployment
```dockerfile
# Dockerfile example
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
```

### Environment Variables for Production
```env
# Database
DATABASE_URL=postgresql://user:pass@prod-db:5432/education_erp

# Security (Generate strong keys for production)
SECRET_KEY=production-secret-key-here
JWT_SECRET_KEY=jwt-production-secret

# Payment (Use live keys)
PAYSTACK_SECRET_KEY=sk_live_...
PAYSTACK_PUBLIC_KEY=pk_live_...

# Redis
REDIS_URL=redis://prod-redis:6379

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## 📞 Support

For technical support or questions:
- Check the API documentation at `/docs`
- Review error logs in the application
- Ensure all environment variables are configured
- Verify database connectivity
- Check Redis connectivity for caching features

## 🔄 Updates and Maintenance

### Database Migrations
The system automatically creates tables on startup. For schema changes:
1. Update model definitions
2. Restart the application
3. Verify changes in database

### Backup and Recovery
Regular backups recommended:
```bash
# PostgreSQL backup
pg_dump education_erp > backup_$(date +%Y%m%d).sql

# Restore from backup
psql education_erp < backup_20240115.sql
```

## 📋 Troubleshooting

### Common Issues

#### Database Connection Error
- Verify DATABASE_URL is correct
- Check PostgreSQL service is running
- Ensure database exists

#### Authentication Issues
- Verify SECRET_KEY is set
- Check JWT token expiration
- Confirm user has proper roles

#### Payment Processing Errors
- Verify Paystack API keys
- Check network connectivity
- Review Paystack dashboard for errors

#### Location Verification Issues
- Check GPS accuracy
- Verify authentic locations are configured
- Ensure LOCATION_TOLERANCE_METERS is appropriate

### Logging
The application logs important events and errors. Check logs for:
- Authentication attempts
- Payment transactions
- Database operations
- API requests and responses

## 📄 License

This Education ERP System is proprietary software. All rights reserved.

---

**Note**: This documentation covers the core API endpoints and functionality. For complete API documentation with all available endpoints, request/response schemas, and examples, visit the interactive documentation at `http://localhost:5000/docs` when the application is running.