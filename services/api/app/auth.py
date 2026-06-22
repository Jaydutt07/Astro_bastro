from __future__ import annotations

from fastapi import Header

from .config import settings


def current_user_id(x_user_id: str | None = Header(default=None), authorization: str | None = Header(default=None)) -> str:
    if x_user_id:
        return x_user_id[:120]
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        if token:
            return token[:120]
    return settings.local_demo_user_id
