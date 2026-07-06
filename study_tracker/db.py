"""Database engine and session helpers (SQLModel / SQLAlchemy)."""

from __future__ import annotations

from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine

from study_tracker.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)


@contextmanager
def get_session():
    with Session(engine) as session:
        yield session


def create_tables() -> None:
    SQLModel.metadata.create_all(engine)