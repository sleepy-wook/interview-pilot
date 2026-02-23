"""Interview API endpoints.

Handles the full interview lifecycle:
- POST /interview/start: Start research + resume analysis (Phase 0)
- GET  /interview/{session_id}/plan: Get interview plan (Phase 1)
- GET  /interview/{session_id}/next: Get next question + hints
- POST /interview/{session_id}/answer: Submit answer (text mode)
- POST /interview/{session_id}/evaluate: Generate evaluation report (Phase 3)
- GET  /interview/{session_id}/state: Get current interview state
- GET  /interview/history: Get past interview sessions
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Import tools to register them
import tools.web_search  # noqa: F401
import tools.web_scrape  # noqa: F401
import tools.llm_tools  # noqa: F401
import tools.document_reader  # noqa: F401

from tools.registry import global_registry
from tools.llm_tools import set_llm_model
from agents.research_agent import ResearchAgent
from agents.resume_agent import ResumeAgent
from agents import merge_research_brief
from agents.persona_agents import HMPersona, TechPersona, HRPersona
from agents.master_agent import MasterAgent
from agents.evaluation_agent import EvaluationAgent
from core.state import InterviewState
from core.database import (
    get_db,
    Session as DBSession,
    InterviewTurn as DBTurn,
    EvaluationReport as DBEvalReport,
    CompanyRole,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interview", tags=["interview"])

# In-memory session store (live sessions)
_sessions: dict[str, dict] = {}


# ── DB helpers (best-effort, never block the interview) ──


def _save_session_to_db(session_id: str, req: "StartRequest", plan_length: int) -> None:
    """Save a new interview session to the database."""
    try:
        db = get_db()
        if db is None:
            return
        db_session = DBSession(
            short_id=session_id,
            company=req.company,
            role=req.role,
            mode=req.mode,
            model=req.model,
            question_count=req.question_count,
            status="in_progress",
        )
        db.add(db_session)
        db.commit()
        db.close()
    except Exception as e:
        logger.warning("Failed to save session to DB: %s", e)


def _save_turn_to_db(session_id: str, turn) -> None:
    """Save an interview turn to the database."""
    try:
        db = get_db()
        if db is None:
            return
        db_session = db.query(DBSession).filter(DBSession.short_id == session_id).first()
        if not db_session:
            db.close()
            return
        db_turn = DBTurn(
            session_id=db_session.id,
            turn_number=turn.turn_number,
            persona=turn.persona,
            question=turn.question,
            answer=turn.answer,
            hint_used=turn.hint_used,
            hint_bullets=turn.hint_bullets,
            answer_analysis=turn.answer_analysis,
            voice_metrics=turn.voice_metrics,
        )
        db.add(db_turn)
        db.commit()
        db.close()
    except Exception as e:
        logger.warning("Failed to save turn to DB: %s", e)


def _save_evaluation_to_db(session_id: str, report: dict) -> None:
    """Save evaluation report and mark session as completed."""
    try:
        db = get_db()
        if db is None:
            return
        db_session = db.query(DBSession).filter(DBSession.short_id == session_id).first()
        if not db_session:
            db.close()
            return
        db_eval = DBEvalReport(
            session_id=db_session.id,
            overall_score=report.get("overall_score"),
            persona_scores=report.get("persona_scores", {}),
            strengths=report.get("strengths", []),
            weaknesses=report.get("weaknesses", []),
            hint_analysis=report.get("hint_analysis", {}),
            voice_summary=report.get("voice_summary", {}),
            model_answers=report.get("model_answers", []),
            action_plan=report.get("action_plan", []),
        )
        db.add(db_eval)
        db_session.status = "completed"
        db_session.overall_score = report.get("overall_score")
        db_session.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.close()
    except Exception as e:
        logger.warning("Failed to save evaluation to DB: %s", e)


# ── Request models ──


class StartRequest(BaseModel):
    company: str
    role: str
    resume_path: str | None = None
    linkedin_path: str | None = None
    linkedin_url: str | None = None
    mode: str = "practice"
    question_count: int = Field(default=7, ge=3, le=20)
    model: str = Field(default="haiku", pattern="^(haiku|sonnet)$")


class AnswerRequest(BaseModel):
    answer: str
    voice_metrics: dict | None = None


# ── Endpoints ──


@router.get("/history")
async def get_history():
    """Get past interview sessions from DB."""
    try:
        db = get_db()
        if db is None:
            return {"sessions": []}
        sessions = (
            db.query(DBSession)
            .order_by(DBSession.created_at.desc())
            .limit(50)
            .all()
        )
        result = []
        for s in sessions:
            turn_count = len(s.turns) if s.turns else 0
            result.append({
                "session_id": s.short_id,
                "company": s.company,
                "role": s.role,
                "mode": s.mode,
                "model": s.model,
                "status": s.status,
                "overall_score": s.overall_score,
                "question_count": s.question_count,
                "turn_count": turn_count,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            })
        db.close()
        return {"sessions": result}
    except Exception as e:
        logger.warning("Failed to fetch history: %s", e)
        return {"sessions": []}


@router.get("/company-roles")
async def get_company_roles():
    """Get available company-role presets from DB."""
    try:
        db = get_db()
        if db is None:
            return {"company_roles": []}
        roles = db.query(CompanyRole).order_by(CompanyRole.company).all()
        result = []
        for r in roles:
            result.append({
                "id": str(r.id),
                "company": r.company,
                "role": r.role,
            })
        db.close()
        return {"company_roles": result}
    except Exception as e:
        logger.warning("Failed to fetch company-roles: %s", e)
        return {"company_roles": []}


def _get_cached_research(company: str, role: str) -> dict | None:
    """Look up pre-researched company-role data from DB."""
    try:
        db = get_db()
        if db is None:
            return None
        cr = (
            db.query(CompanyRole)
            .filter(CompanyRole.company == company, CompanyRole.role == role)
            .first()
        )
        if cr is None:
            db.close()
            return None
        result = {
            "company_profile": {
                "name": cr.company,
                "description": cr.role_description or "",
            },
            "jd_structured": cr.jd_structured or {},
            "interview_tips": cr.interview_tips or [],
            "keywords": cr.jd_structured.get("keywords", []) if cr.jd_structured else [],
            "competitive_landscape": "",
            "company_role_meta": {
                "required_competencies": cr.required_competencies or [],
                "technical_skills": cr.technical_skills or [],
                "soft_skills": cr.soft_skills or [],
                "interview_rounds": cr.interview_rounds or [],
                "question_types": cr.question_types or [],
            },
        }
        db.close()
        return result
    except Exception:
        return None


@router.post("/start")
async def start_interview(req: StartRequest):
    """Phase 0: Research + Resume analysis, then Phase 1: Generate plan."""
    session_id = str(uuid.uuid4())[:8]
    model = req.model

    # Set LLM tools model for this session
    set_llm_model(model)

    # Phase 0: Check for cached company-role data (skip web research if found)
    cached = _get_cached_research(req.company, req.role)

    if cached:
        research_output = cached
        logger.info("Using cached research for %s / %s", req.company, req.role)
    else:
        # Phase 0: Research (web search)
        research_agent = ResearchAgent(registry=global_registry, model=model)
        research_output = research_agent.research(req.company, req.role)

    # Phase 0: Resume/LinkedIn analysis (if either provided)
    resume_output = {}
    if req.resume_path or req.linkedin_path or req.linkedin_url:
        jd_structured = research_output.get("jd_structured", {})
        resume_agent = ResumeAgent(registry=global_registry, model=model)
        resume_output = resume_agent.analyze(
            resume_path=req.resume_path or "",
            jd_structured=jd_structured,
            linkedin_path=req.linkedin_path,
            linkedin_url=req.linkedin_url,
        )

    # Merge into Research Brief
    brief = merge_research_brief(research_output, resume_output)

    keywords = brief.get("keywords", [])

    # Create interview state
    state = InterviewState(
        session_id=session_id,
        company=req.company,
        role=req.role,
        mode=req.mode,
        model=model,
        question_count=req.question_count,
        research_brief=brief,
    )

    # Phase 1: Generate plan
    personas = {
        "HM": HMPersona(registry=global_registry, model=model),
        "Tech": TechPersona(registry=global_registry, model=model),
        "HR": HRPersona(registry=global_registry, model=model),
    }
    master = MasterAgent(registry=global_registry, state=state, personas=personas)
    plan = master.generate_plan()

    # Store session in memory
    _sessions[session_id] = {
        "state": state,
        "master": master,
        "personas": personas,
    }

    # Persist to DB (best-effort)
    _save_session_to_db(session_id, req, len(plan))

    return {
        "session_id": session_id,
        "research_brief_summary": {
            "company": brief.get("company_profile", {}).get("name", req.company),
            "gaps_count": len(brief.get("gap_analysis", {}).get("gaps", [])),
            "keywords_count": len(keywords),
        },
        "plan_length": len(plan),
    }


@router.get("/{session_id}/plan")
async def get_plan(session_id: str):
    """Get the interview plan."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"plan": session["state"].interview_plan}


