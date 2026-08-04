import asyncio
import hashlib
import random

import httpx
from fastapi import HTTPException

from app.config import settings
from app.services.retry import retry_on_transient_errors
from app.utils import cache

OPENAI_URL = "https://api.openai.com/v1/chat/completions"

_MOCK_RESPONSES = [
    "Why don't programmers like nature? It has too many bugs.",
    "I told my computer I needed a break, and it said 'no problem, I'll go to sleep.'",
    "Why do Java developers wear glasses? Because they don't C#.",
    "There are 10 types of people in the world: those who understand binary, and those who don't.",
    "A SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?'",
]


def _cache_key(message: str) -> str:
    return "chat:" + hashlib.sha256(message.encode()).hexdigest()


async def _call_mock(message: str) -> str:
    """Simulates an LLM call with realistic latency, no network/cost involved.
    Enabled via USE_MOCK_LLM=true so the project can be demoed and tested
    without an OpenAI API key or incurring any token costs."""
    await asyncio.sleep(random.uniform(0.3, 0.8))
    reply = random.choice(_MOCK_RESPONSES)
    return f"[MOCK RESPONSE] {reply} (echoing your message: '{message[:80]}')"


@retry_on_transient_errors
async def _call_openai(message: str) -> str:
    if not settings.openai_api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.openai_model,
        "messages": [{"role": "user", "content": message}],
    }

    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        resp = await client.post(OPENAI_URL, headers=headers, json=payload)

    if resp.status_code == 429:
        raise HTTPException(status_code=429, detail="Upstream rate limit exceeded")
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Upstream error: {resp.text[:200]}")

    data = resp.json()
    return data["choices"][0]["message"]["content"]


async def get_chat_response(message: str) -> str:
    key = _cache_key(message)
    cached = cache.get(key)
    if cached is not None:
        return cached

    if settings.use_mock_llm:
        result = await _call_mock(message)
    else:
        result = await _call_openai(message)

    cache.set(key, result, settings.cache_ttl_seconds)
    return result
