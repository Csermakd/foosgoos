from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_user():
    response = client.post("/users/", json={"name": "testuser"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "testuser"
    assert "id" in data