"""
users services
"""
from datetime import timedelta
from typing import Optional
from app.utils.database  import SessionDep
from sqlmodel import  select
from app.apis.users.models import User
from app.utils.security import create_access_token,  get_user_permissions_raw, verify_password
from app.utils.logging_utitl import logger
# ---------- User Services ----------


def authenticate_user(email: str, password: str, session: SessionDep, expires_delta: timedelta = timedelta(minutes=15)) -> str:
    """
    Authenticate a user and return a JWT with permissions.
    
    Args:
        email: User email
        password: Plain password
        session: Database session
        expires_delta: Token expiration time (default 15 minutes)
    Returns:
        JWT token string
    Raises:
        ValueError: If credentials are invalid
    """
    # Fetch user by email.Return not found if user not found
    user = get_user_by_mail(session,email)
    if not user or not verify_password(password, user.hashed_password):
        # Invalid credentials
        # Log the failed login attempt
        logger.info(f"Failed login attempt for email: {email}")
        return None
    

    # Get user's permissions
    permissions = get_user_permissions_raw(str(user.id), session)
    logger.info(f"User permissions: {permissions}")
    
    # Create token with permissions baked in
    token = create_access_token(
        subject=str(user.id),
        expires_delta=expires_delta,
        permissions=permissions
    )
    return token



def get_user_by_mail(session: SessionDep, email: str) -> User:
    """Fetch a User by email from the database."""
    return session.exec(select(User).where(User.email == email)).first()




