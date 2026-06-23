from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

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


class ProblemRecord(Base):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(120), index=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    problem_text: Mapped[str] = mapped_column(Text)
    insight_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))


class UserMemoryRecord(Base):
    __tablename__ = "user_memories"

    user_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    memory_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


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


def get_user_memory(session: Session, user_id: str) -> UserMemoryRecord | None:
    return session.scalar(select(UserMemoryRecord).where(UserMemoryRecord.user_id == user_id))


def memory_context(session: Session, user_id: str) -> dict[str, Any]:
    record = get_user_memory(session, user_id)
    if not record:
        return {"problemCount": 0, "recentProblems": [], "categoryCounts": {}, "solutionHistory": []}
    try:
        payload = json.loads(record.memory_json)
    except json.JSONDecodeError:
        payload = {}
    return {
        "problemCount": int(payload.get("problemCount", 0)),
        "recentProblems": list(payload.get("recentProblems", []))[-8:],
        "categoryCounts": dict(payload.get("categoryCounts", {})),
        "solutionHistory": list(payload.get("solutionHistory", []))[-8:],
        "lastUpdatedAt": payload.get("lastUpdatedAt"),
    }


def remember_problem(
    session: Session,
    user_id: str,
    category: str,
    problem_text: str,
    insight_json: str,
) -> dict[str, Any]:
    now = datetime.now(UTC).isoformat()
    record = get_user_memory(session, user_id)
    memory = memory_context(session, user_id)
    recent_problems = list(memory.get("recentProblems", []))
    category_counts = dict(memory.get("categoryCounts", {}))
    solution_history = list(memory.get("solutionHistory", []))

    try:
        insight = json.loads(insight_json)
    except json.JSONDecodeError:
        insight = {}

    category_counts[category] = int(category_counts.get(category, 0)) + 1
    recent_problems.append(
        {
            "category": category,
            "problemDetails": problem_text,
            "problemTitle": insight.get("problemTitle", ""),
            "createdAt": now,
        }
    )
    solution = insight.get("freeSolution") or {}
    if solution:
        solution_history.append(
            {
                "title": solution.get("title", ""),
                "duration": solution.get("duration", ""),
                "createdAt": now,
            }
        )

    updated = {
        "problemCount": int(memory.get("problemCount", 0)) + 1,
        "recentProblems": recent_problems[-8:],
        "categoryCounts": category_counts,
        "solutionHistory": solution_history[-8:],
        "lastUpdatedAt": now,
    }
    if record:
        record.memory_json = json.dumps(updated)
    else:
        session.add(UserMemoryRecord(user_id=user_id, memory_json=json.dumps(updated)))
    return updated
