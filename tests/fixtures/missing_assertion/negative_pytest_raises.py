import pytest


def create_user(name: str) -> None:
    if not name:
        raise ValueError("name is required")


def test_rejects_invalid_user():
    with pytest.raises(ValueError):
        create_user("")
