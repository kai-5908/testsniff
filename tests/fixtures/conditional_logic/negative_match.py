def test_example(value):
    match value:
        case "a":
            assert True
        case _:
            assert True
