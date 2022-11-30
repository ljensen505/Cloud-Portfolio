class ParamError(Exception):
    def __init__(self, error: dict, status_code: int):
        self.error: dict = error
        self.status_code: int = status_code


class IdError(Exception):
    def __init__(self, error: dict, status_code: int):
        self.error: dict = error
        self.status_code: int = status_code
