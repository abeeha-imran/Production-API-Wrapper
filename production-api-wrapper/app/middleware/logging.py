import time

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from app.database import SessionLocal
from app.models.logs import RequestLog
from app.utils import new_request_id


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = new_request_id()
        request.state.request_id = request_id
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as exc:  # noqa: BLE001
            latency_ms = (time.perf_counter() - start) * 1000
            self._save_log(
                endpoint=request.url.path,
                method=request.method,
                status_code=500,
                latency_ms=latency_ms,
                client_ip=request.client.host if request.client else None,
                error=str(exc),
            )
            logger.exception(f"[{request_id}] Unhandled error")
            raise

        latency_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = f"{latency_ms:.2f}"

        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"-> {response.status_code} ({latency_ms:.2f}ms)"
        )

        self._save_log(
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            latency_ms=latency_ms,
            client_ip=request.client.host if request.client else None,
        )

        return response

    @staticmethod
    def _save_log(**kwargs):
        # Skip noisy/system endpoints
        if kwargs.get("endpoint") in {"/docs", "/openapi.json", "/redoc", "/favicon.ico"}:
            return
        db = SessionLocal()
        try:
            db.add(RequestLog(**kwargs))
            db.commit()
        except Exception:  # noqa: BLE001
            db.rollback()
        finally:
            db.close()
