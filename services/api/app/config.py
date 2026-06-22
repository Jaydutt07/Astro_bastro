from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///services/api/trust_astro.db")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    revenuecat_api_key: str | None = os.getenv("REVENUECAT_API_KEY")
    revenuecat_project_id: str | None = os.getenv("REVENUECAT_PROJECT_ID")
    local_demo_user_id: str = os.getenv("LOCAL_DEMO_USER_ID", "demo-user")


settings = Settings()
