"""Add subscription models

Revision ID: 20240625_add_subscription_models
Revises: 
Create Date: 2024-06-25 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20240625_add_subscription_models'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create subscription_plans table
    op.create_table(
        'subscription_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price_monthly', sa.Float(), nullable=False),
        sa.Column('price_yearly', sa.Float(), nullable=True),
        sa.Column('max_students', sa.Integer(), nullable=False),
        sa.Column('max_teachers', sa.Integer(), nullable=False),
        sa.Column('max_storage_mb', sa.Integer(), nullable=False, server_default='1024'),
        sa.Column('features', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('paystack_plan_code', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_default', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('paystack_plan_code')
    )

    # Update school_subscriptions table
    op.add_column('school_subscriptions', sa.Column('status', sa.String(length=20), server_default='active', nullable=False))
    op.add_column('school_subscriptions', sa.Column('auto_renew', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('school_subscriptions', sa.Column('paystack_subscription_code', sa.String(length=100), nullable=True))
    op.add_column('school_subscriptions', sa.Column('paystack_customer_code', sa.String(length=100), nullable=True))
    op.add_column('school_subscriptions', sa.Column('payment_method', sa.String(length=50), nullable=True))
    
    # Add plan_id column without foreign key constraint first
    op.add_column('school_subscriptions', sa.Column('plan_id', sa.Integer(), nullable=True))
    
    # Create a default plan if none exists
    op.execute("""
        INSERT INTO subscription_plans 
        (name, description, price_monthly, price_yearly, max_students, max_teachers, max_storage_mb, is_default, is_active)
        SELECT 'Free', 'Free plan with basic features', 0, 0, 50, 5, 1024, true, true
        WHERE NOT EXISTS (SELECT 1 FROM subscription_plans WHERE is_default = true)
    """)
    
    # Set default plan_id for existing subscriptions
    op.execute("""
        UPDATE school_subscriptions 
        SET plan_id = (SELECT id FROM subscription_plans WHERE is_default = true LIMIT 1)
        WHERE plan_id IS NULL
    """)
    
    # Now that we've set default values, make the column non-nullable
    op.alter_column('school_subscriptions', 'plan_id', nullable=False)
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_school_subscription_plan',
        'school_subscriptions', 'subscription_plans',
        ['plan_id'], ['id'], ondelete='RESTRICT'
    )
    
    # Drop old columns that we've replaced
    op.drop_column('school_subscriptions', 'plan_name')
    op.drop_column('school_subscriptions', 'max_students')
    op.drop_column('school_subscriptions', 'max_teachers')
    op.drop_column('school_subscriptions', 'features')

def downgrade():
    # Re-add old columns
    op.add_column('school_subscriptions', sa.Column('plan_name', sa.VARCHAR(length=100), autoincrement=False, nullable=False))
    op.add_column('school_subscriptions', sa.Column('max_students', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('school_subscriptions', sa.Column('max_teachers', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('school_subscriptions', sa.Column('features', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), autoincrement=False, nullable=True))
    
    # Set default values for the old columns
    op.execute("""
        UPDATE school_subscriptions s
        SET 
            plan_name = p.name,
            max_students = p.max_students,
            max_teachers = p.max_teachers,
            features = p.features
        FROM subscription_plans p
        WHERE s.plan_id = p.id
    """)
    
    # Drop foreign key and columns
    op.drop_constraint('fk_school_subscription_plan', 'school_subscriptions', type_='foreignkey')
    op.drop_column('school_subscriptions', 'plan_id')
    op.drop_column('school_subscriptions', 'status')
    op.drop_column('school_subscriptions', 'auto_renew')
    op.drop_column('school_subscriptions', 'paystack_subscription_code')
    op.drop_column('school_subscriptions', 'paystack_customer_code')
    op.drop_column('school_subscriptions', 'payment_method')
    
    # Drop subscription_plans table
    op.drop_table('subscription_plans')
