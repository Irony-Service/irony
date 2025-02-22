from fastapi import APIRouter, Depends, Response

from irony.models.service_agent.vo.auth.login_request import AgentLoginRequest
from irony.models.service_agent.vo.auth.login_response import AgentLoginResponse
from irony.models.service_agent.vo.auth.register_request import AgentRegisterRequest
from irony.models.service_agent.vo.auth.register_response import AgentRegisterResponse
from irony.services.agent import auth_service
from irony.util import auth

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AgentRegisterResponse)
async def register(user: AgentRegisterRequest):
    """
    Register a new service agent.

    Args:
        user (AgentRegisterRequest): Registration details for the new agent

    Returns:
        AgentRegisterResponse: Registration confirmation details
    """
    return await auth_service.register_service_agent(user)


@router.post("/login", response_model=AgentLoginResponse)
async def login(response: Response, request: AgentLoginRequest):
    """
    Authenticate a service agent.

    Args:
        response (Response): FastAPI response object for setting cookies
        request (AgentLoginRequest): Login credentials

    Returns:
        AgentLoginResponse: Authentication token and user details
    """
    return await auth_service.login_service_agent(response, request)


@router.get("/protected-route")
async def protected_route(current_user: str = Depends(auth.get_current_user)):
    """
    Test endpoint for authenticated users.

    Args:
        current_user (str): Authenticated user ID

    Returns:
        dict: Welcome message with user ID
    """
    return {"message": f"Welcome, {current_user}!"}
