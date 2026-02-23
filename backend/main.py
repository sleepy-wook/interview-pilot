import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.auth import verify_password
from core.config import get_settings
from api.interview import router as interview_router
from api.voice_ws import router as voice_router
from api.upload import router as upload_router

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB tables and seed data if needed."""
    try:
        from core.database import create_tables, get_db, CompanyRole
        create_tables()
        logger.info("Database tables created/verified.")
        # Seed default company-role if empty
        db = get_db()
        if db is not None:
            from core.seed import seed_company_roles
            seed_company_roles(db)
            logger.info("Company-role seed data synced.")
            db.close()
    except Exception as e:
        logger.warning("DB init skipped (DB unavailable): %s", e)
    yield


app = FastAPI(
    title="Interview Pilot API",
    description="AI Mock Interview Agent Backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interview_router, prefix="/api", dependencies=[Depends(verify_password)])
app.include_router(voice_router, prefix="/api")  # WebSocket handles auth separately
app.include_router(upload_router, prefix="/api", dependencies=[Depends(verify_password)])


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/auth/check")
async def auth_check():
    """Public endpoint: returns whether password is required."""
    return {"required": bool(settings.app_password)}
