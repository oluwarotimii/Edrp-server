"""Add subdomain to schools

Revision ID: add_subdomain_to_schools
Revises: bcddb5beb96e
Create Date: 2025-06-25 18:23:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_subdomain_to_schools'
down_revision = 'bcddb5beb96e'
branch_labels = None
depends_on = None

def upgrade():
    # Add subdomain column
    op.add_column('schools', sa.Column('subdomain', sa.String(63), nullable=True, unique=True))
    
    # Add index for faster lookups
    op.create_index(op.f('ix_schools_subdomain'), 'schools', ['subdomain'], unique=True)
    
    # For existing schools, generate subdomains based on their names
    # This is a simple example - you might want to make this more sophisticated
    op.execute("""
        UPDATE schools 
        SET subdomain = LOWER(REPLACE(REPLACE(REPLACE(name, ' ', '-'), '.', ''), '--', '-'))
        WHERE subdomain IS NULL
    """)
    
    # Make subdomain non-nullable after populating
    op.alter_column('schools', 'subdomain', nullable=False)

def downgrade():
    # Drop the index first
    op.drop_index(op.f('ix_schools_subdomain'), table_name='schools')
    
    # Then drop the column
    op.drop_column('schools', 'subdomain')
