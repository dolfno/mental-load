import os

from fastapi import APIRouter, HTTPException, Header, Depends, status

from src.application import RegisterUser
from src.infrastructure import get_database, SQLiteMemberRepository, AuthService
from ..schemas import CreateUserRequest, UserResponse

router = APIRouter(prefix="/api/admin", tags=["admin"])


def get_member_repo():
    db = get_database()
    return SQLiteMemberRepository(db)


def get_auth_service():
    return AuthService()


def verify_admin_api_key(x_admin_api_key: str = Header(..., alias="X-Admin-Api-Key")):
    """Verify the admin API key from the request header."""
    expected_key = os.getenv("ADMIN_API_KEY")
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin API key not configured",
        )
    if x_admin_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin API key",
        )
    return True


@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(
    request: CreateUserRequest,
    _: bool = Depends(verify_admin_api_key),
    member_repo: SQLiteMemberRepository = Depends(get_member_repo),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Create a new user account (admin only)."""
    use_case = RegisterUser(member_repo, auth_service)
    try:
        member, _ = use_case.execute(
            name=request.name,
            email=request.email,
            password=request.password,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return UserResponse(id=member.id, name=member.name, email=member.email)
