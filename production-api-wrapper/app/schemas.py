from typing import Any, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class ChatData(BaseModel):
    response: str


class StructuredResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    request_id: str


class HealthResponse(BaseModel):
    status: str
    database: str
    cache: str


class MetricsResponse(BaseModel):
    requests_today: int
    successful_requests: int
    error_requests: int
    average_latency_ms: float


class LogEntry(BaseModel):
    id: str
    endpoint: str
    method: str
    status_code: int
    latency_ms: float
    timestamp: str

    class Config:
        from_attributes = True


class WebhookEvent(BaseModel):
    event_type: str
    payload: dict
