import unittest


class TestUserCreation(unittest.TestCase):
    def test_creates_user(self):
        create_user("alice")


def create_user(name: str) -> dict[str, str]:
    return {"name": name}
