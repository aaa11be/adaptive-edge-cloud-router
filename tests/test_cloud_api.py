from fastapi.testclient import TestClient

from edge_cloud_router.api.cloud_server import app as cloud_app


cloud_client = TestClient(cloud_app)


def test_cloud_health() -> None:
    response = cloud_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_cloud_infer_mock() -> None:
    payload = {
        "request_id": "cloud-api-test-001",
        "prompt": "What is edge AI?",
        "task_type": "smoke",
        "metadata": {},
    }

    response = cloud_client.post("/infer", json=payload)

    assert response.status_code == 200

    data = response.json()
    assert data["request_id"] == "cloud-api-test-001"
    assert data["endpoint"] == "cloud"
    assert data["quality_score"] == 0.90
    assert data["configured_processing_delay_ms"] == 80.0
    assert data["configured_rtt_ms"] == 0.0
    assert data["server_processing_ms"] > 0
    assert data["success"] is True
    assert data["error_type"] is None