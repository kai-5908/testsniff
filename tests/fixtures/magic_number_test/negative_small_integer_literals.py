import unittest


def test_pytest_values(value):
    assert value == 0
    assert value == 1
    assert value == -1


class TestExample(unittest.TestCase):
    def test_example(self, value):
        self.assertEqual(value, 0)
        self.assertEqual(value, 1)
        self.assertEqual(value, -1)
