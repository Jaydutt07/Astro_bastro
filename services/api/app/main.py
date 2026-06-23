from __future__ import annotations

import json
from datetime import date, datetime
from zoneinfo import ZoneInfo

from astro_core import BirthProfile, EntitlementStatus, HarmonyResponse, ProblemInsightResponse, ReadingResponse, build_chart_snapshot, build_harmony_insight
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from .auth import current_user_id
from .db import (
    ProblemRecord,
    ProfileRecord,
    PurchaseRecord,
    ReadingRecord,
    UserMemoryRecord,
    get_profile,
    get_session,
    init_db,
    memory_context,
    remember_problem,
)
from .places import PlaceResult, search_places
from .quality import QualityReport, evaluate_quality
from .reading import render_problem_insight, render_reading
from .revenuecat import validate_purchase
from .safety import reject_unsafe_question

app = FastAPI(
    title="Astro Solves API",
    version="0.1.0",
    description="Problem-solving Vedic astrology API. Deterministic chart math is the source of truth; private model rendering writes prose.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:19006",
        "http://127.0.0.1:19006",
        "http://localhost:8081",
        "http://127.0.0.1:8081",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
init_db()

READING_PERIODS = {"daily", "weekly", "monthly", "yearly"}
DAILY_READING_FREE_LIMIT = 1
PROBLEM_FREE_LIMIT = 2


class AskRequest(BaseModel):
    question: str = Field(min_length=4, max_length=500)


class ProblemRequest(BaseModel):
    category: str = Field(default="shani", pattern="^(shani|relationship|career|money|family|health-stress|other)$")
    problem_details: str = Field(alias="problemDetails", min_length=10, max_length=1500)


class HarmonyRequest(BaseModel):
    partner_name: str = Field(default="Partner", alias="partnerName", min_length=2, max_length=120)
    partner_birth_date: date | None = Field(default=None, alias="partnerBirthDate")
    relationship_focus: str = Field(default="relationship", alias="relationshipFocus", pattern="^(relationship|marriage|peace)$")


class FeedbackRequest(BaseModel):
    reading_id: int | None = Field(default=None, alias="readingId")
    rating: int = Field(ge=1, le=5)
    note: str | None = Field(default=None, max_length=1000)


class PurchaseRequest(BaseModel):
    report_kind: str = Field(alias="reportKind", pattern="^(love|career|yearly)$")
    product_id: str = Field(alias="productId")
    app_user_id: str = Field(alias="appUserId")
    receipt_token: str = Field(alias="receiptToken")


class SolutionUnlockRequest(BaseModel):
    product_id: str = Field(alias="productId")
    app_user_id: str = Field(alias="appUserId")
    receipt_token: str = Field(alias="receiptToken")
    category: str = Field(default="shani", pattern="^(shani|relationship|career|money|family|health-stress|other)$")
    problem_details: str = Field(default="Unlock deeper remedy support.", alias="problemDetails", max_length=1500)


class PlaceSearchResponse(BaseModel):
    results: list[PlaceResult]


class MemoryContextResponse(BaseModel):
    memory: dict


class EntitlementsResponse(BaseModel):
    reading: EntitlementStatus
    problem: EntitlementStatus


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/places/search", response_model=PlaceSearchResponse)
async def places(q: str, limit: int = 6) -> PlaceSearchResponse:
    return PlaceSearchResponse(results=await search_places(q, limit=max(1, min(limit, 8))))


@app.post("/profile", response_model=BirthProfile)
def save_profile(
    profile: BirthProfile,
    session: Session = Depends(get_session),
    user_id: str = Depends(current_user_id),
) -> BirthProfile:
    if not profile.consent.privacy_accepted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Privacy consent is required.")
    record = get_profile(session, user_id)
    payload = profile.model_dump_json(by_alias=True)
    if record:
        record.profile_json = payload
    else:
        session.add(ProfileRecord(user_id=user_id, profile_json=payload))
    session.commit()
    return profile


@app.get("/chart/natal")
def natal_chart(
    session: Session = Depends(get_session),
    user_id: str = Depends(current_user_id),
):
    profile = _load_profile(session, user_id)
    return build_chart_snapshot(profile)


@app.get("/reading/daily", response_model=ReadingResponse)
async def daily_reading(
    session: Session = Depends(get_session),
    user_id: str = Depends(current_user_id),
) -> ReadingResponse:
    return await _period_reading("daily", session, user_id)


@app.get("/reading/{period}", response_model=ReadingResponse)
async def period_reading(
    period: str,
    session: Session = Depends(get_session),
    user_id: str = Depends(current_user_id),
) -> ReadingResponse:
    if period not in READING_PERIODS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reading period must be daily, weekly, monthly, or yearly.")
    return await _period_reading(period, session, user_id)


async def _period_reading(period: str, session: Session, user_id: str) -> ReadingResponse:
    profile = _load_profile(session, user_id)
    today = _profile_today(profile)
    cached = session.scalar(
        select(ReadingRecord).where(
            ReadingRecord.user_id == user_id,
            ReadingRecord.reading_date == today,
            ReadingRecord.intent == period,
        )
    )
    if cached:
        return ReadingResponse.model_validate_json(cached.reading_json).model_copy(
            update={"entitlement": _reading_entitlement(session, user_id, today)}
        )

    used_period = session.scalar(
        select(ReadingRecord.intent).where(
            ReadingRecord.user_id == user_id,
            ReadingRecord.reading_date == today,
            ReadingRecord.intent.in_(READING_PERIODS),
        )
    )
    if used_period:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"Today's free reading is already used for {used_period}. "
                "Extra period readings are part of the paid plan."
            ),
        )

    chart = build_chart_snapshot(profile)
    context = memory_context(session, user_id) if profile.consent.ai_personalization else None
    reading = await render_reading(chart, intent=period, memory_context=context)
    session.add(
        ReadingRecord(
            user_id=user_id,
            reading_date=today,
            intent=period,
            reading_json=reading.model_dump_json(by_alias=True),
        )
    )
    session.commit()
    return reading.model_copy(update={"entitlement": _reading_entitlement(session, user_id, today)})


