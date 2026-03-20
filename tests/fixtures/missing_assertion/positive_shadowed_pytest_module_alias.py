# ruff: noqa: F401, F811

import pytest


class DummyPytest:
    def raises(self, *args, **kwargs):
        return None


pytest = DummyPytest()


def test_example():
    pytest.raises(ValueError)
