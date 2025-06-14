"""Create initial database schema

Revision ID: 7fa4d44500d9
Revises: 
Create Date: 2025-06-14 02:47:22.674533

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# Import the Base and all models to ensure they are registered with the metadata
from database import Base
from models import (
    school, user, student, teacher, academic, attendance,
    assessment, fee, communication, timetable, admission
)

# revision identifiers, used by Alembic.
revision: str = '7fa4d44500d9'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create all tables based on the models' metadata
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    # Drop all tables
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
