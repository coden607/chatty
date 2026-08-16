import sys
from unittest.mock import MagicMock, patch

# Mock heavy dependencies before importing the app
sys.modules["AUTOMATED_REVENUE_ENGINE"] = MagicMock()
sys.modules["AUTOMATED_CUSTOMER_ACQUISITION"] = MagicMock()
sys.modules["START_COMPLETE_AUTOMATION"] = MagicMock()

import asyncio
from AUTOMATION_API_SERVER import app
from fastapi.testclient import TestClient

def test_dashboard_all():
    client = TestClient(app)
    response = client.get("/api/dashboard/all")
    assert response.status_code == 200
    data = response.json()

    expected_keys = [
        "leads", "workflows", "agents", "tasks", "collab",
        "messages", "autonomy", "pipelines", "campaigns",
        "n8n", "transparency", "briefs", "grants",
        "experiments", "anomalies", "weekly"
    ]

    for key in expected_keys:
        assert key in data, f"Missing key: {key}"
        assert "error" not in data[key], f"Error in {key}: {data[key].get('error')}"

    print("✅ /api/dashboard/all verified successfully!")

def test_weekly_brief_cache():
    client = TestClient(app)

    # First call
    with patch("AUTOMATION_API_SERVER.transparency_log", [{"action": "test", "result": "ok", "details": "none"}]):
        with patch("AUTOMATION_API_SERVER.collab_feed", []):
            response1 = client.get("/api/weekly/brief")
            assert response1.status_code == 200
            data1 = response1.json()

            # Second call should be cached
            response2 = client.get("/api/weekly/brief")
            assert response2.status_code == 200
            data2 = response2.json()

            assert data1 == data2
            print("✅ /api/weekly/brief cache verified!")

if __name__ == "__main__":
    test_dashboard_all()
    test_weekly_brief_cache()
