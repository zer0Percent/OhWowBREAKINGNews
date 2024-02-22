class GetRawNewsException(Exception):
    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)

class DatabaseException(Exception):
    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)