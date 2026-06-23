from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional during minimal installs
    load_dotenv = None


if load_dotenv:
    project_root = Path(__file__).resolve().parents[3]
    load_dotenv(project_root / ".env", override=False)
    load_dotenv(project_root / "services" / "api" / ".env", override=False)
else:
    project_root = Path(__file__).resolve().parents[3]

    def _load_env_file(path: Path) -> None:
        if not path.exists():
            return
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

    _load_env_file(project_root / ".env")
    _load_env_file(project_root / "services" / "api" / ".env")


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off"}


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///services/api/astro_solves.db")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5.5")
    openai_reasoning_effort: str = os.getenv("OPENAI_REASONING_EFFORT", "low")
    openai_verbosity: str = os.getenv("OPENAI_VERBOSITY", "low")
    openai_reading_max_output_tokens: int = max(450, _env_int("OPENAI_READING_MAX_OUTPUT_TOKENS", 900))
    openai_problem_max_output_tokens: int = max(900, _env_int("OPENAI_PROBLEM_MAX_OUTPUT_TOKENS", 1500))
    openai_verify_ssl: bool = _env_bool("OPENAI_VERIFY_SSL", True)
    openai_ca_bundle: str | None = os.getenv("OPENAI_CA_BUNDLE") or None
    openai_timeout_seconds: float = _env_float("OPENAI_TIMEOUT_SECONDS", 90.0)
    openai_max_attempts: int = max(1, _env_int("OPENAI_MAX_ATTEMPTS", 2))
    revenuecat_api_key: str | None = os.getenv("REVENUECAT_API_KEY")
    revenuecat_project_id: str | None = os.getenv("REVENUECAT_PROJECT_ID")
    local_demo_user_id: str = os.getenv("LOCAL_DEMO_USER_ID", "demo-user")


settings = Settings()
