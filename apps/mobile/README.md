# Astro Solves Mobile

Expo app for the iOS + Android beta.

## Local Device Run

Start the API first:

```bash
DATABASE_URL=sqlite:////tmp/astro_solves_dev.db \
PYTHONPATH=packages/astro-core:services/api \
python -m uvicorn app.main:app --app-dir services/api --host 0.0.0.0 --port 8000
```

Then start Expo:

```bash
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm --workspace apps/mobile run start
```

For a physical phone on the same Wi-Fi, replace `127.0.0.1` with the Mac's LAN IP.
For Android Emulator, the app defaults to `http://10.0.2.2:8000`.

## EAS Preview

```bash
cd apps/mobile
npx eas build --profile preview --platform android
npx eas build --profile preview --platform ios
```

Set `EXPO_PUBLIC_API_BASE_URL` to the deployed API URL before making a public build.
