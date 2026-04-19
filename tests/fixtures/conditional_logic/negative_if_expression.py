def test_example(value):
    result = 1 if value else 0
    assert result in {0, 1}
