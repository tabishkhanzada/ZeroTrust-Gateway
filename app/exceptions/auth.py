from fastapi import HTTPException, status


class AuthException(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(status_code=status_code, detail=detail)

class UserAlreadyExistsException(AuthException):
    def __init__(self):
        super().__init__(
            detail="User with this email already exists",
            status_code=status.HTTP_400_BAD_REQUEST
        )

class InvalidCredentialsException(AuthException):
    def __init__(self):
        super().__init__(detail="Invalid email or password")

class TokenExpiredException(AuthException):
    def __init__(self):
        super().__init__(detail="Token has expired")

class TokenInvalidException(AuthException):
    def __init__(self):
        super().__init__(detail="Invalid token")

class TokenBlacklistedException(AuthException):
    def __init__(self):
        super().__init__(detail="Token has been revoked")
