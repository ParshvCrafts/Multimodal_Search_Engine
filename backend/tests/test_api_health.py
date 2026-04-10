from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from backend.app.main import app


def _make_mock_engine(ready=True, n_products=100):
    engine = MagicMock()
    engine._is_ready = ready
    engine.metadata = MagicMock()
    engine.metadata.__len__ = MagicMock(return_value=n_products)
    engine.audit.return_value = {"status": "ready", "products": n_products}
    return engine


class TestHealthEndpoints:
    def test_health_ok(self):
        client = TestClient(app, raise_server_exceptions=False)
        app.state.engine = _make_mock_engine()
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["engine_ready"] is True
        assert data["products"] == 100

    def test_health_not_ready(self):
        client = TestClient(app, raise_server_exceptions=False)
        app.state.engine = _make_mock_engine(ready=False)
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["engine_ready"] is False

    def test_health_no_engine(self):
        client = TestClient(app, raise_server_exceptions=False)
        app.state.engine = None
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["engine_ready"] is False

    def test_audit(self):
        client = TestClient(app, raise_server_exceptions=False)
        app.state.engine = _make_mock_engine()
        response = client.get("/api/v1/audit")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
