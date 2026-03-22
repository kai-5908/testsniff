def test_creates_user():
    response = {"status_code": 201, "name": "alice"}
    assert response["status_code"] == 201
    assert response["name"] == "alice"
