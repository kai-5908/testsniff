from pytest import mark


@mark.skip(reason="temporarily disabled")
def test_example():
    assert True
