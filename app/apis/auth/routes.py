from datetime import timedelta
from typing import Annotated, Any

from app.apis.users.models import UserSIgnInRequest
from fastapi import APIRouter, Depends, HTTPException,BackgroundTasks
from fastapi.responses import HTMLResponse

from app.apis.auth  import services as crud
from app.utils.security import CurrentUser, get_current_active_superuser,get_password_hash
from app.utils.database import  SessionDep

from app.models import AuthUser, EmailSchema, Message, NewPassword, Token, VerifyOTPRequest
from app.utils.email_util import (
    generate_password_reset_token,
    generate_reset_password_email,
    send_email,
    verify_password_reset_token,
)

from app.utils.otp_email import send_otp, send_otp_mail,verify_otp

router = APIRouter(prefix="/auth" ,tags=["signin"])


@router.post("/signin", response_model=Token)
def signin_user(session: SessionDep, auth_req: UserSIgnInRequest) -> Any:
    """
   signin user and return JWT token
    """
    token = crud.authenticate_user(
        email=auth_req.email,
        password=auth_req.password,
        session=session
    )
    if not token:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return Token(
        access_token=token)



@router.post("/signin/test-token", response_model=AuthUser)
def test_token(current_user: CurrentUser) -> Any:
    """
    Test access token
    """
    return current_user


@router.post("/password-recovery/{email}")
def recover_password(email: str, session: SessionDep) -> Message:
    """
    Password Recovery
    """
    user = crud.get_user_by_mail(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )
    send_email(
        email_to=user.email,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Password recovery email sent")


@router.post("/reset-password/")
def reset_password(session: SessionDep, body: NewPassword) -> Message:
    """
    Reset password
    """
    email = verify_password_reset_token(token=body.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = crud.get_user_by_mail(session=session, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system.",
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    hashed_password = get_password_hash(password=body.new_password)
    user.hashed_password = hashed_password
    session.add(user)
    session.commit()
    return Message(message="Password updated successfully")


@router.post(
    "/password-recovery-html-content/{email}",
    dependencies=[Depends(get_current_active_superuser)],
    response_class=HTMLResponse,
)
def recover_password_html_content(email: str, session: SessionDep) -> Any:
    """
    HTML Content for Password Recovery
    """
    user = crud.get_user_by_mail(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )

    return HTMLResponse(
        content=email_data.html_content, headers={"subject:": email_data.subject}
    )

@router.post("/send-otp/")
async def send_otp_email(email: EmailSchema, background_tasks: BackgroundTasks) -> Any:
    """
    Send OTP to email
    """
    background_tasks.add_task(send_otp_mail, email)
    return {"message": "Email has been sent in the background"}


@router.post("/verify-otp/")
def verify_otp_email(data: VerifyOTPRequest) -> Message:
    """
    Verify OTP
    """
    return verify_otp(data=data)


