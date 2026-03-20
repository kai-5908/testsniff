# ruff: noqa: F401, F811

import pytest


def test_example(pytest):
    pytest.raises(ValueError)
