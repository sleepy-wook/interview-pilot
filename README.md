# Interview Pilot

AI-powered mock interview platform with multi-agent orchestration and real-time voice input.

## Overview

Interview Pilot simulates realistic job interviews using multiple AI interviewer personas. It researches the target company and role, analyzes your resume, generates personalized questions, provides real-time coaching, and delivers a comprehensive evaluation report.

### Key Features

- **Multi-Agent Interview**: Three distinct personas — Hiring Manager, Technical Lead, HR — each with unique questioning styles and independent memory
- **Personalized Questions**: Questions reference your actual resume, projects, and identified skill gaps
- **Dynamic Follow-ups**: Weak or evasive answers trigger natural follow-up questions (not a static checklist)
- **Real-time Voice Input**: Speech-to-text via Amazon Transcribe with filler word detection and voice metrics
- **Practice Mode**: Progressive hints with key points, personal hooks from your resume, and example answers
- **Evaluation Report**: Per-question STAR analysis, consistency checking, model answers, and actionable improvement plan
- **Pre-researched Data**: Company/role competencies and interview styles stored in DB — no web search needed for known companies

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (Next.js)                                     │
│  React + TypeScript + Tailwind CSS                      │
│  Voice Recording (Web Audio API + WebSocket)            │
└─────────────────┬───────────────────────────────────────┘
                  │ REST + WebSocket
┌─────────────────▼───────────────────────────────────────┐
│  Backend (FastAPI)                                       │
│                                                          │
│  ┌──────────────────────────────────────┐               │
│  │  Agents                               │               │
│  │  ├─ ResearchAgent (web search/scrape) │               │
│  │  ├─ ResumeAgent (PDF analysis)        │               │
│  │  ├─ MasterAgent (orchestration)       │               │
│  │  ├─ PersonaAgents (HM/Tech/HR)       │               │
│  │  └─ EvaluationAgent (scoring)        │               │
│  └──────────────────────────────────────┘               │
│                                                          │
│  ┌──────────────────────────────────────┐               │
│  │  Tools (LLM-powered)                  │               │
│  │  question_generator, answer_analyzer, │               │
│  │  hint_generator, persona_router,      │               │
│  │  consistency_checker, star_detector,  │               │
│  │  gap_analyzer, jd_parser,             │               │
│  │  answer_improver                      │               │
│  └──────────────────────────────────────┘               │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│  AWS Services                                            │
│  ├─ Bedrock (Claude Haiku 4.5 / Sonnet 4.6)            │
│  ├─ Amazon Transcribe Streaming (STT)                   │
│  ├─ RDS PostgreSQL (persistence)                        │
│  └─ S3 (file storage)                                   │
└─────────────────────────────────────────────────────────┘
```

## Interview Flow

```
Phase 0: Setup
  └─ Select company/role, upload resume (optional), choose mode & model

Phase 1: Research & Planning
  └─ Load pre-researched data (or web search) → Analyze resume → Generate question plan

Phase 2: Interview
  └─ Question → Answer (text/voice) → Analysis → Routing → Follow-up or next question
     ├─ HM asks about business fit, culture, leadership
     ├─ Tech asks about architecture, coding, system design
     └─ HR asks about soft skills, motivation, expectations

Phase 3: Evaluation
  └─ Overall score, per-question analysis, STAR breakdown, model answers, action plan
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic |
| LLM | Amazon Bedrock (Claude Haiku 4.5, Sonnet 4.6) |
| STT | Amazon Transcribe Streaming |
| Database | PostgreSQL (RDS) |
| Storage | S3 |
| Package Mgmt | npm (frontend), uv (backend) |

## Project Structure

