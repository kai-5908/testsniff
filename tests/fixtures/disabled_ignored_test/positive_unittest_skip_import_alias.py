import unittest
from unittest import skip as unit_skip


class TestExample(unittest.TestCase):
    @unit_skip("temporarily disabled")
    def test_example(self):
        self.assertTrue(True)
