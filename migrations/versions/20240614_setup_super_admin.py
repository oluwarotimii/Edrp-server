"""Setup Super Admin

Revision ID: 20240614_setup_super_admin
Revises: 
Create Date: 2024-06-14 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '20240614_setup_super_admin'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create super admin role if not exists
    op.execute("""
        INSERT INTO roles (name, description, is_system_role, created_at, updated_at)
        SELECT 'Super Admin', 'System administrator with full access', true, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name = 'Super Admin');
        
        -- Create default admin role if not exists
        INSERT INTO roles (name, description, is_system_role, created_at, updated_at)
        SELECT 'Admin', 'School administrator with full access to their school', true, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name = 'Admin');
        
        -- Create system school if not exists
        INSERT INTO schools (name, email, address, is_approved, created_at, updated_at, join_code)
        SELECT 'System School', 'system@school.com', 'System Address', true, NOW(), NOW(), 'SYSTEM'
        WHERE NOT EXISTS (SELECT 1 FROM schools WHERE name = 'System School');
    """)
    
    # Create system admin user if not exists
    op.execute("""
        WITH system_school AS (
            SELECT id FROM schools WHERE name = 'System School'
        ),
        super_admin_role AS (
            SELECT id FROM roles WHERE name = 'Super Admin'
        )
        INSERT INTO users (
            username, email, first_name, last_name, hashed_password, 
            is_active, is_verified, is_approved, school_id, created_at, updated_at
        )
        SELECT 
            'system.admin', 
            'superadmin@example.com', 
            'System', 
            'Admin', 
            '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', -- password: 'password'
            true, true, true, 
            (SELECT id FROM system_school),
            NOW(), 
            NOW()
        WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'superadmin@example.com');
        
        -- Assign super admin role
        INSERT INTO user_roles (user_id, role_id, assigned_at, school_id)
        SELECT 
            (SELECT id FROM users WHERE email = 'superadmin@example.com'),
            (SELECT id FROM roles WHERE name = 'Super Admin'),
            NOW(),
            (SELECT id FROM schools WHERE name = 'System School')
        WHERE NOT EXISTS (
            SELECT 1 FROM user_roles 
            WHERE user_id = (SELECT id FROM users WHERE email = 'superadmin@example.com')
            AND role_id = (SELECT id FROM roles WHERE name = 'Super Admin')
        );
    """)

def downgrade():
    # Remove super admin user and role
    op.execute("""
        DELETE FROM user_roles 
        WHERE user_id = (SELECT id FROM users WHERE email = 'superadmin@example.com');
        
        DELETE FROM users WHERE email = 'superadmin@example.com';
        
        -- Only remove the role if you're sure it's not used elsewhere
        -- DELETE FROM roles WHERE name = 'Super Admin';
    """)
