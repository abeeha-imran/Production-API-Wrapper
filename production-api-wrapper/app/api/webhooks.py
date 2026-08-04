import hashlib
import hmac

from fastapi import APIRouter, Header, HTTPException, Request

from app.config import settings

router = APIRouter()

WEBHOOK_SECRET = settings.api_key  # reuse api_key as webhook signing secret for demo purposes


def _verify_signature(body: bytes, signature: str) -> bool:
    expected = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature or "")


@router.post("/webhook", tags=["webhooks"])
async def receive_webhook(request: Request, x_signature: str = Header(default="")):
    body = await request.body()

    if not _verify_signature(body, x_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()
    # In a real system: dispatch payload["event_type"] to a handler / queue.
    return {"success": True, "received_event": payload.get("event_type", "unknown")}
