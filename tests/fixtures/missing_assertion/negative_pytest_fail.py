from pytest import fail


def test_stops_after_unexpected_state():
    fail("unexpected state")
