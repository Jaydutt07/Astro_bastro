from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from astro_core import BirthProfile, ReadingResponse, build_chart_snapshot
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .auth import current_user_id
from .db import ProfileRecord, PurchaseRecord, ReadingRecord, get_profile, get_session, init_db
from .places import PlaceResult, search_places
from .quality import QualityReport, evaluate_quality
from .reading import render_reading
from .revenuecat import validate_purchase
from .safety import reject_unsafe_question

app = FastAPI(
    title="Trust Astro API",
    version="0.1.0",
    description="Privacy-forward Vedic astrology API. Deterministic chart math is the source of truth; GPT renders prose.",
)
init_db()


class AskRequest(BaseModel):
    question: str = Field(min_length=4, max_length=500)


class FeedbackRequest(BaseModel):
    reading_id: int | None = Field(default=None, alias="readingId")
    rating: int = Field(ge=1, le=5)
    note: str | None = Field(default=None, max_length=1000)


class PurchaseRequest(BaseModel):
    report_kind: str = Field(alias="reportKind", pattern="^(love|career|yearly)$")
    product_id: str = Field(alias="productId")
    app_user_id: str = Field(alias="appUserId")
    receipt_token: str = Field(alias="receiptToken")


class PlaceSearchResponse(BaseModel):
    results: list[PlaceResult]


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
    profile = _load_profile(session, user_id)
    today = datetime.now(ZoneInfo(profile.timezone)).date().isoformat()
    cached = session.scalar(
        select(ReadingRecord).where(
            ReadingRecord.user_id == user_id,
            ReadingRecord.reading_date == today,
            ReadingRecord.intent == "daily",
        )
    )
    if cached:
        return ReadingResponse.model_validate_json(cached.reading_json)

    chart = build_chart_snapshot(profile)
    reading = await render_reading(chart, intent="daily")
    session.add(
        ReadingRecord(
            user_id=user_id,
            reading_date=today,
            intent="daily",
            reading_json=reading.model_dump_json(by_alias=True),
        )
    )
    session.commit()
    return reading


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
    return await render_reading(chart, intent="ask", question=payload.question)


@app.post("/reports/purchase")
async def purchase_report(
    payload: PurchaseRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(current_user_id),
):
    profile = _load_profile(session, user_id)
    unlocked, raw = await validate_purchase(payload.app_user_id, payload.product_id, payload.receipt_token)
    chart = build_chart_snapshot(profile)
    report = await render_reading(chart, intent=payload.report_kind)
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
    session.execute(delete(PurchaseRecord).where(PurchaseRecord.user_id == user_id))
    session.commit()
    return {"status": "deleted"}


def _load_profile(session: Session, user_id: str) -> BirthProfile:
    record = get_profile(session, user_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Create a birth profile first.")
    return BirthProfile.model_validate_json(record.profile_json)
