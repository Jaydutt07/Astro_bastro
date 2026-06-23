# Astro Solves API

FastAPI backend for the Astro Solves beta. The deterministic chart engine lives in
`packages/astro-core`; model-backed rendering is kept behind the API and never exposed in the app UI.

## Local Run

```bash
PYTHONPATH=packages/astro-core:services/api python -m uvicorn app.main:app --app-dir services/api --reload
```

Optional environment variables:

- `OPENAI_API_KEY`: enables private model-backed readings.
- `OPENAI_MODEL`: defaults to `gpt-5.5`.
- `OPENAI_REASONING_EFFORT`: defaults to `medium`.
- `REVENUECAT_API_KEY`: enables live RevenueCat validation.
- `DATABASE_URL`: defaults to local SQLite at `services/api/astro_solves.db`.
- `TRUST_ASTRO_EPHEMERIS_DIR`: stores Skyfield/JPL ephemeris files outside the repo.

For local secrets, copy `services/api/.env.example` to `services/api/.env`.
The API also reads a root `.env` file. Both locations are ignored by git.

Without paid-service keys, endpoints stay runnable and return deterministic demo readings,
problem insights, and local-demo solution unlocks.

Core beta endpoints:

- `POST /profile`
- `GET /chart/natal`
- `GET /reading/{period}` with `daily`, `weekly`, `monthly`, or `yearly`
- `POST /problem/insight`
- `POST /solutions/unlock`
- `GET /memory/context`

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
docker build -f services/api/Dockerfile -t astro-solves-api .
docker run --rm -p 8000:8000 --env-file services/api/.env.example astro-solves-api
```
