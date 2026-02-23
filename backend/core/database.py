"""Database connection and SQLAlchemy models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from core.config import get_settings


class Base(DeclarativeBase):
    pass


# --- Models ---


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    settings = Column(JSONB, default=dict)

    sessions = relationship("Session", back_populates="user")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    short_id = Column(String(8), unique=True, index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    company = Column(String, nullable=False)
    role = Column(String, nullable=False)
    mode = Column(String, nullable=False, default="practice")  # "practice" | "real"
    model = Column(String, nullable=False, default="haiku")  # "haiku" | "sonnet"
    question_count = Column(Integer, nullable=False, default=10)
    status = Column(String, nullable=False, default="in_progress")
    overall_score = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="sessions")
    research_brief = relationship("ResearchBrief", back_populates="session", uselist=False)
    turns = relationship("InterviewTurn", back_populates="session", order_by="InterviewTurn.turn_number")
    evaluation = relationship("EvaluationReport", back_populates="session", uselist=False)
    files = relationship("UploadedFile", back_populates="session")


class ResearchBrief(Base):
    __tablename__ = "research_briefs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    company = Column(String, nullable=False)
    role = Column(String, nullable=False)
    jd_structured = Column(JSONB, default=dict)
    company_intel = Column(JSONB, default=dict)
    resume_structured = Column(JSONB, default=dict)
    gap_analysis = Column(JSONB, default=dict)
    predicted_weak_points = Column(JSONB, default=dict)
    custom_vocabulary_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    reusable_hash = Column(String, index=True, nullable=True)

    session = relationship("Session", back_populates="research_brief")


class InterviewTurn(Base):
    __tablename__ = "interview_turns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    turn_number = Column(Integer, nullable=False)
    persona = Column(String, nullable=False)  # "HM" | "Tech" | "HR"
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    hint_bullets = Column(JSONB, default=dict)
    hint_used = Column(Boolean, default=False)
    hint_opened_at = Column(DateTime(timezone=True), nullable=True)
    answer_analysis = Column(JSONB, default=dict)
    voice_metrics = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    session = relationship("Session", back_populates="turns")


class EvaluationReport(Base):
    __tablename__ = "evaluation_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    overall_score = Column(Integer, nullable=True)
    persona_scores = Column(JSONB, default=dict)
    strengths = Column(JSONB, default=dict)
    weaknesses = Column(JSONB, default=dict)
    hint_analysis = Column(JSONB, default=dict)
    voice_summary = Column(JSONB, default=dict)
    model_answers = Column(JSONB, default=dict)
    action_plan = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    session = relationship("Session", back_populates="evaluation")


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    file_type = Column(String, nullable=False)  # "resume" | "linkedin"
    s3_key = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    session = relationship("Session", back_populates="files")


class CompanyRole(Base):
    """Pre-researched company + role data for skipping web research."""
    __tablename__ = "company_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company = Column(String, nullable=False)
    role = Column(String, nullable=False)
    role_description = Column(Text, nullable=True)
    required_competencies = Column(JSONB, default=list)
    technical_skills = Column(JSONB, default=list)
    soft_skills = Column(JSONB, default=list)
    interview_rounds = Column(JSONB, default=list)
    question_types = Column(JSONB, default=list)
    interview_tips = Column(JSONB, default=list)
    jd_structured = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# --- Engine & Session ---

_engine = None
_SessionFactory = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
    return _engine


def get_session_factory():
    global _SessionFactory
    if _SessionFactory is None:
        engine = get_engine()
        _SessionFactory = sessionmaker(bind=engine)
    return _SessionFactory


def get_db():
    """Get a DB session. Returns None if DB is unavailable."""
    try:
        factory = get_session_factory()
        db = factory()
        # Quick connectivity check
        db.execute(text("SELECT 1"))
        return db
    except Exception:
        return None


def create_tables():
    """Create all tables. Used for initial migration."""
    engine = get_engine()
    Base.metadata.create_all(engine)


def drop_tables():
    """Drop all tables. Use with caution."""
    engine = get_engine()
    Base.metadata.drop_all(engine)
