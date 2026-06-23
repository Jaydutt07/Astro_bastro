# Astro Solves Beta

Problem-solving Vedic astrology app scaffold for iOS, Android, and API deployment.

The product direction is:

- Vedic astrology + numerology, India English-first
- deterministic chart facts as the source of truth
- private model-backed rendering behind the API, never exposed in the app UI
- privacy-forward profile storage and explicit consent
- daily, weekly, monthly, and yearly readings
- problem analysis for Shani, Saade Saati, career, relationship, family, money, and stress themes
- first remedy free, premium solution packs by subscription

## Project Layout

- `apps/mobile/`: Expo React Native iOS/Android app
- `services/api/`: FastAPI backend, model rendering, RevenueCat validation, place search
- `packages/astro-core/`: chart math, nakshatras, dashas, transits, numerology
- `docs/astro-solves-baseline.md`: baseline product context for future work

## Local API

```bash
python3 -m venv /tmp/astro-solves-venv
/tmp/astro-solves-venv/bin/pip install -r services/api/requirements.txt

DATABASE_URL=sqlite:////tmp/astro_solves_dev.db \
PYTHONPATH=packages/astro-core:services/api \
/tmp/astro-solves-venv/bin/python -m uvicorn app.main:app --app-dir services/api --host 0.0.0.0 --port 8000
```

## Local Mobile

```bash
npm install
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm --workspace apps/mobile run start
```

For Android Emulator, the app defaults to `http://10.0.2.2:8000`.
For a physical phone, set `EXPO_PUBLIC_API_BASE_URL` to the API machine's LAN IP.

## Verification

```bash
PYTHONPATH=packages/astro-core:services/api /tmp/astro-solves-venv/bin/python -m pytest services/api/tests packages/astro-core/tests -q
npm --workspace apps/mobile run typecheck
PYTHONPATH=packages/astro-core:services/api /tmp/astro-solves-venv/bin/python services/api/scripts/evaluate_reading_quality.py
```

## Environment

Copy `.env.example` to `.env`, or copy `services/api/.env.example` to `services/api/.env`, and fill only the services you are using. These `.env` files are ignored by git.

- `OPENAI_API_KEY`
- `OPENAI_MODEL` (defaults to `gpt-5.5`)
- `OPENAI_REASONING_EFFORT` (defaults to `medium`)
- `REVENUECAT_API_KEY`
- `DATABASE_URL`
- `TRUST_ASTRO_EPHEMERIS_DIR`

The app runs without OpenAI/RevenueCat keys by returning deterministic demo readings,
problem insights, and local-demo subscription unlocks.
