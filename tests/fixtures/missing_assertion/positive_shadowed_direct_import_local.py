# ruff: noqa: F401, F811

from pytest import raises


def test_example():
    def raises(*args, **kwargs):
        return None

    raises(ValueError)
