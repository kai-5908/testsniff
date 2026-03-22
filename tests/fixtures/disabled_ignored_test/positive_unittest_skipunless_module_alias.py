import unittest as ut


class TestExample(ut.TestCase):
    @ut.skipUnless(False, "temporarily disabled")
    def test_example(self):
        self.assertTrue(True)
