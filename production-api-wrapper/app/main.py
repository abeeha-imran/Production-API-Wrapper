from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from loguru import logger

from app.api import proxy, webhooks
from app.config import settings
from app.database import init_db
from app.limiter import limiter
from app.middleware.logging import RequestLoggingMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info(f"Starting Production API Wrapper (env={settings.environment})")
    yield


app = FastAPI(
    title="Production API Wrapper",
    description="A production-style FastAPI wrapper around the OpenAI API, "
    "demonstrating backend engineering practices: auth, rate limiting, "
    "caching, retries, logging, and observability.",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(proxy.router, prefix="")
app.include_router(webhooks.router, prefix="")


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Something went wrong", "data": None},
    )


@app.get("/", tags=["root"])
def root():
    return {
        "name": "Production API Wrapper",
        "docs": "/docs",
        "health": "/health",
    }
