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
down_revision: Union[str, None] = 'd8a9a4b1c2d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This migration is now a placeholder and does nothing
    pass


def downgrade() -> None:
    # Delete the initial roles
    op.execute("DELETE FROM roles WHERE name IN ('Admin', 'Teacher', 'Student', 'Parent')")
