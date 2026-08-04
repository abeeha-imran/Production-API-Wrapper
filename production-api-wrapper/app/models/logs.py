import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, DateTime, Text

from app.database import Base


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)
    status_code = Column(Integer, nullable=False)
    latency_ms = Column(Float, nullable=False)
    client_ip = Column(String, nullable=True)
    request_body = Column(Text, nullable=True)
    response_body = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
