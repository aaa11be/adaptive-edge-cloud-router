from fastapi.testclient import TestClient

from edge_cloud_router.api.server import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    
def test_infer_local_mock() -> None:
    payload = {
        "request_id": "api-test-001",
        "prompt": "What is edge AI?",
        "task_type": "smoke",
        "metadata": {},
    }

    response = client.post("/infer", json=payload)

    assert response.status_code == 200

    data = response.json()
    assert data["request_id"] == "api-test-001"
    assert data["endpoint"] == "local"
    assert data["quality_score"] == 0.60
    assert data["configured_processing_delay_ms"] == 20.0
    assert data["configured_rtt_ms"] == 0.0
    assert data["server_processing_ms"] > 0
    assert data["success"] is True
    assert data["error_type"] is None