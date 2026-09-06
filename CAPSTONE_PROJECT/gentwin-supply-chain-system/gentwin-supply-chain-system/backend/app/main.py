"""
Application entrypoint.

Run with:
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth_router import router as auth_router
from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.services.user_store import get_user_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Backend for the Generative AI & Digital Twin-Based Supply Chain "
        "Resilience & Disruption Management System, with JWT-based user "
        "and admin authentication."
    ),
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["auth"])
app.include_router(v1_router, prefix=settings.API_V1_PREFIX, tags=["supply-chain-twin"])


@app.get("/", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok", "service": settings.PROJECT_NAME}


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Supply Chain Digital Twin backend starting up.")
    # Initializing the user store here seeds the default admin account
    # (see .env.example: DEFAULT_ADMIN_USERNAME / DEFAULT_ADMIN_PASSWORD).
    get_user_store()
    if not settings.GEMINI_API_KEY:
        logger.warning(
            "GEMINI_API_KEY is not set. /api/v1/simulate and the WebSocket "
            "stream will return errors until it is configured in .env."
        )
    if settings.SECRET_KEY == "dev-only-insecure-secret-change-me":
        logger.warning(
            "SECRET_KEY is using the insecure default. Set a strong random "
            "SECRET_KEY in .env before deploying."
        )
