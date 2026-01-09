# Performance & Real-time Tools Integration Guide

This document outlines the newly integrated performance and real-time tools added to the Education ERP System.

## 🚀 New Integrations Overview

### 1. Redis: Speed Engine
- **Purpose**: High-speed caching for user permissions and message broker for background tasks
- **Configuration**: Set `REDIS_URL` in your `.env` file
- **Default**: `redis://localhost:6379`

### 2. WebSockets: Real-time Communication
- **Purpose**: Enables live, two-way communication for instant notifications, live attendance updates, and real-time chat
- **Endpoints**:
  - `/api/ws/{user_id}` - General WebSocket for chat and real-time updates
  - `/api/ws/notifications/{user_id}` - Dedicated notification WebSocket

### 3. Celery: Heavy Lifter
- **Purpose**: Processes background tasks like generating PDF report cards or sending bulk emails
- **Configuration**: Set `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` in your `.env` file
- **Default**: `redis://localhost:6379/0`

### 4. Resend: Email Delivery Service
- **Purpose**: Sends automated system emails (alerts, resets, newsletters) with high reliability
- **Configuration**: Set `RESEND_API_KEY` in your `.env` file

### 5. Sentry: Error Tracking & Monitoring
- **Purpose**: Provides error tracking and performance monitoring
- **Configuration**: Set `SENTRY_DSN` in your `.env` file

## 🔧 Configuration

Add these variables to your `.env` file:

```env
# Redis Configuration
REDIS_URL=redis://localhost:6379

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Resend Configuration
RESEND_API_KEY=your_resend_api_key_here

# Sentry Configuration
SENTRY_DSN=your_sentry_dsn_here
SENTRY_ENVIRONMENT=development  # or production
```

## 🛠️ Running the Services

### Starting Redis
Make sure Redis is running on your system:
```bash
sudo systemctl start redis
# or if using Docker
docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
```

### Starting Celery Worker
```bash
cd /path/to/your/project
celery -A celery_app.celery_app worker --loglevel=info
```

### Starting Celery Beat (for scheduled tasks)
```bash
celery -A celery_app.celery_app beat --loglevel=info
```

## 📡 WebSocket Usage

### Client-side JavaScript Example:
```javascript
// Connect to WebSocket
const userId = 1; // Replace with actual user ID
const ws = new WebSocket(`ws://localhost:8000/api/ws/${userId}`);

ws.onopen = function(event) {
    console.log('Connected to WebSocket');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
    
    if (data.type === 'message') {
        // Handle chat message
        displayMessage(data);
    } else if (data.type === 'notification') {
        // Handle notification
        showNotification(data);
    }
};

ws.onclose = function(event) {
    console.log('WebSocket disconnected');
};

// Send a message
function sendMessage(recipientId, content) {
    const message = {
        type: 'message',
        recipient_id: recipientId,
        content: content,
        timestamp: Date.now()
    };
    ws.send(JSON.stringify(message));
}
```

## 📋 Available Celery Tasks

### 1. Bulk Email Sending
```python
from tasks.email_tasks import send_bulk_email

emails_data = [
    {
        "from": "noreply@yourschool.edu",
        "to": ["student@example.com"],
        "subject": "Important Notice",
        "html": "<p>Your message here</p>"
    }
]

result = send_bulk_email.delay(emails_data)
```

### 2. PDF Report Generation
```python
from tasks.report_tasks import generate_pdf_report

report_data = {
    "title": "Student Report",
    "content": "Report content here...",
    "report_id": "report_123"
}

result = generate_pdf_report.delay(report_data)
```

### 3. Attendance Sync
```python
from tasks.attendance_tasks import process_attendance_sync

attendance_data = [
    {
        "student_id": 1,
        "date": "2023-10-01",
        "status": "present"
    }
]

result = process_attendance_sync.delay(attendance_data)
```

## 🧪 Testing the Integrations

Run the integration test:
```bash
python test_integrations.py
```

## 🚀 Production Deployment Notes

1. **Redis**: Use a dedicated Redis instance or Redis Cloud service
2. **Celery**: Deploy workers separately and monitor their health
3. **Sentry**: Configure for production with appropriate sampling rates
4. **Resend**: Use production API keys and configure custom domains
5. **WebSockets**: Ensure your reverse proxy supports WebSocket connections

## 📊 Performance Improvements

With these integrations, you can expect:
- **Faster response times** through Redis caching
- **Better user experience** with real-time updates
- **Improved scalability** with background task processing
- **Enhanced reliability** with proper error tracking
- **Efficient email delivery** with Resend service

## 🔐 Security Considerations

- Always validate user IDs in WebSocket connections
- Secure your Redis instance with authentication
- Use HTTPS for WebSocket connections in production
- Rotate API keys regularly
- Monitor and audit all background tasks
