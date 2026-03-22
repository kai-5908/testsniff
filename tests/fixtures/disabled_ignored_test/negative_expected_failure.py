import unittest


class TestExample(unittest.TestCase):
    @unittest.expectedFailure
    def test_example(self):
        self.assertTrue(True)
