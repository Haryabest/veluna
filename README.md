# Veluna

Production-ready Telegram Mini App — AI Anime Waifu / AI Girlfriend platform.

## Architecture

```
veluna/
├── frontend/          # Next.js 15 + TypeScript + TailwindCSS
├── backend/           # FastAPI + PostgreSQL + Redis + Celery
├── nginx/             # Reverse proxy
├── docker-compose.yml # Full stack orchestration
└── .env.example       # Environment template
```

### Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | Next.js 15, TypeScript, TailwindCSS, Zustand, TanStack Query, Framer Motion, Telegram Mini Apps SDK |
| Backend | FastAPI, SQLAlchemy, Alembic, JWT, WebSockets |
| Data | PostgreSQL, Redis |
| Workers | Celery (generation, chat, analytics queues) + Celery Beat |
| Storage | MinIO (S3-compatible) |
| Infra | Docker, Docker Compose, Nginx |

## Quick Start (Docker)

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env — set SECRET_KEY, JWT_SECRET_KEY, TELEGRAM_BOT_TOKEN, AI keys

# 2. Start all services
docker compose up -d --build

# 3. Run database migrations
docker compose exec backend alembic upgrade head

# 4. Open
# Frontend:  http://localhost:3000
# Backend:   http://localhost:8000/docs
# MinIO:     http://localhost:9001 (console)
# Nginx:     http://localhost
```

## Local Development

### Prerequisites

- Node.js 20+
- Python 3.12+
- PostgreSQL 16
- Redis 7
- MinIO (optional for storage)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Set env vars (or use .env in project root)
export DATABASE_URL=postgresql+asyncpg://veluna:veluna_secret@localhost:5432/veluna
export SECRET_KEY=your-secret-key-min-32-chars-long!!
export JWT_SECRET_KEY=your-jwt-secret-key-min-32-chars!!

# Run migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Celery Workers

```bash
# Terminal 1 — Generation worker
celery -A app.workers.celery_app worker -Q generation_queue -c 2 --loglevel=info -n generation@%h

# Terminal 2 — Chat worker
celery -A app.workers.celery_app worker -Q chat_queue -c 4 --loglevel=info -n chat@%h

# Terminal 3 — Analytics worker
celery -A app.workers.celery_app worker -Q analytics_queue -c 2 --loglevel=info -n analytics@%h

# Terminal 4 — Beat scheduler
celery -A app.workers.celery_app beat --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
cp ../.env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
# Set NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

npm run dev
# Open http://localhost:3000
```

## Environment Configuration

Copy `.env.example` to `.env` and configure:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | App secret (min 32 chars) |
| `JWT_SECRET_KEY` | JWT signing key |
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather |
| `DATABASE_URL` | PostgreSQL async connection string |
| `REDIS_URL` | Redis connection |
| `AI_CHAT_PROVIDER` | `openai` / `openrouter` / `groq` |
| `IMAGE_PROVIDER` | `fal` / `replicate` |
| `STORAGE_PROVIDER` | `minio` / `s3` |
| `ADMIN_TELEGRAM_IDS` | Comma-separated admin Telegram IDs |

## Project Structure

### Backend

```
backend/app/
├── api/v1/           # REST endpoints (versioned)
├── core/             # Config, security, logging, telegram validation
├── database/         # SQLAlchemy session, Redis
├── models/           # PostgreSQL models
├── schemas/          # Pydantic schemas
├── repositories/     # Data access layer
├── services/         # Business logic
├── providers/        # AI & storage abstraction
│   ├── ai/           # Chat + image providers
│   └── storage/      # MinIO / S3 providers
├── websocket/        # Real-time chat manager
├── workers/          # Celery app config
├── tasks/            # Background tasks
└── middleware/       # Rate limiting, logging
```

### Frontend

```
frontend/src/
├── app/              # Next.js App Router pages
├── components/
│   ├── shared/       # UI kit (Button, Card, Skeleton...)
│   ├── entities/     # Domain components
│   └── widgets/      # Composed widgets
├── features/         # Feature modules (auth, chat...)
├── services/         # API layer
├── store/            # Zustand stores
├── hooks/            # Custom hooks
└── lib/              # Utils, constants, api-client
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/telegram` | Telegram initData auth |
| GET | `/api/v1/users/me` | Current user |
| GET | `/api/v1/characters` | List characters |
| POST | `/api/v1/chats` | Start chat |
| POST | `/api/v1/chats/{id}/messages` | Send message |
| POST | `/api/v1/generations` | Queue image generation |
| GET | `/api/v1/payments/balance` | Gem balance |
| GET | `/api/v1/admin/stats` | Admin statistics |
| WS | `/ws/chat/{chat_id}` | Real-time chat |

## Celery Queues

| Queue | Worker | Purpose |
|-------|--------|---------|
| `generation_queue` | worker-generation | Image generation (async) |
| `chat_queue` | worker-chat | AI response processing |
| `analytics_queue` | worker-analytics | Event tracking, aggregation |

### Scheduled Jobs (Celery Beat)

- Session cleanup — every 30 min
- Analytics aggregation — daily at 02:00 UTC
- Inactive chat cleanup — daily at 03:00 UTC
- Cache cleanup — every 6 hours
- Failed generation cleanup — daily at 04:00 UTC

## Provider System

AI and storage providers are swappable via environment variables:

```python
# Change provider without touching business logic
AI_CHAT_PROVIDER=openrouter
IMAGE_PROVIDER=replicate
STORAGE_PROVIDER=s3
```

Available implementations:
- **Chat**: OpenAI, OpenRouter, Groq
- **Image**: Fal, Replicate
- **Storage**: MinIO, S3

## Database Migrations

```bash
# Create migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Apply
docker compose exec backend alembic upgrade head

# Rollback
docker compose exec backend alembic downgrade -1
```

## MinIO Storage

Buckets structure:
```
veluna/
├── characters/    # Character avatars & previews
├── generations/   # Generated images
├── users/         # User uploads
└── previews/      # Public preview images
```

Console: http://localhost:9001 (credentials from `.env`)

## WebSocket

Connect with JWT token:
```
ws://localhost:8000/ws/chat/{chat_id}?token={access_token}
```

Message types: `message`, `typing`, `ping`/`pong`, `generation_update`

## License

Proprietary — All rights reserved.
