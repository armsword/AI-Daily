import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


def test_index_page(client):
    with patch("app.main.get_latest_reports") as mock_get:
        mock_get.return_value = []
        response = client.get("/")
        assert response.status_code == 200
        assert "AI Daily" in response.text


def test_api_reports(client):
    with patch("app.main.get_latest_reports") as mock_get:
        mock_get.return_value = []
        response = client.get("/api/reports")
        assert response.status_code == 200
        assert response.json() == []
