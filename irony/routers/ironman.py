from datetime import datetime, timedelta, timezone
import time
from fastapi import APIRouter, HTTPException, Response


from irony.db import db
from irony.models.fetch_adaptive_route_vo import FetchAdaptiveRouteRequest
from irony.models.fetch_order_details_vo import FetchOrderDetailsRequest
from irony.models.fetch_orders_vo import FetchOrderRequest
from irony.models.service_agent import ServiceAgent, ServiceAgentRegister
from irony.models.update_order_vo import UpdateOrderRequest
from irony.models.user import User
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from irony.models.user_login import UserLogin
from irony.models.user_registration import UserRegistration
from irony.services.Ironman import (
    fetch_adaptive_route_service,
    fetch_order_deatils_service,
    fetch_orders_service,
    update_order_service,
)
from irony.util import auth

router = APIRouter()

# Below is placeholder code


ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


@router.post("/login")
async def login(response: Response, user: UserLogin):
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
        samesite="lax",
        expires=datetime.now(timezone.utc)
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": db_user.model_dump(exclude={"password"}),
    }


@router.post("/register")
async def register(user: ServiceAgentRegister):
    # Check if passwords match
    if not user.mobile or not user.password or not user.confirm_password:
        raise HTTPException(
            status_code=400, detail="Mobile, Password or confirm password not provided"
        )

    if not user.name:
        raise HTTPException(status_code=400, detail="Name not provided")

    if not user.service_location_id:
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
    result = await db.service_agent.insert_one(service_agent.model_dump(exclude={"id"}))

    service_agent.id = result.inserted_id

    return {
        "message": "User registered successfully",
        "user": service_agent.model_dump(exclude={"password"}),
    }


@router.get("/protected-route")
async def protected_route(current_user: str = Depends(auth.get_current_user)):
    return {"message": f"Welcome, {current_user}!"}


@router.get("/fetchOrders")
async def fetchOrders(current_user: str = Depends(auth.get_current_user)):
    return await fetch_orders_service.fetch_orders(current_user)


@router.post("/fetchOrderDetails")
async def fetchOrderDetails(request: FetchOrderDetailsRequest):
    return await fetch_order_deatils_service.fetch_order_details(request)


@router.post("/updateOrder")
async def updateOrder(request: UpdateOrderRequest):
    return await update_order_service.update_order(request)


@router.post("/fetchAdaptiveRoute")
async def fetchAdaptiveRoute(request: FetchAdaptiveRouteRequest):
    pass
    # return await fetch_adaptive_route_service.fetch_route(request)