```
interview-pilot/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx            # Main page (phase state machine)
│   │   │   ├── layout.tsx          # Root layout
│   │   │   └── globals.css         # Tailwind imports
│   │   ├── components/
│   │   │   ├── SetupForm.tsx       # Company/role selection, file upload
│   │   │   ├── ResearchProgress.tsx # Loading animation during research
│   │   │   ├── InterviewChat.tsx   # Chat interface with voice/text input
│   │   │   ├── ChatMessage.tsx     # Individual message with persona styling
│   │   │   ├── CoachingPanel.tsx   # Real-time answer feedback sidebar
│   │   │   ├── HintPanel.tsx       # Progressive hints (practice mode)
│   │   │   ├── VoiceRecorder.tsx   # WebSocket audio streaming
│   │   │   ├── Report.tsx          # Evaluation report with charts
│   │   │   └── HistoryList.tsx     # Collapsible sidebar for past sessions
│   │   └── lib/
│   │       ├── api.ts              # API client functions
│   │       ├── types.ts            # TypeScript interfaces
│   │       └── constants.ts        # Persona/quality config
│   └── package.json
│
├── backend/
│   ├── main.py                     # FastAPI app entry point
│   ├── agents/
│   │   ├── base_agent.py           # BaseAgent with LLM tool loop
│   │   ├── research_agent.py       # Web research (autonomous)
│   │   ├── resume_agent.py         # Resume/LinkedIn analysis
│   │   ├── master_agent.py         # Interview orchestration
│   │   ├── persona_agents.py       # HM, Tech, HR personas
│   │   └── evaluation_agent.py     # Post-interview scoring
│   ├── tools/
│   │   ├── registry.py             # Tool registration system
│   │   ├── llm_tools.py            # 9 LLM-powered analysis tools
│   │   ├── document_reader.py      # PDF extraction (Vision + pdfplumber)
│   │   ├── web_search.py           # DuckDuckGo search
│   │   └── web_scrape.py           # Web page scraping
│   ├── api/
│   │   ├── interview.py            # Interview lifecycle endpoints
│   │   ├── voice_ws.py             # WebSocket voice streaming
│   │   └── upload.py               # File upload endpoint
│   ├── core/
│   │   ├── config.py               # Pydantic Settings
│   │   ├── state.py                # InterviewState dataclass
│   │   ├── database.py             # SQLAlchemy models
│   │   ├── seed.py                 # Pre-researched company data
│   │   ├── bedrock_client.py       # Bedrock API wrapper
│   │   ├── s3_client.py            # S3 operations
│   │   └── transcribe_client.py    # Transcribe Streaming client
│   └── pyproject.toml
│
├── .env.example                    # Environment template
└── CLAUDE.md                       # Project guidelines
```

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- AWS account with Bedrock, Transcribe, RDS, S3 access
- AWS CLI configured with named profile

### Setup

1. **Clone and configure environment**

```bash
cp .env.example backend/.env
# Edit backend/.env with your AWS credentials, DB URL, etc.
```

2. **Backend**

```bash
cd backend
uv sync
uv run uvicorn main:app --reload --port 8000
```

3. **Frontend**

```bash
cd frontend
npm install
npm run dev
```

4. Open http://localhost:3000

### Environment Variables

| Variable | Description |
|----------|-------------|
| `AWS_PROFILE` | AWS credentials profile name |
| `AWS_REGION` | AWS region (e.g., `us-east-1`) |
| `BEDROCK_MODEL_HAIKU` | Bedrock model ID for Haiku |
| `BEDROCK_MODEL_SONNET` | Bedrock model ID for Sonnet |
| `DATABASE_URL` | PostgreSQL connection string |
| `S3_BUCKET` | S3 bucket for file uploads |
| `TRANSCRIBE_LANGUAGE_CODE` | Transcribe language (default: `en-US`) |
| `FRONTEND_URL` | Frontend URL for CORS |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/interview/start` | Start interview (research + plan) |
| GET | `/api/interview/{id}/plan` | Get interview question plan |
| GET | `/api/interview/{id}/next` | Get next question with hints |
| POST | `/api/interview/{id}/answer` | Submit answer |
| POST | `/api/interview/{id}/evaluate` | Generate evaluation report |
| GET | `/api/interview/history` | Past interview sessions |
| GET | `/api/interview/company-roles` | Available company/role presets |
| POST | `/api/upload` | Upload resume/LinkedIn PDF |
| WS | `/api/ws/voice` | Voice streaming (WebSocket) |

## Database Schema

```
Session ─┬─ InterviewTurn (1:N)
         ├─ EvaluationReport (1:1)
         ├─ ResearchBrief (1:1)
         └─ UploadedFile (1:N)

CompanyRole (pre-researched company/role data with competencies, interview rounds, tips)
```

Tables are auto-created on startup. Pre-seeded with Databricks Korea / Solutions Engineer data.
