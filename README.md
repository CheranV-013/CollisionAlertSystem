# SIH26007 — Intelligent Vehicle Surrounding Awareness

This is a local SIH 2026 prototype combining live HOST NEO-6M GPS, phone GPS for B01, camera detection interfaces, IMU status, sensor-fusion-ready models, collision-risk estimation, and an original automotive-style dashboard. It is not Tesla Autopilot/FSD.

## Run on macOS

```bash
./scripts/setup_mac.sh
cp .env.example .env
./scripts/run_all.sh
```

Open the frontend URL printed by Vite. FastAPI OpenAPI is available at the backend URL plus `/docs`. The map is deliberately key-free demo mode; `MAP_API_KEY` and `MAP_STYLE_URL` are reserved for a real provider integration.

The application starts in LIVE MODE with an empty registry. The first screen requires an explicit `HOST TRUCK` or `TRUCK MEMBER` choice. Each browser gets a persistent `smartDriveDeviceId`; the backend then assigns `HOST-001` or sequential `MEMBER-001`, `MEMBER-002`, and so on. Roles are never inferred from local storage, IP, or device type. If browser GPS is unavailable, the backend may display an `IP_APPROXIMATE` city-level fallback, never as precise vehicle GPS. DEMO MODE is only activated by pressing START DEMO or calling `/api/simulation/start`.

## Shared device flow

Open the same deployed website on every device. Select the role, then press `ENABLE GPS`. Browser geolocation requires a secure context. For local development, create a trusted local certificate with `mkcert`, then configure Vite's `server.https` using that certificate/key; alternatively use a local HTTPS reverse proxy. Do not disable browser security. Every device continuously sends validated `LOCATION_UPDATE` messages to the shared `/ws` endpoint, including accuracy and nullable speed/heading.

## Deployment

Render: deploy from `render.yaml`, or set root directory to `backend`, build command to `pip install -r requirements.txt`, and start command to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Set `ALLOWED_ORIGINS` to the deployed Vercel URL and verify `/api/health`.

Vercel: set project root to `frontend`, build command `npm run build`, output directory `dist`, and keep `frontend/vercel.json` for SPA fallback. Set `VITE_API_URL=https://<render-service>.onrender.com`, `VITE_WS_URL=wss://<render-service>.onrender.com/ws`, and optionally `VITE_MAP_STYLE_URL`.

To start a clean development world, call `POST /api/session/reset`. In production set `SESSION_RESET_TOKEN` and call `POST /api/session/reset?token=<token>`. After reset, the next explicitly selected host receives `HOST-001`; members receive `MEMBER-001`, `MEMBER-002`, and so on. Vehicle IDs are backend-assigned; local storage only retains the device ID, selected role, and assigned ID for reconnects.

## Test

```bash
source .venv/bin/activate
cd backend && pytest
cd ../frontend && npm test
```

## Hardware status

The Vehicle A sketch now reads NEO-6M NMEA with TinyGPS++ and posts real fix/no-fix state over Wi-Fi. The B01 phone path is live. nRF24 replacement and MPU6050 sampling still require bench wiring and board-specific validation. Camera inference remains disconnected until the ESP32-CAM is configured. See `docs/` for protocol, algorithms, hardware, and demo notes.
