# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Job Analyzer is an AI-powered job analysis tool that helps job seekers evaluate job postings against their CV. Users manually paste job descriptions, and the system analyzes eligibility, generates match scores, provides resume suggestions, identifies ATS keywords, and generates tailored cover letters. The system includes daily email digests of analyzed jobs.

## Online Repository

The project is hosted on Github on this repository: https://github.com/emytrb/job-search.
The gh CLI (Github CLI) is correctly configured, you can use the `gh` commands to interact with the github repository.
When you have completed a significant feature, ask the user if they want you to commit & push.

## Commands

### Development

All services run via Docker during development.

```bash
# Start all services
docker-compose up

# Start specific services
docker-compose up postgres redis backend frontend

# Backend only (requires postgres/redis running)
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend only
cd frontend && npm run dev

# Run database migrations
cd backend && alembic upgrade head

# Create new migration
cd backend && alembic revision --autogenerate -m "description"
```

## DB Credentials

User: `jobsearcher`
Password: `changeme`

### Frontend

```bash
cd frontend
npm run dev      # Development server
npm run build    # Production build
npm run lint     # ESLint
```

### Celery Workers

```bash
cd backend
# LLM worker (processes job analyses, must be -c 1 for rate limiting)
celery -A workers.celery_app worker -Q llm -c 1 --loglevel=info

# Digest worker (sends email digests)
celery -A workers.celery_app worker -Q digest -c 1 --loglevel=info

# Beat scheduler (triggers periodic digest)
celery -A workers.celery_app beat --loglevel=info
```

## Architecture

### Processing Pipeline

```
User Input → Analysis Queue → LLM Analysis → SavedAnalysis → Frontend/Digest
                   ↓
            Celery Workers (2 queues: llm, digest)
```

1. **Job Input**: User pastes job description and URL on the Analyzer page
2. **Queue Processing**: Jobs are queued and processed sequentially with automatic retry on failure
3. **LLM Analysis** (`backend/llm/client.py`): Uses LiteLLM with Groq cloud API. Performs 4-step analysis:
   - Eligibility check (early exit if not eligible)
   - Matching score and job summary
   - Resume analysis and ATS keywords
   - Cover letter generation
4. **Results Storage**: Analysis saved to `SavedAnalysis` model for later viewing

### Key Components

- **API**: FastAPI async app at `backend/app/main.py`, routes in `backend/app/api/v1/`
- **Models**: SQLAlchemy ORM in `backend/app/models/` (SavedAnalysis, AnalysisQueueItem, UserPreferences, Digest)
- **Workers**: Celery tasks in `backend/workers/tasks/` with 2 queues: llm, digest
- **Frontend**: Next.js app in `frontend/src/app/` with pages for analyzer (home), analyzed-jobs, digest, settings
- **LLM Prompts**: `backend/llm/prompts/job_analyzer.py` contains all analysis prompts

### Infrastructure

- PostgreSQL (async via asyncpg)
- Redis (Celery broker)
- Groq Cloud API (LLM provider, uses `openai/gpt-oss-120b` model)
- Nginx reverse proxy

### Rate Limiting

The LLM client handles Groq's rate limits automatically:

- Catches 429 responses and reads the `retry-after` header
- Waits the exact time specified before retrying
- Falls back to exponential backoff if header unavailable
- Supports up to 10 retries per request

### Celery Beat Schedule

- Daily digest: 8 AM UTC

## API Endpoints

- `POST /api/v1/analyzer/analyze` - Add job to analysis queue
- `GET /api/v1/analyzer/queue` - Get queue status
- `DELETE /api/v1/analyzer/queue/{id}` - Remove from queue
- `GET /api/v1/analyzer/saved` - List saved analyses
- `GET /api/v1/analyzer/saved/{id}` - Get analysis details
- `DELETE /api/v1/analyzer/saved/{id}` - Delete analysis
- `POST /api/v1/analyzer/requeue` - Requeue analyses for re-analysis
- `GET/PUT /api/v1/preferences` - User preferences (CV, guidelines)
- `GET /api/v1/digest/preview` - Preview next digest
- `POST /api/v1/digest/send` - Trigger digest email
- `GET /api/v1/digest/history` - List sent digests

## Environment Variables

Copy `.env.example` to `.env`. Key variables:

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `LLM_PROVIDER` - LLM provider (default: groq)
- `LLM_MODEL` - Model name (default: openai/gpt-oss-120b)
- `GROQ_API_KEY` - Groq API key (required)
- `SMTP_*`, `EMAIL_*` - Email digest settings

## Frontend Pages

- `/` - Job Analyzer (paste job description, view analysis)
- `/analyzed-jobs` - List of all analyzed jobs with select mode for requeue
- `/analyzed-jobs/{id}` - Detailed view of a single analysis
- `/digest` - Preview and send email digests
- `/settings` - Configure CV, guidelines, and preferences

## Project Structure

```
job-searcher/
├── backend/                    # FastAPI backend application
│   ├── alembic/               # Database migrations
│   │   └── versions/          # Migration files (001-006)
│   ├── app/                   # Main application code
│   │   ├── api/v1/endpoints/  # REST API endpoints (analyzer, preferences, digest)
│   │   ├── core/              # Configuration and settings
│   │   ├── db/                # Database session management
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── services/          # Business logic services
│   │   └── utils/             # Utility functions
│   ├── llm/                   # LLM integration
│   │   ├── client.py          # LiteLLM client with rate limiting
│   │   └── prompts/           # Analysis prompts (eligibility, matching, resume, cover letter)
│   ├── mailer/                # Email functionality
│   │   ├── sender.py          # SMTP email sender
│   │   └── templates/         # Jinja2 email templates (digest.html)
│   └── workers/               # Celery background workers
│       ├── celery_app.py      # Celery configuration
│       └── tasks/             # Task definitions (analyzer_queue, digest)
├── frontend/                  # Next.js frontend application
│   └── src/
│       ├── app/               # Next.js App Router pages
│       │   ├── page.tsx       # Home/Analyzer page
│       │   ├── analyzed-jobs/ # Analyzed jobs list and detail pages
│       │   ├── digest/        # Digest preview page
│       │   └── settings/      # Settings page
│       ├── components/        # Reusable React components
│       └── lib/
│           └── api/           # API client (client.ts)
├── infra/                     # Infrastructure configuration
│   ├── nginx/                 # Nginx reverse proxy config
│   └── vpn/                   # VPN configuration (legacy, unused)
├── docker-compose.yml         # Docker services orchestration
├── .env                       # Environment variables (not committed)
└── CLAUDE.md                  # This file
```
