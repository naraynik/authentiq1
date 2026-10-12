"""Idempotent schema top-up for databases created by an older version.

Base.metadata.create_all() creates missing tables but never adds columns to an
existing table, so this adds the newer nullable columns if they are missing.
Safe to run on every start (SQLite and PostgreSQL). Alembic users can run
`alembic upgrade head` instead (migrations 002 and 003 do the same thing).
"""
import logging
from sqlalchemy import JSON, Integer, LargeBinary, String, inspect, text

logger = logging.getLogger(__name__)

NEW_COLUMNS = {
    "products": {
        "sku": String(),
        "facility": JSON(),
        "distributors": JSON(),
        "registration_block": Integer(),
    },
    "manufacturers": {
        "verification_document": LargeBinary(),
        "verification_document_type": String(),
    },
}


def ensure_new_columns(engine) -> None:
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    with engine.begin() as conn:
        for table, columns in NEW_COLUMNS.items():
            if table not in tables:
                continue
            existing = {c["name"] for c in insp.get_columns(table)}
            for name, sql_type in columns.items():
                if name not in existing:
                    type_sql = sql_type.compile(dialect=engine.dialect)
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {type_sql}"))
                    logger.info("Added column %s.%s", table, name)
