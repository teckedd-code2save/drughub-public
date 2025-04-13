"""
users services
"""
from datetime import timedelta
from http.client import HTTPException
from typing import Annotated, Optional, List
import uuid
from app.utils.database  import SessionDep
from app.apis.users.utils import get_user_by_mail
from fastapi import Depends
from sqlmodel import  select
from app.apis.users.models import User, Role,UserCreateRequest,UserResponse,UserResponsePublic
from app.apis.users.schemas import   UserUpdateRequest
from app.utils.database import get_db
from app.utils.security import create_access_token, get_password_hash, get_user_permissions, get_user_permissions_raw, verify_password
from app.utils.logging import logger
# ---------- User Services ----------


def register_user(
    user_create: UserCreateRequest,
    session: SessionDep,
) -> UserResponsePublic:
    """
    Create a new user
    """

    existing_user = get_user_by_email(user_create.email, session)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
    email=user_create.email,
    user_name=user_create.user_name,
    phone=user_create.phone,
    role_ids=user_create.role_ids,
    hashed_password=get_password_hash(user_create.password),
)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def login_user(email: str, password: str, session: SessionDep, expires_delta: timedelta = timedelta(minutes=15)) -> str:
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


def get_user_by_id(
    user_id: uuid.UUID,
    session: SessionDep,
) -> Optional[UserResponse]:
    """
    Get a user by id
    """
    
    user = session.get(User, user_id)
    if not user:
        return None
    return user


def get_user_by_email(
    email: str,
    session: SessionDep,
) -> Optional[UserResponse]:
    """
    Get a user by email
    """
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    if not user:
        return None
    return user


def get_user_by_phone(
    phone: str,
    session: SessionDep,
) -> Optional[UserResponse]:
    """
    Get a user by phone
    """
    
    statement = select(User).where(User.phone == phone)
    user = session.exec(statement).first()
    if not user:
        return None
    return user

def get_paginated_users(
    session: SessionDep,
     skip: int = 0,
    limit: int = 100,
) -> List[UserResponse]:
    """
    Get a paginated list of users
    """
    
    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()
    return users


def update_user(user_id: uuid.UUID, user_update: UserUpdateRequest, session: SessionDep) -> UserResponse:
    """
    Update a user
    """
    
    user = session.get(User, user_id)
    if not user:
        return None
    user_data = user_update.dict(exclude_unset=True)
    for key, value in user_data.items():
        setattr(user, key, value)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def delete_user(user_id: uuid.UUID, session: SessionDep) -> bool:
    """
    Delete a user
    """
    user = session.get(User, user_id)
    if not user:
        return False
    session.delete(user)
    session.commit()
    return True

def get_user_role(user: User, session: SessionDep) -> Optional[Role]:
    """
    Get a user's role
    """
    if not user.role_id:
        return None
    role = session.get(Role, user.role_id)
    if not role:
        return None
    return role

def assign_role_to_user(
    user_id: uuid.UUID,
    role_id: uuid.UUID,
    session: SessionDep,
) -> UserResponse:
    """
    Assign a role to a user
    """
    
    user = session.get(User, user_id)
    if not user:
        return None
    role = session.get(Role, role_id)
    if not role:
        return None
    user.role = role
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

