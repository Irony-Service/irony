class AuthConfig:
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    MIN_PASSWORD_LENGTH: int = 8
