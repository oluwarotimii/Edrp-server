"""Fix roles seeding

Revision ID: fix_roles_seeding
Revises: 7fa4d44500d9
Create Date: 2025-06-14 13:01:10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fix_roles_seeding'
down_revision: Union[str, None] = '7fa4d44500d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create an ad-hoc table object for the roles table
    roles_table = sa.table('roles',
        sa.column('name', sa.String),
        sa.column('description', sa.Text),
        sa.column('is_system_role', sa.Boolean)
    )

    # Insert the initial roles, including Super Admin
    op.bulk_insert(roles_table, [
        {'name': 'Admin', 'description': 'Administrator with full access', 'is_system_role': True},
        {'name': 'Teacher', 'description': 'A teacher in the school', 'is_system_role': True},
        {'name': 'Student', 'description': 'A student in the school', 'is_system_role': True},
        {'name': 'Parent', 'description': 'A parent or guardian of a student', 'is_system_role': True},
        {'name': 'Super Admin', 'description': 'System administrator with full access', 'is_system_role': True}
    ])

    # Grant all existing permissions to the Super Admin role.
    # This ensures that the Super Admin is always fully empowered upon database creation.
    op.execute("""
    INSERT INTO public.role_permissions (role_id, permission_id)
    SELECT
        (SELECT id FROM roles WHERE name = 'Super Admin') as role_id,
        p.id as permission_id
    FROM permissions p
    ON CONFLICT (role_id, permission_id) DO NOTHING;
    """)


def downgrade() -> None:
    # Delete the initial roles, including Super Admin
    op.execute("DELETE FROM roles WHERE name IN ('Admin', 'Teacher', 'Student', 'Parent', 'Super Admin')")
