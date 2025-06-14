"""Seed initial roles

Revision ID: bcddb5beb96e
Revises: 7fa4d44500d9
Create Date: 2025-06-14 02:52:43.191363

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bcddb5beb96e'
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

    # Insert the initial roles
    op.bulk_insert(roles_table, [
        {'name': 'Admin', 'description': 'Administrator with full access', 'is_system_role': True},
        {'name': 'Teacher', 'description': 'A teacher in the school', 'is_system_role': True},
        {'name': 'Student', 'description': 'A student in the school', 'is_system_role': True},
        {'name': 'Parent', 'description': 'A parent or guardian of a student', 'is_system_role': True}
    ])


def downgrade() -> None:
    # Delete the initial roles
    op.execute("DELETE FROM roles WHERE name IN ('Admin', 'Teacher', 'Student', 'Parent')")
