def test_creates_user(client):
    response = client.post("/users", json={"name": "alice"})
    assert response.status_code == 201
