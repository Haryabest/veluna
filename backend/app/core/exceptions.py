from fastapi import HTTPException, status


class VelunaError(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(VelunaError):
    def __init__(self, resource: str, identifier: str | int):
        super().__init__(f"{resource} not found: {identifier}", code="NOT_FOUND")


class ForbiddenError(VelunaError):
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, code="FORBIDDEN")


class InsufficientBalanceError(VelunaError):
    def __init__(self, required: int, available: int):
        super().__init__(
            f"Insufficient gems: required {required}, available {available}",
            code="INSUFFICIENT_BALANCE",
        )


class RateLimitError(VelunaError):
    def __init__(self):
        super().__init__("Rate limit exceeded", code="RATE_LIMIT")


class ValidationError(VelunaError):
    def __init__(self, message: str):
        super().__init__(message, code="VALIDATION_ERROR")


def veluna_error_handler(_request, exc: VelunaError):
    status_map = {
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "FORBIDDEN": status.HTTP_403_FORBIDDEN,
        "INSUFFICIENT_BALANCE": status.HTTP_402_PAYMENT_REQUIRED,
        "RATE_LIMIT": status.HTTP_429_TOO_MANY_REQUESTS,
    }
    return HTTPException(
        status_code=status_map.get(exc.code, status.HTTP_400_BAD_REQUEST),
        detail={"code": exc.code, "message": exc.message},
    )
