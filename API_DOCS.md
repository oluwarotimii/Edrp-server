# SchoolMaster API Documentation

## Table of Contents
- [Authentication](#authentication)
- [Schools](#schools)
- [Users](#users)
- [Roles & Permissions](#roles--permissions)
- [Super Admin Setup](#super-admin-setup)

## Authentication

### Login
```bash
curl -X POST https://edrp-server-production.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin@test.school.com", "password": "SecurePass123"}'
```

### Refresh Token
```bash
curl -X POST https://edrp-server-production.up.railway.app/api/auth/refresh \
  -H "Authorization: Bearer <refresh_token>"
```

## Schools

### Register New School
```bash
curl -X POST https://edrp-server-production.up.railway.app/api/schools \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test School",
    "address": "123 School St",
    "email": "test.school@example.com",
    "principal_name": "John Doe",
    "school_type": "Day",
    "admin_first_name": "Admin",
    "admin_last_name": "User",
    "admin_email": "admin@test.school.com",
    "admin_password": "SecurePass123"
  }'
```

### Get All Schools (Admin Only)
```bash
curl -X GET https://edrp-server-production.up.railway.app/api/schools \
  -H "Authorization: Bearer <access_token>"
```

### Get School by ID
```bash
curl -X GET https://edrp-server-production.up.railway.app/api/schools/1 \
  -H "Authorization: Bearer <access_token>"
```

## Users

### Get Current User
```bash
curl -X GET https://edrp-server-production.up.railway.app/api/users/me \
  -H "Authorization: Bearer <access_token>"
```

### Get All Users (Admin Only)
```bash
curl -X GET https://edrp-server-production.up.railway.app/api/users \
  -H "Authorization: Bearer <access_token>"
```

## Roles & Permissions

### Get All Roles
```bash
curl -X GET https://edrp-server-production.up.railway.app/api/roles \
  -H "Authorization: Bearer <access_token>"
```

### Get Role by ID
```bash
curl -X GET https://edrp-server-production.up.railway.app/api/roles/1 \
  -H "Authorization: Bearer <access_token>"
```

## Super Admin Setup

To create a super admin user, you'll need to:

1. First, make sure you have a super admin role in your database. You can add this by running the following SQL in your database:

```sql
INSERT INTO roles (name, description, is_system_role, created_at, updated_at)
VALUES ('Super Admin', 'System administrator with full access', true, NOW(), NOW());

-- Then get the role ID and insert the permissions
INSERT INTO role_permissions (role_id, permission_id, created_at, updated_at)
SELECT 
  (SELECT id FROM roles WHERE name = 'Super Admin') as role_id,
  id as permission_id,
  NOW(),
  NOW()
FROM permissions;
```

2. Then create a super admin user through the API:

```bash
# First, create a school (if not exists)
curl -X POST https://edrp-server-production.up.railway.app/api/schools \
  -H "Content-Type: application/json" \
  -d '{
    "name": "System School",
    "address": "System Address",
    "email": "system@school.com",
    "principal_name": "System Admin",
    "school_type": "Day",
    "admin_first_name": "System",
    "admin_last_name": "Admin",
    "admin_email": "superadmin@example.com",
    "admin_password": "SuperSecurePassword123!"
  }'

# Then update the user to be a super admin (run this in your database)
UPDATE user_roles 
SET role_id = (SELECT id FROM roles WHERE name = 'Super Admin')
WHERE user_id = (SELECT id FROM users WHERE email = 'superadmin@example.com');
```

3. Alternatively, you can create a migration to set up the initial super admin:

```python
# In a new migration file
def upgrade():
    op.execute("""
        -- Create super admin role if not exists
        INSERT INTO roles (name, description, is_system_role, created_at, updated_at)
        SELECT 'Super Admin', 'System administrator with full access', true, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name = 'Super Admin');
        
        -- Assign all permissions to super admin role
        INSERT INTO role_permissions (role_id, permission_id, created_at, updated_at)
        SELECT 
            (SELECT id FROM roles WHERE name = 'Super Admin'),
            id,
            NOW(),
            NOW()
        FROM permissions
        ON CONFLICT DO NOTHING;
    """)

def downgrade():
    # Remove super admin role and its permissions
    op.execute("""
        DELETE FROM role_permissions 
        WHERE role_id = (SELECT id FROM roles WHERE name = 'Super Admin');
        
        DELETE FROM roles WHERE name = 'Super Admin';
    """)
```

## Environment Variables

Make sure these environment variables are set in your Railway dashboard:

```
DATABASE_URL=postgresql://user:password@host:port/dbname
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Running Tests

To test the API endpoints, you can use the provided curl commands or import the collection into Postman. Make sure to:

1. Update the base URL if you're running locally
2. Replace `<access_token>` with a valid JWT token
3. Replace any placeholders like `:id` with actual IDs
