class BackendError(Exception):
    def __init__(self, status: int, error_type: str, message: str):
        self.status = status
        self.error_type = error_type
        self.message = message
        super().__init__(f"{error_type}: {message}")
