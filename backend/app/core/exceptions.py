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


class AccountBannedError(VelunaError):
    def __init__(self, ban_reason: str | None, banned_until):
        from app.services.user_ban_service import format_ban_message

        super().__init__(format_ban_message(ban_reason, banned_until), code="ACCOUNT_BANNED")
        self.ban_reason = ban_reason
        self.banned_until = banned_until


class InsufficientBalanceError(VelunaError):
    def __init__(self, required: int, available: int, *, currency: str = "gems"):
        if currency == "credits":
            message = f"Недостаточно сердец: нужно {required}, доступно {available}"
        else:
            message = f"Недостаточно гемов: нужно {required}, доступно {available}"
        super().__init__(message, code="INSUFFICIENT_BALANCE")


class RateLimitError(VelunaError):
    def __init__(self):
        super().__init__("Rate limit exceeded", code="RATE_LIMIT")


class ValidationError(VelunaError):
    def __init__(self, message: str):
        super().__init__(message, code="VALIDATION_ERROR")


class ServiceUnavailableError(VelunaError):
    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(message, code="SERVICE_UNAVAILABLE")


def veluna_error_handler(_request, exc: VelunaError):
    status_map = {
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "FORBIDDEN": status.HTTP_403_FORBIDDEN,
        "ACCOUNT_BANNED": status.HTTP_403_FORBIDDEN,
        "INSUFFICIENT_BALANCE": status.HTTP_402_PAYMENT_REQUIRED,
        "RATE_LIMIT": status.HTTP_429_TOO_MANY_REQUESTS,
    }
    detail: dict = {"code": exc.code, "message": exc.message}
    if isinstance(exc, AccountBannedError):
        detail["ban_reason"] = exc.ban_reason
        detail["banned_until"] = (
            exc.banned_until.isoformat() if exc.banned_until is not None else None
        )
    return HTTPException(
        status_code=status_map.get(exc.code, status.HTTP_400_BAD_REQUEST),
        detail=detail,
    )
