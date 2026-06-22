# Astro Bastro / Trust Astro MVP

Trust-first Vedic astrology app scaffold for iOS, Android, and API deployment.

The product direction is:

- Vedic astrology + numerology, India English-first
- deterministic chart facts as the source of truth
- GPT as the reading renderer, not the astrologer
- privacy-forward profile storage and explicit consent
- freemium daily readings, paid reports, and AI question credits

## Project Layout

- `apps/mobile/`: Expo React Native iOS/Android app
- `services/api/`: FastAPI backend, GPT rendering, RevenueCat validation, place search
- `packages/astro-core/`: chart math, nakshatras, dashas, transits, numerology

## Local API

```bash
python3 -m venv /tmp/trust-astro-venv
/tmp/trust-astro-venv/bin/pip install -r services/api/requirements.txt

DATABASE_URL=sqlite:////tmp/trust_astro_dev.db \
PYTHONPATH=packages/astro-core:services/api \
/tmp/trust-astro-venv/bin/python -m uvicorn app.main:app --app-dir services/api --host 0.0.0.0 --port 8000
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
PYTHONPATH=packages/astro-core:services/api /tmp/trust-astro-venv/bin/python -m pytest services/api/tests packages/astro-core/tests -q
npm --workspace apps/mobile run typecheck
PYTHONPATH=packages/astro-core:services/api /tmp/trust-astro-venv/bin/python services/api/scripts/evaluate_reading_quality.py
```

## Environment

Copy `.env.example` or `services/api/.env.example` and fill only the services you are using:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `REVENUECAT_API_KEY`
- `DATABASE_URL`
- `TRUST_ASTRO_EPHEMERIS_DIR`

The app runs without OpenAI/RevenueCat keys by returning deterministic demo readings
and mock-validating local purchases.
