"""Make school_id on roles nullable

Revision ID: d8a9a4b1c2d0
Revises: bcddb5beb96e
Create Date: 2025-06-14 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd8a9a4b1c2d0'
down_revision = 'bcddb5beb96e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('roles', 'school_id',
               existing_type=sa.INTEGER(),
               nullable=True)


def downgrade() -> None:
    op.alter_column('roles', 'school_id',
               existing_type=sa.INTEGER(),
               nullable=False)
