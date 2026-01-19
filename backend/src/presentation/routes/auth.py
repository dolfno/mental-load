from fastapi import APIRouter, HTTPException, Depends, status

from src.application import LoginUser
from src.infrastructure import get_database, SQLiteMemberRepository, AuthService
from src.domain import HouseholdMember
from ..schemas import LoginRequest, UserResponse, AuthResponse
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_member_repo():
    db = get_database()
    return SQLiteMemberRepository(db)


def get_auth_service():
    return AuthService()


@router.post("/login", response_model=AuthResponse)
def login(
    request: LoginRequest,
    member_repo: SQLiteMemberRepository = Depends(get_member_repo),
    auth_service: AuthService = Depends(get_auth_service),
):
    use_case = LoginUser(member_repo, auth_service)
    try:
        member, token = use_case.execute(
            email=request.email,
            password=request.password,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return AuthResponse(
        user=UserResponse(id=member.id, name=member.name, email=member.email),
        access_token=token,
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: HouseholdMember = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
    )
