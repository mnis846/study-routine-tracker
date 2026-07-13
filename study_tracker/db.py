"""Database engine and session helpers (SQLModel / SQLAlchemy)."""

from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from study_tracker.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)


@contextmanager
def get_session():
    with Session(engine) as session:
        yield session


def _appsetting_has_broken_id_column() -> bool:
    inspector = inspect(engine)
    if "appsetting" not in inspector.get_table_names():
        return False
    columns = {col["name"] for col in inspector.get_columns("appsetting")}
    return "id" in columns


def repair_schema() -> None:
    """Fix legacy Alembic schema where appsetting.id breaks inserts."""
    if not _appsetting_has_broken_id_column():
        return

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE appsetting_new (
                    user_id INTEGER NOT NULL,
                    "key" VARCHAR NOT NULL,
                    value VARCHAR NOT NULL,
                    PRIMARY KEY (user_id, "key"),
                    FOREIGN KEY(user_id) REFERENCES user(id)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO appsetting_new (user_id, "key", value)
                SELECT user_id, "key", value FROM appsetting
                """
            )
        )
        conn.execute(text("DROP TABLE appsetting"))
        conn.execute(text("ALTER TABLE appsetting_new RENAME TO appsetting"))


def create_tables() -> None:
    repair_schema()
    SQLModel.metadata.create_all(engine)