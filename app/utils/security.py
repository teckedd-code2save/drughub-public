from datetime import datetime, timedelta, timezone
from typing import Annotated, List, Any, Optional
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError,InvalidSignatureError
from passlib.context import CryptContext
from app.utils.database import SessionDep 
from sqlmodel import select,Session
from collections.abc import Callable
from app.utils.config import settings
from app.models import AuthUser, TokenPayload  
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import  ValidationError
from sqlalchemy import text
from app.utils.logging_utitl import logger


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"

# login route
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/signin"
)

TokenDep = Annotated[str, Depends(reusable_oauth2)]

# password hashing
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a hashed password for storage."""
    return pwd_context.hash(password)

# JWT creation

def create_access_token(subject: str | Any, expires_delta: timedelta, permissions: List[str]) -> str:
    """
    Create a JWT with user ID and permissions baked in.
    
    Args:
        subject: User ID or identifier (e.g., UUID as string)
        expires_delta: Time until token expires
        permissions: List of permissions (e.g., ["view_order", "edit_product"])
    Returns:
        Encoded JWT string
    """
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "exp": expire,           # Expiration timestamp
        "sub": str(subject),     # Subject (user ID)
        "permissions": permissions  # Baked-in permissions
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

    

# Token decoding
def decode_token(token: str) -> dict:
    """
    Decode a JWT to inspect its payload (e.g., for permission checks).
    
    Args:
        token: Encoded JWT string
    Returns:
        Decoded payload dictionary
    Raises:
        jwt exceptions: If token is invalid or expired
    """
    logger.info(f"Decoding token: {token}")
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])



  # Baked-in permissions from security module

# Logged in user permissions and authorization
def get_user_permissions(user_id: str, session: SessionDep) -> List[str]:
    """
    Fetch all permissions for a user based on their role_ids.
    
    Args:
        user_id: User's UUID as string
        session: SQLModel database session
    Returns:
        List of unique permissions
    """
    # Fetch user
    user = session.get(User, user_id)
    if not user or not user.role_ids:
        return []
    # Fetch roles and combine permissions
    roles = session.exec(select(Role).where(Role.id.in_(user.role_ids))).all()
    permissions = list({perm for role in roles for perm in role.permissions})  # Deduplicate
    return permissions

def get_user_permissions_raw(user_id: str, session: SessionDep) -> List[str]:
    """
    Fetch all permissions for a user based on their role_ids using raw SQL.
    
    Args:
        user_id: User's UUID as string
        session: SQLAlchemy Session
    Returns:
        List of unique permissions
    """
    # Step 1: Get role_ids from user
    role_ids_query = text("""
        SELECT role_ids
        FROM public.user
        WHERE id = :user_id
    """)
    result = session.execute(role_ids_query, {"user_id": user_id}).first()
    
    logger.info(f"User role_ids: {result[0]}")

    if not result or not result[0]:
        return []

    # Step 2: Fetch permissions from roles matching those role_ids
    permissions_query = text("""
        SELECT DISTINCT jsonb_array_elements_text(permissions::jsonb) AS permission
        FROM public.role
        WHERE id = ANY(:role_ids)
    """)
    permissions_result = session.execute(permissions_query, {"role_ids": result[0]}).fetchall()
    logger.info(f"Permissions result: {permissions_result}")

    return [row[0] for row in permissions_result]


def get_current_user(
    session: SessionDep,
    token: TokenDep) -> AuthUser:
    """
    Validate JWT and return a generic AuthUser object.
    
    Args:
        session: Database session
        token: JWT string
        get_user_func: Callable to fetch user details (injected by dependent module)
    Returns:
        AuthUser with ID, permissions, and basic status
    Raises:
        HTTPException: On invalid token or user issues
    """
    try:
        payload = decode_token(token)
        token_data = TokenPayload(**payload)
    except ExpiredSignatureError as e:
        logger.warning(f"Token expired: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except ValidationError as e:
        logger.error(f"Token payload validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token payload",
        )
    except InvalidSignatureError as e:
        logger.error(f"JWT decoding failed.Invalid signature: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token signature",
        )
        
    table_name = "public.user"  # Replace with your actual table name

    # Fetch user details if a function is provided, otherwise use token data
    # Use raw SQL with string table name to fetch status fields
    query = text(f"SELECT is_verified FROM {table_name} WHERE id = :id")
    result = session.execute(query, {"id": token_data.sub}).mappings().fetchone()
    
    auth_user = AuthUser(
        id=token_data.sub,
        permissions=token_data.permissions,
        is_verified=result["is_verified"] if result else False
    )
    
    if not auth_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return auth_user

# Base dependency
CurrentUser = Annotated[AuthUser, Depends(get_current_user)]

# Permission check dependency
def require_permissions(required_permissions: List[str]):
    def check_permissions(current_user: CurrentUser) -> AuthUser:
        if not all(perm in current_user.permissions for perm in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return check_permissions

# Superuser check
def get_current_active_superuser(current_user: CurrentUser) -> AuthUser:
    if not current_user.is_verified:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
# Example usage in endpoint dependencies
RequireEditProduct = Annotated[AuthUser, Depends(require_permissions(["edit_products"]))]
RequireViewOrder = Annotated[AuthUser, Depends(require_permissions(["view_orders"]))]
RequireViewProfile = Annotated[AuthUser, Depends(require_permissions(["view_profile"]))]