import time
import uuid
from typing import Any, Optional


def new_request_id() -> str:
    return str(uuid.uuid4())


class TTLCache:
    """Simple in-memory TTL cache. Swap for Redis in production by
    implementing the same get/set interface against a Redis client."""

    def __init__(self):
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        item = self._store.get(key)
        if not item:
            return None
        expires_at, value = item
        if time.time() > expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._store[key] = (time.time() + ttl_seconds, value)


cache = TTLCache()
