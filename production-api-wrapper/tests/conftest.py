import os

os.environ.setdefault("API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import init_db

init_db()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-key"}
