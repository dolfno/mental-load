import logging
import os

from src.domain import HouseholdMember
from .database import get_database
from .repositories import SQLiteMemberRepository
from .auth import AuthService

logger = logging.getLogger(__name__)


def create_default_admin_if_needed() -> bool:
    """
    Create a default admin user if no registered users exist.

    Reads configuration from environment variables:
    - ADMIN_EMAIL: Email for the admin user (required)
    - ADMIN_PASSWORD: Password for the admin user (required)
    - ADMIN_NAME: Display name (optional, defaults to "Admin")

    Returns True if admin was created, False otherwise.
    """
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_name = os.getenv("ADMIN_NAME", "Admin")

    # Check if env vars are set
    if not admin_email or not admin_password:
        logger.info("ADMIN_EMAIL and/or ADMIN_PASSWORD not set. Skipping auto-admin creation.")
        return False

    db = get_database()
    member_repo = SQLiteMemberRepository(db)

    # Check if any users with email/password exist (registered users)
    all_members = member_repo.get_all()
    registered_users = [m for m in all_members if m.email is not None]

    if registered_users:
        logger.info("Registered users already exist. Skipping auto-admin creation.")
        return False

    # Check if user with this email already exists
    existing = member_repo.get_by_email(admin_email)
    if existing:
        logger.info(f"User with email {admin_email} already exists. Skipping auto-admin creation.")
        return False

    # Create the admin user
    auth_service = AuthService()
    password_hash = auth_service.hash_password(admin_password)

    admin = HouseholdMember(
        id=None,
        name=admin_name,
        email=admin_email,
        password_hash=password_hash,
    )

    member_repo.save(admin)
    logger.info(f"Created default admin user: {admin_email}")
    return True
