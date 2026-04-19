def test_example(client):
    response = client.get("/users", timeout=30)
    assert response.ok
