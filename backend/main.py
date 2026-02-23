import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
            existing = db.query(CompanyRole).first()
            if existing is None:
                from core.seed import seed_company_roles
                seed_company_roles(db)
                logger.info("Seeded default company-role data.")
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

app.include_router(interview_router, prefix="/api")
app.include_router(voice_router, prefix="/api")
app.include_router(upload_router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
