import unittest


class User:
    def __init__(self, name: str) -> None:
        self.name = name


def create_user(name: str) -> User:
    return User(name)


class TestUserCreation(unittest.TestCase):
    def test_creates_user(self):
        response = create_user("alice")
        self.assertEqual(response.name, "alice")
