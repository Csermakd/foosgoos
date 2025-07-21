from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_match():
    # SAMPLE, CHANGE LATER
    payload = {
        "player_ids": [1, 2],
        "date": "2025-07-21",
        "winner_id": 1
    }
    response = client.post("/matches/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data