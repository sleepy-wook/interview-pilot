# Interview Pilot - Project Guidelines

## Project Structure
- `frontend/` — Next.js (App Router, TypeScript, Tailwind CSS)
- `backend/` — Python FastAPI

## Backend
- **Package manager: `uv`** (not pip, not poetry)
  - Add dependencies: `uv add <package>`
  - Add dev dependencies: `uv add --dev <package>`
  - Run scripts: `uv run <command>`
  - Sync environment: `uv sync`
- Python 3.12
- Virtual environment at `backend/.venv/`

## Frontend
- Package manager: npm
- Next.js with App Router (`src/app/`)

## AWS Services
- Amazon Bedrock (Claude Haiku 4.5) — LLM
- Amazon Transcribe Streaming — STT
- RDS PostgreSQL — Database
- S3 — File storage
- EC2 — Backend deployment

## Language
- Application language: English only
- Code comments / docs: English or Korean OK
