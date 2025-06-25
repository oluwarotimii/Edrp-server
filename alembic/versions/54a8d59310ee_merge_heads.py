"""Merge heads

Revision ID: 54a8d59310ee
Revises: add_subdomain_to_schools, c72f809b6cac
Create Date: 2025-06-25 18:37:17.063435

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54a8d59310ee'
down_revision: Union[str, None] = ('add_subdomain_to_schools', 'c72f809b6cac')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
