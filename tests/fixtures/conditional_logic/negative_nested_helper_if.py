def test_example():
    def helper(value):
        if value:
            return True
        return False

    assert helper(True)
