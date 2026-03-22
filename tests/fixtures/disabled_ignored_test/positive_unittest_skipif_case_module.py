import unittest
from unittest import case as case_module


class TestExample(unittest.TestCase):
    @case_module.skipIf(True, "temporarily disabled")
    def test_example(self):
        self.assertTrue(True)
