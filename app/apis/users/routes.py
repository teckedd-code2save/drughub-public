import uuid
from typing import Annotated, Any

from app.utils.email import generate_new_account_email,send_email
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import col, delete

from app.apis.users  import services as crud
from app.apis.users.models import (
    User,
    UserCreateRequest,
    UserResponse,
    UserResponsePublic,
    UserSIgnInRequest,
    UsersResponse
)
from app.apis.users.schemas import (
    UserUpdateRequest,
    UpdatePasswordRequest)

from app.utils.security import (
    CurrentUser,
    get_current_active_superuser,
)
from app.utils.database import SessionDep

from app.utils.config import settings
from app.utils.security import get_password_hash, verify_password
from app.models import (
    Message,
    Token,
    TokenPayload,
   
)

router = APIRouter(prefix="/users", tags=["users"])

userService = Annotated[SessionDep, Depends(SessionDep)]

@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersResponse,
)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """

    users = crud.get_paginated_users(session=session, skip=skip, limit=limit)
    count = users.count()
    if not count:
        raise HTTPException(status_code=404, detail="No users found")
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    if len(users) == 0:
        raise HTTPException(status_code=404, detail="No users found")

    return UsersResponse(data=users, count=count)


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserResponse
)
def create_user(*, session: SessionDep, user_in: UserCreateRequest) -> Any:
    """
    Create new user.
    """
    user = crud.get_user_by_email(email=user_in.email,session=session)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    user = crud.register_user(user_create=user_in,session=session)
    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


@router.patch("/me", response_model=UserResponse)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdateRequest, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """

    if user_in.email:
        existing_user = crud.get_user_by_email(email=user_in.email,session=session)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.patch("/me/password", response_model=Message)
def update_password_me(
    *, session: SessionDep, body: UpdatePasswordRequest, current_user: CurrentUser
) -> Any:
    """
    Update own password.
    """
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    session.commit()
    return Message(message="Password updated successfully")


@router.get("/me", response_model=CurrentUser)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@router.delete("/me", response_model=Message)
def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own user.
    """
    if current_user.is_verified:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    session.delete(current_user)
    session.commit()
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserResponsePublic)
def register_user(session: SessionDep, user_in: UserCreateRequest) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user = crud.get_user_by_email(email=user_in.email,session=session)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user_create = UserCreateRequest.model_validate(user_in)
    user = crud.register_user(session=session, user_create=user_create)
    return user

@router.post("/signin", response_model=Token)
def signin_user(session: SessionDep, user_in: UserSIgnInRequest) -> Any:
    """
   login user and return JWT token
    """
    token = crud.login_user(
        email=user_in.email,
        password=user_in.password,
        session=session
    )
    if not token:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return Token(
        access_token=token)


@router.get("/{user_id}", response_model=UserResponse)
def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    res = UserResponse(**user.dict(), permissions=current_user.permissions)
    return res



@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserResponse,
)
def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_update: UserUpdateRequest,
) -> Any:
    """
    Update a user.
    """

    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = crud.get_user_by_email(email=user_in.email,session=session)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )

    db_user = crud.update_user(user_id=user_id, user_update=user_update, session=session)
    return db_user


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    """
    Delete a user.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    statement = delete(User).where(col(User.id) == user_id)
    session.exec(statement)  # type: ignore
    session.delete(user)
    session.commit()
    return Message(message="User deleted successfully")
