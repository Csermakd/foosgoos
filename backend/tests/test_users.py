from main import app

def test_create_user(client):
    response = client.post("/users/", json={"name": "testuser"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "testuser"
    assert "id" in data