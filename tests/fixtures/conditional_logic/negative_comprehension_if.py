def test_example(values):
    filtered = [value for value in values if value]
    assert filtered == values
