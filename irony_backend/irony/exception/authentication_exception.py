from fastapi import HTTPException


class AuthenticationException(HTTPException):
    """Custom exception for authentication related errors"""

    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)
