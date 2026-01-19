from src.domain import HouseholdMember
from src.application.interfaces import MemberRepository
from src.infrastructure.auth import AuthService


class RegisterUser:
    """Register a new user or claim existing member by name."""

    def __init__(self, member_repo: MemberRepository, auth_service: AuthService):
        self.member_repo = member_repo
        self.auth_service = auth_service

    def execute(self, name: str, email: str, password: str) -> tuple[HouseholdMember, str]:
        # Check if email already exists
        if self.member_repo.get_by_email(email):
            raise ValueError("Email already registered")

        # Check if name exists (can be claimed if not already registered)
        existing = self.member_repo.get_by_name(name)
        if existing and existing.email:
            raise ValueError("Name already taken")

        password_hash = self.auth_service.hash_password(password)

        if existing:
            # Claim existing member
            existing.email = email
            existing.password_hash = password_hash
            member = self.member_repo.save(existing)
        else:
            # Create new member
            member = HouseholdMember(
                id=None, name=name, email=email, password_hash=password_hash
            )
            member = self.member_repo.save(member)

        token = self.auth_service.create_access_token(member.id)
        return member, token


class LoginUser:
    """Authenticate user and return JWT."""

    def __init__(self, member_repo: MemberRepository, auth_service: AuthService):
        self.member_repo = member_repo
        self.auth_service = auth_service

    def execute(self, email: str, password: str) -> tuple[HouseholdMember, str]:
        member = self.member_repo.get_by_email(email)
        if not member or not member.password_hash:
            raise ValueError("Invalid credentials")

        if not self.auth_service.verify_password(password, member.password_hash):
            raise ValueError("Invalid credentials")

        token = self.auth_service.create_access_token(member.id)
        return member, token


class GetCurrentUser:
    """Get user by ID (for token validation)."""

    def __init__(self, member_repo: MemberRepository):
        self.member_repo = member_repo

    def execute(self, user_id: int) -> HouseholdMember | None:
        return self.member_repo.get_by_id(user_id)
