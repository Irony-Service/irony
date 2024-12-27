from datetime import timedelta
from fastapi import APIRouter, HTTPException


from irony.db import db
from irony.models.service_agent import ServiceAgent, ServiceAgentRegister
from irony.models.user import User
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from irony.models.user_login import UserLogin
from irony.models.user_registration import UserRegistration
from irony.util import auth

router = APIRouter()

# Below is placeholder code


ACCESS_TOKEN_EXPIRE_MINUTES = 30

@router.post("/login")
async def login(user: UserLogin):
    db_user = await db.service_agent.find_one({"mobile": user.mobile})
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid mobile or password")
    
    db_user = ServiceAgent(**db_user)
    if auth.verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid mobile or password")
    
    # Generate JWT token
    token = auth.create_access_token(
        data={"sub": user.mobile},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer", "user": db_user.model_dump(exclude={"password"})}

@router.post("/register")
async def register(user: ServiceAgentRegister):
    # Check if passwords match
    if not user.mobile or not user.password or not user.confirm_password:
        raise HTTPException(status_code=400, detail="Mobile, Password or confirm password not provided")
    
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

    return {"message": "User registered successfully", "user": service_agent.model_dump(exclude={"password"})}

@router.get("/protected-route")
async def protected_route(current_user: str = Depends(auth.get_current_user)):
    return {"message": f"Welcome, {current_user}!"}

