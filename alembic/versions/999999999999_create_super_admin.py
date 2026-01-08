"""Seed super admin user with specific credentials

Revision ID: 999999999999
Revises: 5e1193696cbf
Create Date: 2026-01-06 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer, DateTime, Boolean, Text
from datetime import datetime
from passlib.context import CryptContext

# revision identifiers, used by Alembic.
revision = '999999999999'
down_revision = '5e1193696cbf'
branch_labels = None
depends_on = None

def upgrade():
    # Create password context for hashing
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # Define tables
    schools_table = table('schools',
        column('id', Integer),
        column('name', String),
        column('subdomain', String),
        column('address', Text),
        column('phone', String),
        column('email', String),
        column('website', String),
        column('principal_name', String),
        column('join_code', String),
        column('school_type', String),
        column('is_approved', Boolean),
        column('is_active', Boolean),
        column('created_at', DateTime),
        column('updated_at', DateTime)
    )

    users_table = table('users',
        column('id', Integer),
        column('email', String),
        column('username', String),
        column('first_name', String),
        column('last_name', String),
        column('hashed_password', String),
        column('is_active', Boolean),
        column('is_verified', Boolean),
        column('is_approved', Boolean),
        column('school_id', Integer),
        column('phone', String),
        column('address', Text),
        column('date_of_birth', DateTime),
        column('gender', String),
        column('created_at', DateTime),
        column('updated_at', DateTime)
    )

    user_roles_table = table('user_roles',
        column('user_id', Integer),
        column('role_id', Integer),
        column('assigned_at', DateTime)
    )

    # Create system school for super admin
    op.bulk_insert(schools_table, [
        {
            'name': 'System Administration',
            'subdomain': 'systemadmin',
            'address': 'System Admin, Global',
            'phone': '+1234567890',
            'email': 'system.admin@edrp.local',
            'website': 'https://system.edrp.local',
            'principal_name': 'System Admin',
            'join_code': 'SYS001',
            'school_type': 'System',
            'is_approved': True,
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    ])

    # Get the school ID
    connection = op.get_bind()
    school_result = connection.execute(
        sa.text("SELECT id FROM schools WHERE email = 'system.admin@edrp.local' LIMIT 1")
    ).fetchone()
    if school_result:
        school_id = school_result[0]
    else:
        # If the school wasn't inserted (due to conflict), get the existing one
        school_result = connection.execute(
            sa.text("SELECT id FROM schools WHERE subdomain = 'systemadmin' LIMIT 1")
        ).fetchone()
        school_id = school_result[0]

    # Hash the password
    hashed_password = pwd_context.hash("password123")

    # Create super admin user
    op.bulk_insert(users_table, [
        {
            'email': 'superadmin@edrp.com',
            'username': 'superadmin',
            'first_name': 'Super',
            'last_name': 'Admin',
            'hashed_password': hashed_password,
            'is_active': True,
            'is_verified': True,
            'is_approved': True,
            'school_id': school_id,  # Link to system school
            'phone': '+1234567890',
            'address': 'System Admin, Global',
            'date_of_birth': datetime.utcnow(),
            'gender': 'other',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    ])

    # Get user and role IDs
    user_result = connection.execute(
        sa.text("SELECT id FROM users WHERE email = 'superadmin@edrp.com' LIMIT 1")
    ).fetchone()
    user_id = user_result[0]

    # Get the Super Admin role ID (assuming it exists from previous migrations)
    role_result = connection.execute(
        sa.text("SELECT id FROM roles WHERE name = 'Super Admin' LIMIT 1")
    ).fetchone()
    if role_result:
        role_id = role_result[0]

        # Assign super_admin role to user
        op.bulk_insert(user_roles_table, [
            {
                'user_id': user_id,
                'role_id': role_id,
                'assigned_at': datetime.utcnow()
            }
        ])
    else:
        print("Warning: Super Admin role not found. Please ensure the roles are seeded first.")


def downgrade():
    # Remove super admin user and related data
    connection = op.get_bind()

    # Get user ID
    result = connection.execute(
        sa.text("SELECT id FROM users WHERE email = 'superadmin@edrp.com' LIMIT 1")
    ).fetchone()

    if result:
        user_id = result[0]

        # Remove user-role association
        op.execute(
            sa.text("DELETE FROM user_roles WHERE user_id = :user_id"),
            {"user_id": user_id}
        )

        # Remove user
        op.execute(
            sa.text("DELETE FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )

    # Remove system school
    op.execute(
        sa.text("DELETE FROM schools WHERE email = 'system.admin@edrp.local'")
    )
