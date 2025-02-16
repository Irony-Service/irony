from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Response
from irony.config.logger import logger
from irony.db import db
from irony.models import service
from irony.models.service_agent.service_agent import ServiceAgent
from irony.models.service_agent.vo.auth.login_response import (
    AgentLoginData,
    AgentLoginResponse,
)
from irony.models.service_agent.vo.auth.register_response import (
    AgentRegisterData,
    AgentRegisterResponse,
)
from irony.models.service_agent.vo.auth.login_request import AgentLoginRequest
from irony.models.service_agent.vo.auth.register_request import AgentRegisterRequest
from irony.util import auth
from irony import main

# Below is placeholder code
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


async def register_service_agent(
    request: AgentRegisterRequest,
) -> AgentRegisterResponse:
    try:
        if not request.mobile or not request.password or not request.confirm_password:
            raise HTTPException(
                status_code=400,
                detail="Mobile, Password or confirm password not provided",
            )

        if not request.name:
            raise HTTPException(status_code=400, detail="Name not provided")

        if not request.service_location_ids:
            raise HTTPException(status_code=400, detail="Service location not provided")

        if request.password != request.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")

        # Check if email is already registered
        db_user = await db.service_agent.find_one({"mobile": request.mobile})
        if db_user:
            raise HTTPException(status_code=400, detail="Mobile already registered")

        # Hash the password
        request.password = auth.hash_password(request.password)

        agent = ServiceAgent(**request.model_dump())
        # Save user to the database
        db_insert_result = await db.service_agent.insert_one(
            agent.model_dump(exclude={"id"})
        )
        agent.id = db_insert_result.inserted_id
        agent.password = None

        return AgentRegisterResponse(
            message="Service Agent crerated successfully.",
            data=AgentRegisterData(user=agent),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in register_service_agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Internal server error during registration"
        )


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
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        # Set the token in the cookie
        response.set_cookie(
            key="auth_token",
            value=token,
            httponly=True,
            secure=main.cookie_secure,  # Use True in production with HTTPS
            # samesite="lax",
            samesite="none",
            expires=datetime.now(timezone.utc)
            + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        return AgentLoginResponse(
            message="Success!",
            data=AgentLoginData(access_token=token, token_type="bearer", user=agent),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in login_service_agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Internal server error during login"
        )
