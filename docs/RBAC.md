# RBAC (Role-Based Access Control) System

This document describes the Role-Based Access Control system implemented in the Education ERP system.

## Overview

The RBAC system provides fine-grained access control through:
- **Roles**: Collections of permissions assigned to users
- **Permissions**: Specific actions that can be performed on resources
- **Users**: Individuals who are assigned roles

## Components

### 1. Models

- `User`: Represents system users
- `Role`: Represents collections of permissions
- `Permission`: Represents specific actions
- Association tables for many-to-many relationships

### 2. Services

- `PermissionService`: Core logic for permission checking and role management

### 3. Dependencies

- `require_permission()`: Check for specific permission
- `require_any_permission()`: Check for any of specified permissions
- `require_all_permissions()`: Check for all specified permissions
- `require_role()`: Check for specific role
- `require_any_role()`: Check for any of specified roles

## Default Roles

The system includes these default roles:

- `super_admin`: System-wide administrator with all permissions
- `school_admin`: School-level administrator
- `teacher`: Teacher with access to student data, assessments, etc.
- `student`: Student with access to their own data
- `parent`: Parent/guardian with access to their children's data
- `accountant`: Financial operations access

## Default Permissions

Permissions follow the format: `\{module\}:\{action\}` or `\{module\}:\{action\}:\{resource\}`

Examples:
- `users:view` - View users
- `students:create` - Create students
- `schools:manage` - Manage schools

## API Endpoints

### System-Level Management (Super Admin Only)
- `GET /api/system/roles` - Get all roles
- `POST /api/system/roles` - Create a role
- `GET /api/system/permissions` - Get all permissions
- `POST /api/system/permissions` - Create a permission
- `POST /api/system/roles/\{role_id\}/permissions/\{permission_id\}` - Assign permission to role

### School-Level Management (School Admin)
- `GET /api/school/roles` - Get school roles
- `POST /api/school/roles` - Create school role
- `GET /api/school/permissions` - Get permissions

## Usage Examples

### In Route Handlers

```python
from utils.dependencies import require_permission, require_role

@router.get("/students", dependencies=[Depends(require_permission("students:view"))])
async def get_students():
    # Only users with "students:view" permission can access this
    pass

@router.post("/admin", dependencies=[Depends(require_role("school_admin"))])
async def admin_action():
    # Only users with "school_admin" role can access this
    pass
```

### In Code

```python
from services.permissions import PermissionService

# Check if user has specific permission
if PermissionService.has_permission(current_user, "students:view", db):
    # Allow access
    pass

# Check if user has any of the permissions
if PermissionService.has_any_permission(current_user, ["students:view", "students:update"], db):
    # Allow access
    pass
```

## Initialization

To initialize default permissions and system roles:

```bash
python scripts/setup_rbac.py
```

To initialize default roles for a specific school (run when a new school is created):

```bash
python scripts/initialize_school_roles.py <school_id>
```

## Testing

To test RBAC functionality:

```bash
python scripts/test_rbac.py
```

## Key Improvements Made

1. **Consistent Role Naming**: Fixed inconsistency between "Super Admin" and "super_admin"
2. **Enhanced Permission Checking**: All permission checks now use the PermissionService
3. **User Model Methods**: Added convenience methods to User model for permission checking
4. **Duplicate Endpoint Removal**: Removed duplicate login endpoint
5. **Robust Role Checking**: Added fallbacks for role naming inconsistencies
6. **Proper Role Separation**: System roles (like super_admin) are separate from school-specific roles
7. **School-Specific Role Creation**: Added method to create school-specific roles when schools are registered
