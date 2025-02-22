from typing import Dict
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta, timezone

# Bcrypt
# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"


def create_access_token(data: Dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")


# Custom function to handle token from both cookies and Authorization header
def get_token_from_request(request: Request) -> str:
    # Check if the token is present in cookies
    if "auth_token" in request.cookies:
        token = request.cookies.get("auth_token")
        if token:
            return token
    # Check the Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header:
        scheme, token = get_authorization_scheme_param(auth_header)
        if scheme.lower() == "bearer" and token:
            return token

    # Raise an exception if no token is found
    raise HTTPException(status_code=401, detail="User not logged in. Please log in.")


def get_current_user(request: Request, token: str = Depends(get_token_from_request)):
    try:
        payload = verify_access_token(token)
        return payload["sub"]
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
