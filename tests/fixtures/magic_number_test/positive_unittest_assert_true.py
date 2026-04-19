import unittest


class TestExample(unittest.TestCase):
    def test_example(self, value):
        self.assertTrue(value == 200)
