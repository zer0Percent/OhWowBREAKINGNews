class NewRetrieverThreadException(Exception):
    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)

class ScrapeNewException(NewRetrieverThreadException):
    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)

class NewRawModeException(ScrapeNewException):
    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)

class NewReaderModeException(ScrapeNewException):
    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)

class NewWithPaywallMethod(ScrapeNewException):
    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)

class WebArchiveException(Exception):
    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)

class GetRequestWebArchiveException(WebArchiveException):
    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)

class CandidateWebArchiveUrlException(NewRetrieverThreadException):
    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)