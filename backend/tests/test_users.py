from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
#SAMPLE_TEST
def test_create_user():
    response = client.post("/users/", json={"username": "testuser"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert "id" in data