@app.post("/ask", response_model=ReadingResponse)
async def ask(
    payload: AskRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(current_user_id),
) -> ReadingResponse:
    try:
        reject_unsafe_question(payload.question)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    profile = _load_profile(session, user_id)
    chart = build_chart_snapshot(profile)
    context = memory_context(session, user_id) if profile.consent.ai_personalization else None
    reading = await render_reading(chart, intent="ask", question=payload.question, memory_context=context)
    if profile.consent.ai_personalization:
        reading_json = reading.model_dump_json(by_alias=True)
        session.add(
            ProblemRecord(
                user_id=user_id,
                category="ask",
                problem_text=payload.question,
                insight_json=reading_json,
            )
        )
        remember_problem(session, user_id, "ask", payload.question, reading_json)
        session.commit()
    return reading


@app.post("/problem/insight", response_model=ProblemInsightResponse)
async def problem_insight(
    payload: ProblemRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(current_user_id),
) -> ProblemInsightResponse:
    try:
        reject_unsafe_question(payload.problem_details)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    profile = _load_profile(session, user_id)
    used_before = _problem_usage_count(session, user_id)
    if used_before >= PROBLEM_FREE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Your two free problem analyses are used. Deeper problem maps and remedy packs are part of the paid plan.",
        )
    chart = build_chart_snapshot(profile)
    context = memory_context(session, user_id) if profile.consent.ai_personalization else None
    insight = await render_problem_insight(
        chart,
        category=payload.category,
        problem_text=payload.problem_details,
        memory_context=context,
    )
    insight = insight.model_copy(
        update={
            "entitlement": _entitlement_status(
                free_limit=PROBLEM_FREE_LIMIT,
                free_used=used_before + 1,
                message=_problem_entitlement_message(used_before + 1),
            )
        }
    )
    insight_json = insight.model_dump_json(by_alias=True)
    session.add(
        ProblemRecord(
            user_id=user_id,
            category=payload.category,
            problem_text=payload.problem_details if profile.consent.ai_personalization else "[not stored by personalization choice]",
            insight_json=insight_json,
        )
    )
    if profile.consent.ai_personalization:
        remember_problem(session, user_id, payload.category, payload.problem_details, insight_json)
    session.commit()
    return insight


@app.post("/harmony/insight", response_model=HarmonyResponse)
def harmony_insight(
    payload: HarmonyRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(current_user_id),
) -> HarmonyResponse:
    profile = _load_profile(session, user_id)
    chart = build_chart_snapshot(profile)
    return build_harmony_insight(
        chart,
        partner_name=payload.partner_name,
        partner_birth_date=payload.partner_birth_date,
        relationship_focus=payload.relationship_focus,
    )


@app.post("/reports/purchase")
async def purchase_report(
    payload: PurchaseRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(current_user_id),
):
    profile = _load_profile(session, user_id)
    unlocked, raw = await validate_purchase(payload.app_user_id, payload.product_id, payload.receipt_token)
    chart = build_chart_snapshot(profile)
    context = memory_context(session, user_id) if profile.consent.ai_personalization else None
    report = await render_reading(chart, intent=payload.report_kind, memory_context=context)
    session.add(
        PurchaseRecord(
            user_id=user_id,
            product_id=payload.product_id,
            report_kind=payload.report_kind,
            unlocked=unlocked,
            raw_response=json.dumps(raw),
        )
    )
    session.commit()
    return {"status": "unlocked" if unlocked else "pending", "unlocked": unlocked, "report": report}


