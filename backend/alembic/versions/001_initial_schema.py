"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-08 15:37:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. Create manufacturers table
    op.create_table(
        'manufacturers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(), nullable=False),
        sa.Column('gstin', sa.String(), nullable=False),
        sa.Column('company_address', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=False),
        sa.Column('verification_document_path', sa.String(), nullable=False),
        sa.Column('verification_status', sa.String(), nullable=False, server_default='PENDING'),
        sa.Column('verified_by', sa.Integer(), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['verified_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_manufacturers_id'), 'manufacturers', ['id'], unique=False)
    op.create_index(op.f('ix_manufacturers_gstin'), 'manufacturers', ['gstin'], unique=True)

    # 3. Create products table
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.String(), nullable=False),
        sa.Column('manufacturer_id', sa.Integer(), nullable=False),
        sa.Column('manufacturer_name', sa.String(), nullable=False),
        sa.Column('product_name', sa.String(), nullable=False),
        sa.Column('batch_number', sa.String(), nullable=False),
        sa.Column('manufacturing_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expiry_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('product_hash', sa.String(), nullable=False),
        sa.Column('current_location', sa.String(), nullable=False),
        sa.Column('next_location', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='GENUINE'),
        sa.Column('is_onchain', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('registration_tx_hash', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['manufacturer_id'], ['manufacturers.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)
    op.create_index(op.f('ix_products_product_id'), 'products', ['product_id'], unique=True)

    # 4. Create scan_history table
    op.create_table(
        'scan_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.String(), nullable=False),
        sa.Column('scanned_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('location', sa.String(), nullable=False),
        sa.Column('device_id', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('scan_velocity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('hours_since_creation', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('authenticity_probability', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('anomaly_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('ai_verdict', sa.String(), nullable=True),
        sa.Column('blockchain_verdict', sa.String(), nullable=True),
        sa.Column('final_verdict', sa.String(), nullable=False),
        sa.Column('flags', sa.Text(), nullable=True),
        sa.Column('raw_scan_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.product_id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scan_history_id'), 'scan_history', ['id'], unique=False)
    op.create_index(op.f('ix_scan_history_product_id'), 'scan_history', ['product_id'], unique=False)
    op.create_index(op.f('ix_scan_history_scanned_at'), 'scan_history', ['scanned_at'], unique=False)

    # 5. Create location_history table
    op.create_table(
        'location_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.String(), nullable=False),
        sa.Column('location_name', sa.String(), nullable=False),
        sa.Column('details', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=False),
        sa.Column('transaction_hash', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.product_id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_location_history_id'), 'location_history', ['id'], unique=False)
    op.create_index(op.f('ix_location_history_product_id'), 'location_history', ['product_id'], unique=False)

    # 6. Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)

def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('location_history')
    op.drop_table('scan_history')
    op.drop_table('products')
    op.drop_table('manufacturers')
    op.drop_table('users')
