class SortMeAPIException(Exception):
    status_code: int | None

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(str(message))
        self.status_code = status_code

class RequestException(SortMeAPIException):
    pass

class TooManyRequests(SortMeAPIException):
    pass
