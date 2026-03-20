from pytest import raises as expect_raises


def create_user(name: str) -> None:
    if not name:
        raise ValueError("name is required")


def test_rejects_invalid_user():
    with expect_raises(ValueError):
        create_user("")