@router.get("/{session_id}/next")
async def get_next_question(session_id: str):
    """Get the next interview question + hints."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    master: MasterAgent = session["master"]

    if master.should_end_interview():
        return {"done": True, "message": "Interview complete"}

    q_data = master.get_next_question()
    if q_data is None:
        return {"done": True, "message": "No more questions"}

    return {
        "done": False,
        "question": q_data["question"],
        "persona": q_data["persona"],
        "topic": q_data["topic"],
        "hints": q_data.get("hints", {}),
    }


@router.post("/{session_id}/answer")
async def submit_answer(session_id: str, req: AnswerRequest):
    """Submit a text or voice answer for the current question."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    master: MasterAgent = session["master"]
    state: InterviewState = session["state"]

    # Get the current question info from the last get_next_question call
    history = state.answer_history
    current_index = state.current_index
    plan = state.interview_plan

    # Determine which question this answer is for
    if current_index < len(plan):
        current_q = plan[current_index]
    elif state.dynamic_questions:
        current_q = state.dynamic_questions[0]
    else:
        raise HTTPException(status_code=400, detail="No pending question")

    persona = current_q.get("persona", "HM")
    question = current_q.get("question", "")

    result = master.process_answer(question, req.answer, persona)

    # Attach voice metrics if provided
    if req.voice_metrics and result.get("turn"):
        result["turn"].voice_metrics = req.voice_metrics

    # Persist turn to DB (best-effort)
    if result.get("turn"):
        _save_turn_to_db(session_id, result["turn"])

    return {
        "analysis": result["analysis"],
        "consistency": result.get("consistency"),
        "routing": result["routing"],
        "turn_number": result["turn"].turn_number,
        "is_interview_over": master.should_end_interview(),
    }


@router.post("/{session_id}/evaluate")
async def evaluate_interview(session_id: str):
    """Phase 3: Generate evaluation report after interview ends."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    state: InterviewState = session["state"]

    if not state.answer_history:
        raise HTTPException(status_code=400, detail="No answers to evaluate")

    evaluator = EvaluationAgent(registry=global_registry, model=state.model)
    report = evaluator.evaluate(state)

    # Store report in session for later retrieval
    session["evaluation_report"] = report

    # Persist evaluation to DB (best-effort)
    _save_evaluation_to_db(session_id, report)

    return report


@router.get("/{session_id}/state")
async def get_state(session_id: str):
    """Get current interview state (for debugging/monitoring)."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    state: InterviewState = session["state"]
    return {
        "session_id": state.session_id,
        "company": state.company,
        "role": state.role,
        "mode": state.mode,
        "current_index": state.current_index,
        "total_questions": len(state.interview_plan),
        "answers_given": len(state.answer_history),
        "flags_count": len(state.flags),
        "coverage": state.coverage,
    }
