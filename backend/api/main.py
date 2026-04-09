"""
FastAPI application entry-point.

Run with:
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import events as events_router
from api.routes import squads as squads_router
from config.settings import get_settings
from db.database import init_db

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

settings = get_settings()


# ── Lifespan (startup/shutdown hooks) ────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up KnightLife API …")
    await init_db()
    yield
    logger.info("Shutting down KnightLife API.")


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="KnightLife Events API",
    description=(
        "Automatically detected campus events scraped from UCF club Instagram accounts. "
        "Powered by Instaloader + Ollama (Phi-3 + Mistral 7B) + OCR."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(events_router.router)
app.include_router(squads_router.router)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok", "service": "knightlife-api"}


@app.get("/", tags=["meta"])
async def root() -> dict:
    return {
        "message": "KnightLife Events API",
        "docs": "/docs",
        "endpoints": [
            "/events", "/events/today", "/events/upcoming", "/events/club/{club_name}",
            "/squads", "/squads/{invite_code}", "/squads/{invite_code}/join",
        ],
    }
