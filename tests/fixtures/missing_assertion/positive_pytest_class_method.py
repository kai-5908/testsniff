class TestUserCreation:
    def test_creates_user(self, client):
        client.post("/users", json={"name": "alice"})
