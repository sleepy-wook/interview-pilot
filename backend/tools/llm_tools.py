"""LLM-powered tools -- all tools that use Bedrock Claude for specialized analysis.

Each tool:
1. Receives structured input
2. Constructs a focused prompt
3. Calls Bedrock Claude (separate from Agent's main LLM call)
4. Returns structured JSON output
"""

from __future__ import annotations

import json

from core.bedrock_client import BedrockClient
from tools.registry import register_tool

# Shared LLM clients for tools (cached per model)
_llm_cache: dict[str, BedrockClient] = {}
_current_model: str = "haiku"


def set_llm_model(model: str) -> None:
    """Set the model used by LLM tools for the current session."""
    global _current_model
    _current_model = model


def _get_llm() -> BedrockClient:
    if _current_model not in _llm_cache:
        _llm_cache[_current_model] = BedrockClient(model=_current_model)
    return _llm_cache[_current_model]


def _llm_call(system: str, user_prompt: str, max_tokens: int = 2048) -> str:
    """Helper: make a focused LLM call and return text response."""
    llm = _get_llm()
    text, _ = llm.converse(
        messages=[{"role": "user", "content": user_prompt}],
        system=system,
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return text


def _parse_json(text: str) -> dict | list:
    """Try to extract JSON from LLM response."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try to find JSON in markdown code block
    for delim_start, delim_end in [("```json", "```"), ("```", "```"), ("{", None), ("[", None)]:
        try:
            start = text.index(delim_start)
            if delim_end and delim_start != delim_end:
                content_start = start + len(delim_start)
                end = text.index(delim_end, content_start)
                return json.loads(text[content_start:end])
            elif delim_start in ("{", "["):
                closing = "}" if delim_start == "{" else "]"
                end = text.rindex(closing) + 1
                return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            continue
    return {"raw_response": text}


# ─── Tool 1: jd_parser ───


@register_tool(
    name="jd_parser",
    description="Parse a job description text into structured requirements, responsibilities, qualifications, and technical keywords.",
    input_schema={
        "type": "object",
        "properties": {
            "jd_text": {"type": "string", "description": "Raw job description text"}
        },
        "required": ["jd_text"],
    },
)
def jd_parser(jd_text: str) -> dict:
    system = (
        "You are a job description parser. Extract structured information from the JD. "
        "Return ONLY valid JSON."
    )
    prompt = f"""Parse this job description into structured JSON:

{jd_text}

Return JSON with these keys:
- "requirements": list of required qualifications/skills
- "responsibilities": list of job responsibilities
- "qualifications": {{"required": [...], "preferred": [...]}}
- "keywords": list of technical keywords for STT custom vocabulary
- "experience_level": "entry" | "mid" | "senior"
- "summary": one-sentence role summary"""

    return _parse_json(_llm_call(system, prompt))


# ─── Tool 2: gap_analyzer ───


@register_tool(
    name="gap_analyzer",
    description="Compare structured JD requirements against structured resume to identify matches, gaps, and strengths.",
    input_schema={
        "type": "object",
        "properties": {
            "jd_structured": {"type": "object", "description": "Structured JD from jd_parser"},
            "resume_structured": {"type": "object", "description": "Structured resume from document_reader"},
        },
        "required": ["jd_structured", "resume_structured"],
    },
)
def gap_analyzer(jd_structured: dict, resume_structured: dict) -> dict:
    system = (
        "You are a resume-JD gap analyzer. Compare the candidate's profile against job requirements. "
        "Be specific and actionable. Return ONLY valid JSON."
    )
    prompt = f"""Compare this candidate's resume against the job requirements:

JD Requirements:
{json.dumps(jd_structured, ensure_ascii=False)}

Candidate Resume:
{json.dumps(resume_structured, ensure_ascii=False)}

Return JSON with:
- "matches": list of {{"requirement": "...", "evidence": "...", "strength": "strong"|"moderate"|"weak"}}
- "gaps": list of {{"requirement": "...", "severity": "critical"|"moderate"|"minor", "suggestion": "..."}}
- "strengths": list of standout candidate strengths not in JD
- "predicted_weak_points": list of topics the candidate will struggle with in interview
- "overall_fit_score": 1-100"""

    return _parse_json(_llm_call(system, prompt, max_tokens=3000))


# ─── Tool 3: question_generator ───


@register_tool(
    name="question_generator",
    description="Generate an interview question based on topic, persona, depth level, and conversation history.",
    input_schema={
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "depth": {"type": "string", "enum": ["surface", "moderate", "deep"]},
            "persona": {"type": "string", "enum": ["HM", "Tech", "HR"]},
            "history_summary": {"type": "string"},
            "research_brief_context": {"type": "object"},
        },
        "required": ["topic", "persona"],
    },
)
def question_generator(
    topic: str,
    persona: str,
    depth: str = "moderate",
    history_summary: str = "",
    research_brief_context: dict | None = None,
) -> dict:
    persona_styles = {
        "HM": "Warm but sharp. Start friendly, then ask the real question. Focus on business fit, culture, leadership.",
        "Tech": "Dry and precise. No fluff. If the answer is vague, say 'Can you be more specific?'. Focus on technical depth.",
        "HR": "Friendly and empathetic but persistent. Dig into motivations, soft skills, and career goals.",
    }
    system = (
        f"You are a {persona} interviewer. Style: {persona_styles.get(persona, '')} "
        "Generate a single PERSONALIZED interview question. Return ONLY valid JSON."
    )
    context_str = json.dumps(research_brief_context, ensure_ascii=False) if research_brief_context else "None"

    # Extract candidate info for personalization
    candidate_info = ""
    if research_brief_context:
        cp = research_brief_context.get("candidate_profile", {})
        ga = research_brief_context.get("gap_analysis", {})
        if cp:
            candidate_info = (
                f"\n\nCandidate specifics (reference in your question):\n"
                f"- Current role: {cp.get('current_role', 'N/A')}\n"
                f"- Key skills: {', '.join(cp.get('skills', [])[:5])}\n"
                f"- Experience: {cp.get('experience_years', 'N/A')} years\n"
            )
        if isinstance(ga, dict) and ga.get("gaps"):
            candidate_info += "- Known gaps: " + ", ".join(
                g.get("requirement", "") for g in ga.get("gaps", [])[:3]
                if isinstance(g, dict)
            ) + "\n"

    prompt = f"""Generate an interview question:
- Topic: {topic}
- Depth: {depth}
- Persona: {persona}
- Previous questions summary: {history_summary or 'None'}
- Research context: {context_str}
{candidate_info}
IMPORTANT: The question MUST be personalized to this specific candidate.
Reference their actual experience, projects, skills, or gaps.
Do NOT ask generic textbook questions.

Return JSON:
- "question": the personalized interview question text
- "rationale": why this question matters for THIS candidate
- "follow_up_if_weak": a follow-up question if the answer is weak"""

    return _parse_json(_llm_call(system, prompt))


# ─── Tool 4: hint_generator ───


@register_tool(
    name="hint_generator",
    description="Generate personalized hint bullet points for an interview question BEFORE the user answers.",
    input_schema={
        "type": "object",
        "properties": {
            "question": {"type": "string"},
            "persona": {"type": "string", "enum": ["HM", "Tech", "HR"]},
            "resume_context": {"type": "object"},
            "research_brief_context": {"type": "object"},
        },
        "required": ["question", "persona"],
    },
)
def hint_generator(
    question: str,
    persona: str,
    resume_context: dict | None = None,
    research_brief_context: dict | None = None,
) -> dict:
    system = (
        "You are an interview coach. Generate helpful hints for the candidate. "
        "Include both general key points AND personalized hooks from their resume. "
        "Return ONLY valid JSON."
    )
    resume_str = json.dumps(resume_context, ensure_ascii=False) if resume_context else "No resume data"
    brief_str = json.dumps(research_brief_context, ensure_ascii=False) if research_brief_context else "No research data"

    prompt = f"""Generate hints for this interview question:

Question: {question}
Persona: {persona}
Candidate Resume: {resume_str}
Research Brief: {brief_str}

Return JSON:
- "bullets": list of 3-5 key points to cover in the answer
- "personal_hooks": list of 1-3 specific experiences from the candidate's resume they should mention
- "avoid": list of 1-2 things NOT to say
- "example_answer": a full model answer (60-90 seconds speaking length, conversational tone, uses STAR framework where applicable, references the candidate's actual experience)"""

    return _parse_json(_llm_call(system, prompt, max_tokens=2048))


# ─── Tool 5: answer_analyzer ───


@register_tool(
    name="answer_analyzer",
    description="Analyze a user's answer for quality, confidence, specificity, STAR structure, and red flags.",
    input_schema={
        "type": "object",
        "properties": {
            "question": {"type": "string"},
            "answer": {"type": "string"},
            "persona": {"type": "string", "enum": ["HM", "Tech", "HR"]},
        },
        "required": ["question", "answer"],
    },
)
def answer_analyzer(question: str, answer: str, persona: str = "HM") -> dict:
    system = (
        "You are a strict interview answer evaluator. Analyze the answer objectively. "
        "Be honest about quality -- most interview answers are NOT strong. "
        "Return ONLY valid JSON."
    )
    prompt = f"""Analyze this interview answer:

Question ({persona}): {question}
Answer: {answer}

QUALITY RUBRIC (follow strictly):
- "strong": Specific examples with numbers/metrics, clear STAR structure, fully addresses the question
- "adequate": Addresses the question but lacks specifics, depth, or concrete examples
- "weak": Vague, generic, no examples, uses hedging language ("I think", "probably", "maybe"), or very short (<50 words)
- "evasive": Redirects, refuses to answer, or answers a different question entirely

IMPORTANT: An answer shorter than 50 words is almost never "strong".
An answer with no specific examples or numbers is at most "adequate".

Return JSON:
- "quality": "strong" | "adequate" | "weak" | "evasive"
- "confidence_score": 1-100
- "specificity_score": 1-100
- "star_score": 1-100 (how well it follows STAR framework)
- "key_points_covered": list of good points mentioned
- "missing_points": list of important things not mentioned
- "flags": list of concerns (e.g., "vague", "too_short", "no_examples", "inconsistent", "avoided_topic")
- "summary": one-sentence assessment"""

    return _parse_json(_llm_call(system, prompt))


# ─── Tool 6: persona_router ───


@register_tool(
    name="persona_router",
    description="Decide which persona should ask the next question and what action to take.",
    input_schema={
        "type": "object",
        "properties": {
            "current_persona": {"type": "string"},
            "answer_quality": {"type": "string", "enum": ["strong", "adequate", "weak", "evasive"]},
            "remaining_topics": {"type": "array", "items": {"type": "string"}},
            "flags": {"type": "array", "items": {"type": "string"}},
            "answer_summary": {"type": "string", "description": "Brief summary of the candidate's answer"},
        },
        "required": ["current_persona", "answer_quality", "remaining_topics"],
    },
)
def persona_router(
    current_persona: str,
    answer_quality: str,
    remaining_topics: list[str],
    flags: list[str] | None = None,
    answer_summary: str = "",
) -> dict:
    system = (
        "You are an interview flow controller that makes real interviewers' decisions. "
        "Real interviewers ALWAYS follow up on weak or incomplete answers. "
        "They do NOT simply move to the next question when an answer is vague, short, or evasive. "
        "Return ONLY valid JSON."
    )
    prompt = f"""Decide next interview action:

Current persona: {current_persona}
Answer quality: {answer_quality}
Answer summary: {answer_summary}
Remaining topics: {remaining_topics}
Flags: {flags or []}

DECISION RULES (follow strictly):
1. If answer_quality is "weak" -> action MUST be "follow_up" (same persona probes deeper)
2. If answer_quality is "evasive" -> action MUST be "follow_up" (same persona pushes for real answer)
3. If answer_quality is "adequate" and there are flags -> action should be "follow_up"
4. If answer_quality is "adequate" with no flags -> action is "next_planned"
5. If answer_quality is "strong" -> action is "next_planned"
6. If flags contain inconsistency keywords -> action is "cross_check" with the persona that can verify
7. If remaining_topics is empty -> consider "end_interview"

A real interview is a CONVERSATION, not a checklist. Follow-ups are expected and normal.

Return JSON:
- "next_persona": "HM" | "Tech" | "HR"
- "action": "next_planned" | "follow_up" | "cross_check" | "dynamic_question" | "end_interview"
- "reason": brief explanation
- "suggested_topic": topic for next question (if applicable)
- "follow_up_focus": what the follow-up should probe (if action is follow_up)"""

    return _parse_json(_llm_call(system, prompt))


# ─── Tool 7: star_detector ───


@register_tool(
    name="star_detector",
    description="Analyze if an answer follows the STAR framework (Situation, Task, Action, Result).",
    input_schema={
        "type": "object",
        "properties": {
            "answer": {"type": "string"}
        },
        "required": ["answer"],
    },
)
def star_detector(answer: str) -> dict:
    system = (
        "You are a STAR framework analyzer. Identify STAR components in the answer. "
        "Return ONLY valid JSON."
    )
    prompt = f"""Analyze this answer for STAR framework structure:

Answer: {answer}

Return JSON:
- "situation": {{"present": true/false, "text": extracted text or ""}}
- "task": {{"present": true/false, "text": extracted text or ""}}
- "action": {{"present": true/false, "text": extracted text or ""}}
- "result": {{"present": true/false, "text": extracted text or ""}}
- "score": 1-100 (overall STAR completeness)
- "feedback": one-sentence improvement suggestion"""

    return _parse_json(_llm_call(system, prompt))


# ─── Tool 8: consistency_checker ───


@register_tool(
    name="consistency_checker",
    description="Check for contradictions across multiple answers given during the interview.",
    input_schema={
        "type": "object",
        "properties": {
            "answers": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "answer": {"type": "string"},
                        "persona": {"type": "string"},
                    },
                },
            }
        },
        "required": ["answers"],
    },
)
def consistency_checker(answers: list[dict]) -> dict:
    system = (
        "You are a consistency analyzer. Find contradictions or inconsistencies "
        "across multiple interview answers. Return ONLY valid JSON."
    )
    answers_str = json.dumps(answers, ensure_ascii=False)
    prompt = f"""Check these interview answers for contradictions:

{answers_str}

Return JSON:
- "contradictions": list of {{"answer_1_index": int, "answer_2_index": int, "description": "...", "severity": "high"|"medium"|"low"}}
- "concerns": list of general concerns about consistency
- "consistent": true/false (overall assessment)"""

    return _parse_json(_llm_call(system, prompt))


# ─── Tool 9: answer_improver ───


@register_tool(
    name="answer_improver",
    description="Generate an improved model answer with reasoning and tips, personalized to the user's resume.",
    input_schema={
        "type": "object",
        "properties": {
            "question": {"type": "string"},
            "user_answer": {"type": "string"},
            "context": {"type": "object"},
        },
        "required": ["question", "user_answer"],
    },
)
def answer_improver(question: str, user_answer: str, context: dict | None = None) -> dict:
    system = (
        "You are an interview coach. Generate an improved model answer. "
        "Keep it natural and conversational, not robotic. Return ONLY valid JSON."
    )
    context_str = json.dumps(context, ensure_ascii=False) if context else "No additional context"
    prompt = f"""Improve this interview answer:

Question: {question}
User's answer: {user_answer}
Context (resume/research): {context_str}

Return JSON:
- "improved_answer": the full improved answer text (conversational, 60-90 seconds speaking length)
- "reasoning": list of what was changed and why
- "tips": list of 2-3 actionable tips for the candidate
- "score_before": estimated score of original answer (1-100)
- "score_after": estimated score of improved answer (1-100)"""

    return _parse_json(_llm_call(system, prompt, max_tokens=3000))
