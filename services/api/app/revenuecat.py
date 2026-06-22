from __future__ import annotations

import json
from typing import Any

import httpx

from .config import settings


async def validate_purchase(app_user_id: str, product_id: str, receipt_token: str) -> tuple[bool, dict[str, Any]]:
    if not settings.revenuecat_api_key:
        return True, {"mode": "local-demo", "productId": product_id, "appUserId": app_user_id}

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            f"https://api.revenuecat.com/v1/subscribers/{app_user_id}",
            headers={"Authorization": f"Bearer {settings.revenuecat_api_key}"},
        )
        response.raise_for_status()
        payload = response.json()

    serialized = json.dumps(payload)
    return product_id in serialized or receipt_token in serialized, payload
