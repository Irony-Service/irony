from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Response

from irony.config import config
from irony.config.agent.auth_config import AuthConfig
from irony.config.logger import logger
from irony.db import db
from irony.exception.authentication_exception import AuthenticationException
from irony.models.service_agent.service_agent import ServiceAgent
from irony.models.service_agent.vo.auth.login_request import AgentLoginRequest
from irony.models.service_agent.vo.auth.login_response import (
    AgentLoginData,
    AgentLoginResponse,
)
from irony.models.service_agent.vo.auth.register_request import AgentRegisterRequest
from irony.models.service_agent.vo.auth.register_response import (
    AgentRegisterData,
    AgentRegisterResponse,
)
from irony.util import auth


def validate_registration_input(request: AgentRegisterRequest) -> None:
    """Validate registration input data"""
    if not request.mobile or not request.password or not request.confirm_password:
        raise AuthenticationException(
            "Mobile, Password or confirm password not provided"
        )

    if not request.name:
        raise AuthenticationException("Name not provided")

    if not request.service_location_ids:
        raise AuthenticationException("Service location not provided")

    if request.password != request.confirm_password:
        raise AuthenticationException("Passwords do not match")


async def check_existing_user(mobile: str) -> None:
    """Check if user already exists"""
    if await db.service_agent.find_one({"mobile": mobile}):
        raise AuthenticationException("Mobile already registered")


async def register_service_agent(
    request: AgentRegisterRequest,
) -> AgentRegisterResponse:
    """Register a new service agent"""
    try:
        validate_registration_input(request)
        await check_existing_user(request.mobile)  # type: ignore

        agent = ServiceAgent(
            **request.model_dump(exclude={"password", "confirm_password"}),
            password=auth.hash_password(request.password)  # type: ignore
        )

        db_insert_result = await db.service_agent.insert_one(
            agent.model_dump(exclude={"id"})
        )
        agent.id = db_insert_result.inserted_id
        agent.password = "lol"  # Clear password before returning

        return AgentRegisterResponse(
            message="Service Agent created successfully.",
            data=AgentRegisterData(user=agent),
        )
    except AuthenticationException:
        raise
    except Exception as e:
        logger.error("Error in register_service_agent: %s", e, exc_info=True)
        raise AuthenticationException(
            "Internal server error during registration", status_code=500
        ) from e


async def login_service_agent(
    response: Response, request: AgentLoginRequest
) -> AgentLoginResponse:
    try:
        # Check if mobile and password are provided
        if not request.mobile.strip() or not request.password.strip():
            raise HTTPException(
                status_code=400, detail="Mobile or Password not provided"
            )

        # Check if the user exists
        service_agent_record = await db.service_agent.find_one(
            {"mobile": request.mobile}
        )
        if not service_agent_record:
            raise HTTPException(status_code=401, detail="Invalid mobile or password")

        agent = ServiceAgent(**service_agent_record)

        # Verify the password
        if not auth.verify_password(request.password, agent.password):
            raise HTTPException(status_code=401, detail="Invalid mobile or password")

        # Generate JWT token
        token = auth.create_access_token(
            data={"sub": request.mobile},
            expires_delta=timedelta(minutes=AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        # Set the token in the cookie
        response.set_cookie(
            key="auth_token",
            value=token,
            httponly=True,
            secure=config.COOKIE_SECURE,  # Use True in production with HTTPS
            samesite="none" if config.COOKIE_SECURE else "lax",
            expires=datetime.now(timezone.utc)
            + timedelta(minutes=AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        return AgentLoginResponse(
            message="Success!",
            data=AgentLoginData(access_token=token, token_type="bearer", user=agent),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in login_service_agent: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500, detail="Internal server error during login"
        ) from e
