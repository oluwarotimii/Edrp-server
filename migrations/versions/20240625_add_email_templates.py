"""Add email templates and sent emails tables

Revision ID: 20240625_add_email_templates
Revises: 20240625_add_subscription_models
Create Date: 2024-06-25 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20240625_add_email_templates'
down_revision = '20240625_add_subscription_models'
branch_labels = None
depends_on = None

def upgrade():
    # Create email_templates table
    op.create_table(
        'email_templates',
        sa.Column('id', sa.String(50), primary_key=True, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('subject', sa.String(255), nullable=False),
        sa.Column('body', sa.Text, nullable=False),
        sa.Column('template_type', sa.Enum(
            'trial_started',
            'trial_ending_soon',
            'subscription_confirmation',
            'payment_failed',
            'payment_received',
            'subscription_cancelled',
            'password_reset',
            'welcome_email',
            'custom',
            name='email_template_type'
        ), nullable=False, server_default='custom'),
        sa.Column('variables', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.String(50), nullable=True),
        sa.UniqueConstraint('name', name='uq_email_template_name'),
        comment='Stores email templates for various system events'
    )

    # Create sent_emails table
    op.create_table(
        'sent_emails',
        sa.Column('id', sa.String(50), primary_key=True, index=True),
        sa.Column('template_id', sa.String(50), sa.ForeignKey('email_templates.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('recipient_email', sa.String(255), nullable=False, index=True),
        sa.Column('subject', sa.String(255), nullable=False),
        sa.Column('body', sa.Text, nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='sent', index=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, index=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True, server_default='{}'),
        comment='Logs of all sent emails for auditing and tracking'
    )

    # Create indexes for better query performance
    op.create_index('idx_sent_emails_recipient_status', 'sent_emails', ['recipient_email', 'status'])
    op.create_index('idx_sent_emails_sent_at', 'sent_emails', ['sent_at'])
    op.create_index('idx_email_templates_type_active', 'email_templates', ['template_type', 'is_active'])

def downgrade():
    # Drop indexes first
    op.drop_index('idx_sent_emails_recipient_status', table_name='sent_emails')
    op.drop_index('idx_sent_emails_sent_at', table_name='sent_emails')
    op.drop_index('idx_email_templates_type_active', table_name='email_templates')
    
    # Drop tables
    op.drop_table('sent_emails')
    op.drop_table('email_templates')
    
    # Drop the enum type
    op.execute("DROP TYPE email_template_type")
