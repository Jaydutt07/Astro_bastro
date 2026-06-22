# Trust Astro API

FastAPI backend for the Vedic astrology MVP. The deterministic chart engine lives in
`packages/astro-core`; OpenAI is used only to render structured prose from chart facts.

## Local Run

```bash
PYTHONPATH=packages/astro-core:services/api python -m uvicorn app.main:app --app-dir services/api --reload
```

Optional environment variables:

- `OPENAI_API_KEY`: enables GPT-rendered readings.
- `OPENAI_MODEL`: defaults to `gpt-4.1-mini`.
- `REVENUECAT_API_KEY`: enables live RevenueCat validation.
- `DATABASE_URL`: defaults to local SQLite at `services/api/trust_astro.db`.
- `TRUST_ASTRO_EPHEMERIS_DIR`: stores Skyfield/JPL ephemeris files outside the repo.

Without paid-service keys, endpoints stay runnable and return deterministic demo output.

## Accuracy Path

The astrology core uses Skyfield/JPL DE421 geocentric ecliptic longitudes when
`skyfield` is installed and the ephemeris can be loaded. If that fails in local
development, it falls back to compact orbital calculations and marks the chart's
`calculationEngine` accordingly.

## Quality Evaluation

```bash
PYTHONPATH=packages/astro-core:services/api python services/api/scripts/evaluate_reading_quality.py
```

The report scores specificity, chart evidence, safety, and tone across curated
birth profiles.

## Docker

```bash
docker build -f services/api/Dockerfile -t trust-astro-api .
docker run --rm -p 8000:8000 --env-file services/api/.env.example trust-astro-api
```
