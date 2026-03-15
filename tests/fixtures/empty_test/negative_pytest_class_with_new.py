class TestWithNew:
    def __new__(cls):
        return super().__new__(cls)

    def test_placeholder(self):
        pass
