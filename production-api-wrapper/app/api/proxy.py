from datetime import datetime, time as dtime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.limiter import limiter
from app.middleware.auth import verify_api_key
from app.models.logs import RequestLog
from app.schemas import (
    ChatRequest,
    StructuredResponse,
    HealthResponse,
    MetricsResponse,
    LogEntry,
)
from app.services.openai_service import get_chat_response
from app.utils import cache

router = APIRouter()


@router.post("/v1/chat", response_model=StructuredResponse, tags=["chat"])
@limiter.limit(settings.rate_limit)
async def chat(payload: ChatRequest, request: Request, _=Depends(verify_api_key)):
    request_id = getattr(request.state, "request_id", "unknown")
    try:
        response_text = await get_chat_response(payload.message)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="Something went wrong") from exc

    return StructuredResponse(
        success=True,
        data={"response": response_text},
        request_id=request_id,
    )


@router.get("/health", response_model=HealthResponse, tags=["ops"])
def health(db: Session = Depends(get_db)):
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_status = "error"

    cache_status = "ok"
    try:
        cache.set("__healthcheck__", "1", 5)
    except Exception:  # noqa: BLE001
        cache_status = "error"

    overall = "healthy" if db_status == "ok" and cache_status == "ok" else "degraded"
    return HealthResponse(status=overall, database=db_status, cache=cache_status)


@router.get("/metrics", response_model=MetricsResponse, tags=["ops"])
def metrics(db: Session = Depends(get_db)):
    today_start = datetime.combine(datetime.utcnow().date(), dtime.min)

    query = db.query(RequestLog).filter(RequestLog.timestamp >= today_start)
    total = query.count()
    successful = query.filter(RequestLog.status_code < 400).count()
    errors = query.filter(RequestLog.status_code >= 400).count()
    avg_latency = db.query(func.avg(RequestLog.latency_ms)).filter(
        RequestLog.timestamp >= today_start
    ).scalar() or 0.0

    return MetricsResponse(
        requests_today=total,
        successful_requests=successful,
        error_requests=errors,
        average_latency_ms=round(avg_latency, 2),
    )


@router.get("/logs", response_model=list[LogEntry], tags=["ops"])
def logs(limit: int = 50, db: Session = Depends(get_db), _=Depends(verify_api_key)):
    limit = max(1, min(limit, 200))
    rows = (
        db.query(RequestLog)
        .order_by(RequestLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        LogEntry(
            id=r.id,
            endpoint=r.endpoint,
            method=r.method,
            status_code=r.status_code,
            latency_ms=r.latency_ms,
            timestamp=r.timestamp.isoformat(),
        )
        for r in rows
    ]
