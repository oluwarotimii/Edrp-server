"""merge bcddb5beb96e and fix_roles_seeding

Revision ID: c72f809b6cac
Revises: bcddb5beb96e, fix_roles_seeding
Create Date: 2025-06-25 14:40:08.205220

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c72f809b6cac'
down_revision: Union[str, None] = ('bcddb5beb96e', 'fix_roles_seeding')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
