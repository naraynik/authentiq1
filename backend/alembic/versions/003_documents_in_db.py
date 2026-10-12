"""003_documents_in_db: Aadhaar file stored in the database + app_state table

Revision ID: 003_documents_in_db
Revises: 002_web_frontend_fields
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003_documents_in_db"
down_revision: Union[str, None] = "002_web_frontend_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    cols = {c["name"] for c in insp.get_columns("manufacturers")}
    if "verification_document" not in cols:
        op.add_column("manufacturers", sa.Column("verification_document", sa.LargeBinary(), nullable=True))
    if "verification_document_type" not in cols:
        op.add_column("manufacturers", sa.Column("verification_document_type", sa.String(), nullable=True))
    if "app_state" not in insp.get_table_names():
        op.create_table(
            "app_state",
            sa.Column("key", sa.String(), primary_key=True),
            sa.Column("value", sa.Text(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )


def downgrade() -> None:
    op.drop_table("app_state")
    op.drop_column("manufacturers", "verification_document_type")
    op.drop_column("manufacturers", "verification_document")
