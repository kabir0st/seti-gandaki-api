class ValidationException(Exception):
    """Custom exception for validation errors."""

    def __init__(self, message):
        super().__init__(message)
