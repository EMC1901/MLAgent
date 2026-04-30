class BusinessException(Exception):
    def __init__(self, message: str, error_code: str = "BUSINESS_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ValidationException(BusinessException):
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message, error_code)


class NotFoundException(BusinessException):
    def __init__(self, message: str, error_code: str = "NOT_FOUND"):
        super().__init__(message, error_code)


class DatabaseException(BusinessException):
    def __init__(self, message: str, error_code: str = "DATABASE_ERROR"):
        super().__init__(message, error_code)