@app.post("/solutions/unlock")
async def unlock_solutions(
    payload: SolutionUnlockRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(current_user_id),
):
    profile = _load_profile(session, user_id)
    unlocked, raw = await validate_purchase(payload.app_user_id, payload.product_id, payload.receipt_token)
    chart = build_chart_snapshot(profile)
    context = memory_context(session, user_id) if profile.consent.ai_personalization else None
    insight = await render_problem_insight(
        chart,
        category=payload.category,
        problem_text=payload.problem_details,
        memory_context=context,
    )
    session.add(
        PurchaseRecord(
            user_id=user_id,
            product_id=payload.product_id,
            report_kind="solutions",
            unlocked=unlocked,
            raw_response=json.dumps(raw),
        )
    )
    session.commit()
    return {
        "status": "unlocked" if unlocked else "pending",
        "unlocked": unlocked,
        "solutionPack": insight.premium_solutions,
        "message": "Premium solution practices unlocked." if unlocked else "Subscription verification is pending.",
    }


@app.get("/memory/context", response_model=MemoryContextResponse)
def user_memory_context(
    session: Session = Depends(get_session),
    user_id: str = Depends(current_user_id),
) -> MemoryContextResponse:
    return MemoryContextResponse(memory=memory_context(session, user_id))


@app.get("/entitlements", response_model=EntitlementsResponse)
def entitlements(
    session: Session = Depends(get_session),
    user_id: str = Depends(current_user_id),
) -> EntitlementsResponse:
    profile = _load_profile(session, user_id)
    today = _profile_today(profile)
    return EntitlementsResponse(
        reading=_reading_entitlement(session, user_id, today),
        problem=_problem_entitlement(session, user_id),
    )


@app.post("/feedback")
def feedback(payload: FeedbackRequest) -> dict[str, str]:
    return {"status": "received"}


@app.get("/quality/evaluate", response_model=QualityReport)
def quality_evaluate() -> QualityReport:
    return evaluate_quality()


@app.delete("/account")
def delete_account(
    session: Session = Depends(get_session),
    user_id: str = Depends(current_user_id),
) -> dict[str, str]:
    session.execute(delete(ProfileRecord).where(ProfileRecord.user_id == user_id))
    session.execute(delete(ReadingRecord).where(ReadingRecord.user_id == user_id))
    session.execute(delete(ProblemRecord).where(ProblemRecord.user_id == user_id))
    session.execute(delete(UserMemoryRecord).where(UserMemoryRecord.user_id == user_id))
    session.execute(delete(PurchaseRecord).where(PurchaseRecord.user_id == user_id))
    session.commit()
    return {"status": "deleted"}


def _load_profile(session: Session, user_id: str) -> BirthProfile:
    record = get_profile(session, user_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Create a birth profile first.")
    return BirthProfile.model_validate_json(record.profile_json)


def _profile_today(profile: BirthProfile) -> str:
    return datetime.now(ZoneInfo(profile.timezone)).date().isoformat()


def _reading_entitlement(session: Session, user_id: str, today: str) -> EntitlementStatus:
    used_periods = list(
        session.scalars(
            select(ReadingRecord.intent)
            .where(
                ReadingRecord.user_id == user_id,
                ReadingRecord.reading_date == today,
                ReadingRecord.intent.in_(READING_PERIODS),
            )
            .distinct()
        )
    )
    used = min(DAILY_READING_FREE_LIMIT, len(used_periods))
    if used_periods:
        message = (
            f"Free reading used for {used_periods[0]}. "
            "Choose again tomorrow or use the paid plan for extra period readings."
        )
    else:
        message = "Choose one free period reading today: daily, weekly, monthly, or yearly."
    return _entitlement_status(free_limit=DAILY_READING_FREE_LIMIT, free_used=used, message=message)


def _problem_entitlement(session: Session, user_id: str) -> EntitlementStatus:
    used = _problem_usage_count(session, user_id)
    return _entitlement_status(
        free_limit=PROBLEM_FREE_LIMIT,
        free_used=used,
        message=_problem_entitlement_message(used),
    )


def _problem_usage_count(session: Session, user_id: str) -> int:
    count = session.scalar(
        select(func.count(ProblemRecord.id)).where(
            ProblemRecord.user_id == user_id,
            ProblemRecord.category != "ask",
        )
    )
    return int(count or 0)


def _problem_entitlement_message(used: int) -> str:
    remaining = max(0, PROBLEM_FREE_LIMIT - used)
    if remaining == 1:
        return "1 free problem analysis left."
    if remaining:
        return f"{remaining} free problem analyses left."
    return "Your two free problem analyses are used. Paid plans can open deeper maps and remedy packs."


def _entitlement_status(*, free_limit: int, free_used: int, message: str) -> EntitlementStatus:
    free_used = min(free_limit, max(0, free_used))
    return EntitlementStatus.model_validate(
        {
            "access": "free",
            "freeLimit": free_limit,
            "freeUsed": free_used,
            "freeRemaining": max(0, free_limit - free_used),
            "message": message,
        }
    )
