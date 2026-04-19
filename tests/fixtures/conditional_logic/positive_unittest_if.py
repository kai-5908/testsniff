import unittest


class TestExample(unittest.TestCase):
    def test_example(self):
        if self._should_check():
            self.assertTrue(True)

    def _should_check(self):
        return True
