from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.domain import HouseholdMember
from src.infrastructure import get_database, SQLiteMemberRepository, AuthService

security = HTTPBearer()


def get_auth_service() -> AuthService:
    return AuthService()


def get_member_repo() -> SQLiteMemberRepository:
    db = get_database()
    return SQLiteMemberRepository(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
    member_repo: SQLiteMemberRepository = Depends(get_member_repo),
) -> HouseholdMember:
    token = credentials.credentials
    user_id = auth_service.decode_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = member_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
