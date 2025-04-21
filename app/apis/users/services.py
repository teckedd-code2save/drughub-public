"""
users services
"""
from http.client import HTTPException
from typing import Optional, List
import uuid
from app.utils.database  import SessionDep
from sqlmodel import  select
from app.apis.users.models import User, Role,UserCreateRequest,UserResponse,UserResponsePublic
from app.apis.users.schemas import   UserUpdateRequest
from app.utils.security import  get_password_hash
from app.utils.logging_util import logger
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

async def get_paginated_users(
    session: SessionDep,  # Using SessionDep
    skip: int = 0,
    limit: int = 100,
) -> List[UserResponse]:
    """
    Get a paginated list of users
    """
    statement = select(User).offset(skip).limit(limit)
    result = await session.execute(statement)  # Use execute with await
    users = result.scalars().all()  # Extract results
    logger.info(f"Users: {users}")
    if not users or len(users) == 0:
        raise HTTPException(status_code=404, detail="No users found")
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


