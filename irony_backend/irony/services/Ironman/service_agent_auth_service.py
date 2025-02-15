from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Response
from irony.config.logger import logger
from irony.db import db
from irony.models import service
from irony.models.service_agent.service_agent import ServiceAgent, ServiceAgentRegister
from irony.models.service_agent.vo.login_user_vo import LoginUserData, LoginUserResponse
from irony.models.service_agent.vo.register_agent_response import (
    RegisterAgentData,
    RegisterAgentResponse,
)
from irony.models.service_agent.vo.user_login import UserLogin
from irony.util import auth

# Below is placeholder code
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


async def register_service_agent(user: ServiceAgentRegister) -> RegisterAgentResponse:
    try:
        if not user.mobile or not user.password or not user.confirm_password:
            raise HTTPException(
                status_code=400,
                detail="Mobile, Password or confirm password not provided",
            )

        if not user.name:
            raise HTTPException(status_code=400, detail="Name not provided")

        if not user.service_location_ids:
            raise HTTPException(status_code=400, detail="Service location not provided")

        if user.password != user.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")

        # Check if email is already registered
        db_user = await db.service_agent.find_one({"mobile": user.mobile})
        if db_user:
            raise HTTPException(status_code=400, detail="Mobile already registered")

        # Hash the password
        user.password = auth.hash_password(user.password)

        service_agent = ServiceAgent(**user.model_dump())
        # Save user to the database
        result = await db.service_agent.insert_one(
            service_agent.model_dump(exclude={"id"})
        )

        service_agent.id = result.inserted_id

        return RegisterAgentResponse(
            message="Service Agent crerated successfully.",
            data=RegisterAgentData(user=service_agent),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in register_service_agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Internal server error during registration"
        )


async def login_service_agent(response: Response, user: UserLogin) -> LoginUserResponse:
    try:
        if not user.mobile.strip() or not user.password.strip():
            raise HTTPException(
                status_code=400, detail="Mobile or Password not provided"
            )

        db_user = await db.service_agent.find_one({"mobile": user.mobile})
        if not db_user:
            raise HTTPException(status_code=401, detail="Invalid mobile or password")

        db_user = ServiceAgent(**db_user)
        if not auth.verify_password(user.password, db_user.password):
            raise HTTPException(status_code=401, detail="Invalid mobile or password")

        # Generate JWT token
        token = auth.create_access_token(
            data={"sub": user.mobile},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        response.set_cookie(
            key="auth_token",
            value=token,
            httponly=True,
            # secure=True,  # Use True in production with HTTPS
            secure=False,  # Use True in production with HTTPS
            # samesite="lax",
            samesite="none",
            expires=datetime.now(timezone.utc)
            + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        return LoginUserResponse(
            message="Success!",
            data=LoginUserData(access_token=token, token_type="bearer", user=db_user),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in login_service_agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Internal server error during login"
        )
