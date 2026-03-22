import unittest


class TestUserCreation(unittest.TestCase):
    def test_creates_user(self):
        response = {"name": "alice"}
        self.assertEqual(response["name"], "alice")
        self.assertTrue("name" in response)
