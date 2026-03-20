def test_creates_user(client):
    client.post("/users", json={"name": "alice"})
