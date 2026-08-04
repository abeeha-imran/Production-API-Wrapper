# Production API Wrapper

A production-style FastAPI service that wraps the OpenAI API, demonstrating
backend engineering practices beyond "just calling an LLM": authentication,
rate limiting, caching, retries, structured logging, observability, testing,
containerization, and CI/CD.

## Architecture

```text
                Client
                   │
                   ▼
        FastAPI Production Wrapper
                   │
     ┌─────────────┼─────────────┐
     │             │             │
 Authentication  Rate Limit   Validation
     │             │             │
     └─────────────┼─────────────┘
                   ▼
          Logging Middleware
                   ▼
          Cache (in-memory TTL)
                   ▼
        OpenAI Service (httpx)
                   ▼
      Retry + Timeout + Errors
                   ▼
          OpenAI API (external)
                   ▲
                   │
         Save Logs (per-request)
                   │
              SQLite / Postgres
```

## Demo Without Any Cost

Set `USE_MOCK_LLM=true` in `.env` to run the entire app — auth, caching,
rate limiting, retries, logging, metrics — without a real `OPENAI_API_KEY`
and without spending a single token. `/v1/chat` will return a simulated
response with realistic latency instead of calling OpenAI. Flip it to
`false` (with a real key set) to hit the live API.

## Tech Stack
*Python • FastAPI • Uvicorn • Pydantic • httpx • Redis • SQLAlchemy • PostgreSQL • Docker • GitHub Actions • Pytest**


## Features

- **`POST /v1/chat`** – proxies a chat message to OpenAI, cached and rate-limited
- **`GET /health`** – checks DB and cache connectivity
- **`GET /metrics`** – requests today, success/error counts, average latency
- **`GET /logs`** – recent request history from the database
- **`POST /webhook`** – HMAC-signature-verified webhook receiver
- API key authentication (`Authorization: Bearer <key>`)
- Rate limiting (SlowAPI, per-client, configurable)
- Retry with exponential backoff for transient upstream failures (`tenacity`)
- Request timeouts on all outbound HTTP calls
- Response caching (in-memory TTL cache; swap for Redis by implementing the
  same `get`/`set` interface in `app/utils.py`)
- Structured JSON-style responses (`success`, `data`, `error`, `request_id`)
- Request ID + response-time headers on every response
- Centralized error handling — no raw exceptions ever reach the client
- Auto-generated OpenAPI docs at `/docs` and `/redoc`
- GZip response compression
- CORS enabled for frontend integration
- SQLite by default, swappable to Postgres via `DATABASE_URL`
- Dockerized with a healthcheck
- GitHub Actions CI (lint, format check, tests)
- Full pytest suite covering auth, validation, rate limiting, and success paths

## Project Structure

```
production-api-wrapper/
├── app/
│   ├── main.py              # app factory, middleware, CORS, exception handlers
│   ├── config.py            # pydantic-settings based configuration
│   ├── limiter.py           # shared SlowAPI limiter instance
│   ├── database.py          # SQLAlchemy engine/session
│   ├── schemas.py           # Pydantic request/response models
│   ├── utils.py             # request IDs, in-memory TTL cache
│   ├── api/
│   │   ├── proxy.py         # /v1/chat, /health, /metrics, /logs
│   │   └── webhooks.py      # /webhook with HMAC verification
│   ├── services/
│   │   ├── openai_service.py  # OpenAI call + caching
│   │   └── retry.py           # tenacity retry policy
│   ├── middleware/
│   │   ├── auth.py          # API key dependency
│   │   └── logging.py       # request logging middleware
│   └── models/
│       └── logs.py          # RequestLog ORM model
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .github/workflows/ci.yml
└── .env.example
```

## Running Locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # fill in OPENAI_API_KEY and API_KEY

uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API docs.

### Example request

```bash
curl -X POST http://localhost:8000/v1/chat \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me a joke"}'
```

```json
{
  "success": true,
  "data": { "response": "..." },
  "request_id": "4f9bc3e2-..."
}
```

## Testing

```bash
pytest -v
```

Tests cover health checks, auth enforcement, request validation, the happy
path (with the OpenAI call mocked), log/metrics endpoints, and webhook
signature verification.

## Docker

```bash
docker build -t production-api-wrapper .
docker run -p 8000:8000 --env-file .env production-api-wrapper
```

Or with Compose (also useful as a base for adding Postgres/Redis services):

```bash
docker compose up --build
```

## Deployment (Render)

1. Push this repo to GitHub.
2. Create a new Web Service on Render, connected to the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables: `OPENAI_API_KEY`, `API_KEY`, `DATABASE_URL`, `RATE_LIMIT`
6. Deploy, then verify `/health` and `/docs` on the generated URL.

## CI/CD

`.github/workflows/ci.yml` runs on every push/PR to `main`:

```
checkout → install deps → ruff lint → black --check → pytest
```

## Notes on Production Hardening

- Swap the in-memory `TTLCache` for Redis by implementing the same
  `get(key)` / `set(key, value, ttl)` interface against `redis-py`.
- Swap SQLite for Postgres by changing `DATABASE_URL` — SQLAlchemy handles
  the rest; add Alembic migrations for schema changes.
- The webhook endpoint currently reuses `API_KEY` as its HMAC secret for
  simplicity — use a dedicated `WEBHOOK_SECRET` in a real deployment.
- Add `/v1/` and `/v2/` prefixes as needed for API versioning as the service
  evolves.
