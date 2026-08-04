from unittest.mock import patch


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "docs" in resp.json()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in {"healthy", "degraded"}


def test_chat_requires_auth(client):
    resp = client.post("/v1/chat", json={"message": "hi"})
    assert resp.status_code == 401


def test_chat_rejects_invalid_key(client):
    resp = client.post(
        "/v1/chat",
        json={"message": "hi"},
        headers={"Authorization": "Bearer wrong-key"},
    )
    assert resp.status_code == 401


def test_chat_validates_empty_message(client, auth_headers):
    resp = client.post("/v1/chat", json={"message": ""}, headers=auth_headers)
    assert resp.status_code == 422


def test_chat_success(client, auth_headers):
    with patch(
        "app.api.proxy.get_chat_response",
        return_value="Why did the chicken cross the road?",
    ):
        resp = client.post(
            "/v1/chat", json={"message": "Tell me a joke"}, headers=auth_headers
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "response" in body["data"]
    assert "request_id" in body


def test_logs_requires_auth(client):
    resp = client.get("/logs")
    assert resp.status_code == 401


def test_metrics(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.json()
    assert "requests_today" in body


def test_webhook_rejects_bad_signature(client):
    resp = client.post(
        "/webhook",
        json={"event_type": "test", "payload": {}},
        headers={"X-Signature": "bad"},
    )
    assert resp.status_code == 401
