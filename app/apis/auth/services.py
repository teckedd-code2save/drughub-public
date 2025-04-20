from datetime import timedelta,datetime
import json
import uuid
from typing import Optional
from fastapi import Request, HTTPException
from sqlmodel import select
from app.utils.database import SessionDep
from app.apis.auth.utils import get_session_key
from app.apis.auth.models import SessionModel, SessionResponse
from app.apis.users.models import User
from app.utils.security import create_access_token, get_user_permissions_raw
from app.utils.redis_db import set_hash, get_hash
from app.utils.logging_utitl import logger
from pydantic import ValidationError

# ---------- User Services ----------

async def authenticate_user_session(
    request: Request,
    email: str,
    session: SessionDep
) -> Optional[SessionResponse]:
    """
    Authenticate a user and return a session response.

    Args:
        request: FastAPI request object.
        email: User email.
        session: Database session.

    Returns:
        SessionResponse: Session details if authentication succeeds, else None.

    Raises:
        HTTPException: If user not found or session creation fails.
    """
    # Fetch user by email
    user = get_user_by_email(session, email)
    if not user:
        logger.warning(f"No user exists for email: {email}")
        return None

    logger.info(f"Creating new user session for user_id: {user.id}")
    
    # Create session
    login_session = await create_session(request=request, account_id=str(user.id))
    if not login_session:
        logger.error(f"Failed to create session for user_id: {user.id}")
        raise HTTPException(status_code=500, detail="Session creation failed")

    # Update last_login
    login_session.last_login = datetime.datetime.utcnow()
    
    # Convert to SessionResponse
    session_response = SessionResponse(
        session_token=login_session.session_token,
        account_id=login_session.account_id,
        created_at=login_session.created_at,
        last_login=login_session.last_login
    )
    
    logger.info(f"Session created for user_id: {user.id}, session_token: {login_session.session_token}")
    return session_response

async def create_session(
    request: Request,
    account_id: str,
) -> Optional[SessionModel]:
    """
    Create a new session in Redis.

    Args:
        request: FastAPI request object.
        account_id: User account ID.

    Returns:
        SessionModel: Created session object or None if creation fails.
    """
    try:
        session_token = str(uuid.uuid4())
        # Create a new session object
        new_session = SessionModel(
            session_token=session_token,
            ip=request.client.host,
            account_id=account_id,
            created_at=datetime.datetime.utcnow()
        )
        
        # Serialize SessionModel to JSON
        session_data = new_session.dict()
        session_json = json.dumps(session_data)
        
        # Store in Redis with expiration (e.g., 7 days)
        session_key = get_session_key(account_id)
        success = await set_hash(session_key, session_token, session_json, ex=604800)  # 7 days in seconds
        if success:
            logger.debug(f"Session stored in Redis: {session_key}:{session_token}")
            return new_session
        else:
            logger.error(f"Failed to store session in Redis: {session_key}:{session_token}")
            return None
    except Exception as e:
        logger.error(f"Error creating session for account_id: {account_id}: {str(e)}")
        return None

async def get_session(account_id: str, session_id: str) -> Optional[SessionResponse]:
    """
    Retrieve a session from Redis by account ID and session ID.

    Args:
        account_id: User account ID.
        session_id: Session token.

    Returns:
        SessionResponse: Session details if found, else None.
    """
    try:
        session_key = get_session_key(account_id)
        session_json = await get_hash(session_key, session_id)
        
        if not session_json:
            logger.warning(f"Session not found: {session_key}:{session_id}")
            return None
            
        # Deserialize JSON to SessionResponse
        session_data = json.loads(session_json)
        session_response = SessionResponse(**session_data)
        
        logger.debug(f"Session retrieved: {session_key}:{session_id}")
        return session_response
    except json.JSONDecodeError:
        logger.error(f"Invalid session data format in Redis: {session_key}:{session_id}")
        return None
    except ValidationError as e:
        logger.error(f"Session validation failed: {session_key}:{session_id}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving session: {session_key}:{session_id}: {str(e)}")
        return None



# ---------- TOKEN AUTH ----------------------#


def authenticate_user_credentials(email: str, password: str, session: SessionDep, expires_delta: timedelta = timedelta(minutes=15)) -> str:
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
    user = get_user_by_email(session,email)
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

def authenticate_user_email(email: str, session: SessionDep, expires_delta: timedelta = timedelta(minutes=15)) -> str:
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
    user = get_user_by_email(session,email)
    if not user:
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


def get_user_by_email(session: SessionDep, email: str) -> Optional[User]:
    """
    Retrieve a user by email from the database.

    Args:
        session: Database session.
        email: User email.

    Returns:
        User: User object if found, else None.
    """
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    return user
