from datetime import timedelta,datetime
import json
import uuid
from typing import Optional
from fastapi import Request, HTTPException
from sqlmodel import select
from app.utils.database import SessionDep
from app.apis.auth.utils import DateTimeEncoder, login_session_key, user_sessions_key
from app.apis.auth.models import SessionModel, SessionResponse
from app.apis.users.models import User
from app.utils.security import create_access_token, get_user_permissions_raw, verify_password
from app.utils.redis_db import get_string, set_hash, get_hash, set_string
from app.utils.logging_util import logger
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

    logger.info(f"User found for email: {email}, user_id: {user}")
    logger.info(f"Creating new user session for user_id: {user.id}")
    
    # Create session
    login_session = await create_session(request=request, account_id=str(user.id))
    if not login_session:
        logger.error(f"Failed to create session for user_id: {user.id}")
        raise HTTPException(status_code=500, detail="Session creation failed")

    # Update last_login
    login_session.last_login = datetime.utcnow()
    
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
            created_at=datetime.utcnow()
        )
        
        # Serialize SessionModel to JSON
        session_data = new_session.dict()
        print(session_data)
        session_json = json.dumps(session_data,cls=DateTimeEncoder)
        
        # Store in Redis with expiration (e.g., 7 days)
        session_key = user_sessions_key(account_id)

        logger.info(f"[Create New Session].account id : {account_id}. Session key :{session_key} . session field : {session_token}.  session value:  {session_json}")

        success =  set_hash(session_key, session_token, session_json, ex=604800)  # 7 days in seconds
        # Store the session token in Redis agains account_id
        
        logger.info(f"[Save User For Session] . account id : {account_id}. Session key :{session_key} .  session value:  {account_id}")

        res =  set_account_id_by_session_id(session_token, account_id)
        if success and res:
            logger.info(f"Session stored in Redis: {session_key}:{session_token}")

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
        account_session_key = user_sessions_key(account_id)
        session_json = await get_hash(account_session_key, session_id)
        
        if not session_json:
            logger.warning(f"Session not found for user. session key : {account_session_key}.session id:{session_id}")
            return None
            
        # Deserialize JSON to SessionResponse
        session_data = json.loads(session_json)
        session_response = SessionResponse(**session_data)
        
        logger.info(f"Session retrieved for account. Key : {account_session_key}. session id : {session_id}")
        return session_response
    except json.JSONDecodeError:
        logger.error(f"Invalid session data format in Redis: {account_session_key}:{session_id}")
        return None
    except ValidationError as e:
        logger.error(f"Session validation failed: {account_session_key}:{session_id}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving session: {account_session_key}:{session_id}: {str(e)}")
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
    stmt = select(User).where(User.email == email)
    result = session.execute(stmt)
    user = result.scalars().first()

    return user

def set_account_id_by_session_id(session_token: str,user_id:str) -> bool:
    """
    Cache the user ID by session token in Redis.
    Args:
        session_token: Session token.
        user_id: User ID.
    Returns: 
        bool: True if caching succeeded, else False.
    """
    key = login_session_key(session_token)
    try:
        # Store the user ID in Redis with the session token as the key
        success = set_string(key, user_id, expiration=604800)  # 7 days in seconds
        if success:
            logger.info(f"[Set Account ID] Success. session key : {key}. account id:{user_id}")
            return True
        else:
            logger.error(f"[Set Account ID] Failed. session key : {key}. account id:{user_id}")
            return False
    except Exception as e:
        logger.error(f"[Set Account ID] Error caching user ID: {session_token}:{user_id}: {str(e)}")
        return False


def get_account_id_by_session_token(session_token: str) -> Optional[str]:
    """
    Retrieve the user ID by session token from Redis.
    
    Args:
        session_token: Session token.
    
    Returns:
        str: User ID if found, else None.
    """
    key = login_session_key(session_token)
    try:
        user_id = get_string(key)
        if user_id:
            logger.info(f"[Get Account ID] Success .session key : {session_token}. account id:{user_id}")
            return user_id
        else:
            logger.warning(f"[Get Account ID] Failed .session key : {session_token}. account id:{user_id}")
            return None
    except Exception as e:
        logger.error(f"[Get Account ID] Error retrieving user ID: {session_token}: {str(e)}")
        return None