import unittest


class TestExample(unittest.TestCase):
    def test_example(self, values):
        self.assertTrue(any(item == 200 for item in values))
