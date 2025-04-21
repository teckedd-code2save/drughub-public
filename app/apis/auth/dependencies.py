from typing import Annotated
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.utils.database import SessionDep
from app.apis.auth.services import get_session, get_account_id_by_session_token
from app.apis.users.models import User
from app.utils.logging_util import logger

security = HTTPBearer()

async def verify_token(
    token: str,
    session: SessionDep
) -> User:
    """
    Verify a session token and return the associated user.

    Args:
        token: Session token from Authorization header.
        session: Database session.

    Returns:
        User: Authenticated user.

    Raises:
        HTTPException: If the token is invalid or user not found.
    """
    # Get account_id from token
    account_id = await get_account_id_by_session_token(token)
    if not account_id:
        logger.warning(f"Invalid session token: {token}")
        raise HTTPException(status_code=401, detail="Invalid token")

    # Fetch session from Redis
    session_data = await get_session(account_id=account_id, session_id=token)
    if not session_data:
        logger.warning(f"Session not found for token: {token}")
        raise HTTPException(status_code=401, detail="Invalid token")

    # Fetch user from database
    user = await session.get(User, session_data.account_id)
    if not user:
        logger.warning(f"User not found for account_id: {session_data.account_id}")
        raise HTTPException(status_code=401, detail="User not found")

    logger.debug(f"User authenticated: {user.id}")
    return user



# Wrapper for routes requiring authentication
async def session_wrapper(
        session: SessionDep ,
    auth: HTTPAuthorizationCredentials = Security(security),
    
) -> User:
    """
    Authenticate a user from a Bearer token and return the User object.

    Args:
        auth: HTTP Authorization credentials (Bearer token).
        session: Database session.

    Returns:
        User: Authenticated user.
    """
    return await verify_token(auth.credentials, session)

# Dependency for protected routes
SessionUser = Annotated[User, Depends(session_wrapper)]