# Supply Chain Digital Twin — Backend

FastAPI backend for the **Generative AI & Digital Twin-Based Supply Chain
Resilience & Disruption Management System**, with JWT-based authentication
and `user` / `admin` roles.

## Stack
- FastAPI + Uvicorn (async)
- Pydantic v2 (full typing, structured schemas)
- NetworkX (Digital Twin graph engine)
- google-genai (Gemini 3.5 Flash, structured outputs)
- WebSockets (real-time scenario streaming)
- SQLite + passlib(bcrypt) + python-jose (accounts & JWT auth)

## Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: set GEMINI_API_KEY, SECRET_KEY, and (optionally)
# DEFAULT_ADMIN_USERNAME / DEFAULT_ADMIN_PASSWORD
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

On first startup, a `supply_chain_twin.db` SQLite file is created and
seeded with one admin account (`DEFAULT_ADMIN_USERNAME` /
`DEFAULT_ADMIN_PASSWORD` from `.env`, default `admin` / `Admin@123`).

## Endpoints

| Method | Path                     | Auth required | Description                                |
|--------|--------------------------|----------------|---------------------------------------------|
| POST   | `/api/v1/auth/register`  | No             | Create a new `user`-role account             |
| POST   | `/api/v1/auth/login`     | No             | Exchange username/password for a JWT         |
| GET    | `/api/v1/auth/me`        | Yes            | Return the current user's profile            |
| GET    | `/api/v1/network`        | Yes            | Current Digital Twin node/edge state         |
| POST   | `/api/v1/twin/generate-chain` | Yes       | Turn the user's own description into a network (becomes the new baseline) |
| POST   | `/api/v1/twin/restore-default` | Yes      | Discard the custom chain, restore the built-in demo network |
| GET    | `/api/v1/twin/suggest-scenarios` | Yes    | 3-4 AI-suggested disruptions tailored to the current network |
| POST   | `/api/v1/simulate`       | Yes            | Run Gemini disruption analysis + apply it (accepts any suggested OR custom prompt) |
| POST   | `/api/v1/optimize`       | Yes            | Baseline vs disrupted vs optimized routes    |
| POST   | `/api/v1/reset`          | Yes (**admin only**) | Reset network to its current baseline (demo seed, or the user's own generated chain) |
| WS     | `/api/v1/stream-sim`     | Yes (token as first message) | Streamed simulation progress |

Send the JWT as `Authorization: Bearer <token>` on every protected HTTP
call. For the WebSocket, send `{"token": "<token>"}` as the very first
message before any `{"prompt": "..."}` messages.

## Project Layout

```
app/
  core/
    config.py       # Settings (env-driven, incl. auth secrets)
    security.py       # Password hashing + JWT issuance/verification
    deps.py            # get_current_user / get_current_admin dependencies
  models/schemas.py     # Pydantic v2 schemas (twin + auth)
  services/
    twin_engine.py       # NetworkX-based Digital Twin singleton
    ai_simulator.py        # Gemini structured-output disruption engine
    optimizer.py             # Weighted Dijkstra resilience optimizer
    user_store.py             # SQLite-backed user accounts, seeds default admin
  api/v1/
    auth_router.py             # register / login / me
    router.py                    # network / simulate / optimize / reset / stream-sim
  main.py                         # App entrypoint, CORS, router mounting
```

## Verified locally
- Full auth flow tested via FastAPI's `TestClient`: register, duplicate
  username rejection, login, wrong-password rejection, unauthenticated
  requests correctly return 401, non-admin `POST /reset` correctly
  returns 403, admin `POST /reset` succeeds.
- `/network`, `/optimize` (baseline vs disrupted vs AI-optimized reroute),
  and `/reset` all pass functional tests once authenticated.
- `/simulate` and the WebSocket require a live `GEMINI_API_KEY` to
  exercise end-to-end; without one they return a clear 503 rather than
  failing silently.

## Notes
- The twin (network state) is an in-memory singleton — restart the server
  or call `POST /api/v1/reset` (as admin) to clear it. User accounts
  persist separately in the SQLite file across restarts.
- Change `SECRET_KEY` and `DEFAULT_ADMIN_PASSWORD` before any real
  deployment (see the top-level `README.md`).
