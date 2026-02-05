# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Job Searcher is an automated job search system that scrapes job boards, filters listings using deterministic rules and LLM analysis, scores matches against user preferences, and delivers daily email digests. The system is designed for UK-based job seekers requiring visa sponsorship.

## Online Repository

The project is hosted on Github on this repository: https://github.com/emytrb/job-search.
The gh CLI (Github CLI) is correctly configured, you can use the `gh` commands to interact with the github repository.
When you have completed a significant feature, ask the user if they want you to commit & push.

## Commands

### Development

```bash
# Start all services
sudo docker-compose up

# Start specific services
sudo docker-compose up postgres redis backend frontend

# Backend only (requires postgres/redis running)
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend only
cd frontend && npm run dev

# Run database migrations
cd backend && alembic upgrade head

# Create new migration
cd backend && alembic revision --autogenerate -m "description"
```

:warning: Always use 'sudo' for docker and docker compose commands

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
# Scraping worker (routes through VPN proxy)
celery -A workers.celery_app worker -Q scraping -c 2 --loglevel=info

# Processing worker (hard filters)
celery -A workers.celery_app worker -Q processing -c 4 --loglevel=info

# LLM worker (must be -c 1 for Ollama)
celery -A workers.celery_app worker -Q llm -c 1 --loglevel=info

# Digest worker
celery -A workers.celery_app worker -Q digest -c 1 --loglevel=info

# Beat scheduler (triggers periodic scrapes)
celery -A workers.celery_app beat --loglevel=info
```

## Architecture

### Processing Pipeline

```
Scrapers → DB → Hard Filter → LLM Analysis → Scoring → Frontend/Digest
            ↓
      Celery Workers (4 specialized queues)
```

1. **Scraping** (`backend/scrapers/`): Playwright-based browser automation with rate limiting and VPN proxy support. Scrapers extend `BaseScraper` and implement `scrape_job_urls()` and `scrape_job_details()`.

2. **Hard Filtering** (`backend/app/services/hard_filter.py`): Regex-based rules eliminate ~80% of jobs before LLM. Checks: location (London/UK), job type (permanent only), sponsorship patterns, security clearance, experience requirements.

3. **LLM Analysis** (`backend/llm/client.py`): Uses LiteLLM to call local Ollama. Extracts seniority, tech stack, remote policy, sponsorship likelihood. Single-threaded worker to avoid overwhelming Ollama.

4. **Scoring** (`backend/app/services/scoring.py`): Weighted composite score with configurable weights: stack match (35%), seniority match (25%), sponsorship likelihood (25%), job quality (15%).

### Key Components

- **API**: FastAPI async app at `backend/app/main.py`, routes in `backend/app/api/v1/`
- **Models**: SQLAlchemy ORM in `backend/app/models/` (Job, LLMAnalysis, JobScore, UserPreferences, ScrapeSource, etc.)
- **Workers**: Celery tasks in `backend/workers/tasks/` with 4 queues: scraping, processing, llm, digest
- **Frontend**: Next.js app in `frontend/src/app/` with pages for jobs, digest, settings, sources

### Infrastructure

- PostgreSQL (async via asyncpg)
- Redis (Celery broker + cache)
- Ollama (local LLM, model: B-A-M-N/vibethinker:1.5b)
- VPN container (gluetun) for scraper IP protection
- Nginx reverse proxy

### Celery Beat Schedule

- Low-risk sources (Greenhouse, Lever): every 6 hours
- Medium-risk sources (WTTJ): every 12 hours
- High-risk sources (Indeed): daily at 3 AM UTC
- Daily digest: 8 AM UTC

## API Endpoints

- `GET/POST /api/v1/jobs` - List and manage jobs
- `GET/POST /api/v1/sources` - Manage scrape sources
- `POST /api/v1/sources/{id}/scrape` - Trigger manual scrape
- `GET/PUT /api/v1/preferences` - User preferences
- `GET /api/v1/digest` - Digest history

## Environment Variables

Copy `.env.example` to `.env`. Key variables:

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `OLLAMA_BASE_URL`, `OLLAMA_MODEL` - LLM configuration
- `SMTP_*`, `EMAIL_*` - Email digest settings
- `VPN_*` - VPN provider configuration for gluetun

## Adding New Scrapers

1. Create new file in `backend/scrapers/` extending `BaseScraper`
2. Implement `get_job_listings_url()`, `scrape_job_urls()`, `scrape_job_details()`
3. Use `self.rate_limiter` and `self.fetch_with_rate_limit()` for all requests
4. Register in appropriate risk level (affects scrape frequency)
