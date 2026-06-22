from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


class ProfileRecord(Base):
    __tablename__ = "profiles"

    user_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    profile_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class ReadingRecord(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(120), index=True)
    reading_date: Mapped[str] = mapped_column(String(20), index=True)
    intent: Mapped[str] = mapped_column(String(40), default="daily")
    reading_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))


class PurchaseRecord(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(120), index=True)
    product_id: Mapped[str] = mapped_column(String(120))
    report_kind: Mapped[str] = mapped_column(String(40))
    unlocked: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_response: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_session():
    with SessionLocal() as session:
        yield session


def get_profile(session: Session, user_id: str) -> ProfileRecord | None:
    return session.scalar(select(ProfileRecord).where(ProfileRecord.user_id == user_id))
