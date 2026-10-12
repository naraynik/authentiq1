"""002_web_frontend_fields: product SKU/facility/distributors/block + customer issues

Revision ID: 002_web_frontend_fields
Revises: 001_initial_schema
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002_web_frontend_fields"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Written to be idempotent: the app also adds these on startup (app/database/upgrade.py).
    insp = sa.inspect(op.get_bind())
    cols = {c["name"] for c in insp.get_columns("products")}
    if "sku" not in cols:
        op.add_column("products", sa.Column("sku", sa.String(), nullable=True))
    if "facility" not in cols:
        op.add_column("products", sa.Column("facility", sa.JSON(), nullable=True))
    if "distributors" not in cols:
        op.add_column("products", sa.Column("distributors", sa.JSON(), nullable=True))
    if "registration_block" not in cols:
        op.add_column("products", sa.Column("registration_block", sa.Integer(), nullable=True))
    if "issues" not in insp.get_table_names():
        op.create_table(
            "issues",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("product_id", sa.String(), nullable=False, index=True),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("contact", sa.String(), nullable=True),
            sa.Column("latitude", sa.Float(), nullable=True),
            sa.Column("longitude", sa.Float(), nullable=True),
            sa.Column("status", sa.String(), nullable=False, server_default="OPEN"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )


def downgrade() -> None:
    op.drop_table("issues")
    for c in ("registration_block", "distributors", "facility", "sku"):
        op.drop_column("products", c)
