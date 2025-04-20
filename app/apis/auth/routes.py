from datetime import timedelta
from typing import Annotated, Any

from app.apis.users.models import UserSIgnInRequest
from fastapi import APIRouter, Depends, HTTPException,BackgroundTasks,Request
from fastapi.responses import HTMLResponse

from app.apis.auth  import services as crud
from app.utils.database import  SessionDep

from app.models import  EmailSchema, Message, Token, VerifyOTPRequest


from app.utils.otp_email import send_otp_mail,verify_otp

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

@router.post("/send-otp/")
async def send_otp_email(email: EmailSchema, background_tasks: BackgroundTasks) -> Any:
    """
    Send OTP to email
    """
    background_tasks.add_task(send_otp_mail, email)
    return {"message": "Email has been sent in the background"}


@router.post("/signin/otp")
async def verify_otp_email(data: VerifyOTPRequest,session: SessionDep,request:Request) -> Message:
    """
    Verify OTP
    """
    res = verify_otp(data=data)
    if res.code == 200:

        login_session = await crud.authenticate_user_session(
        request=request,
        email=data.email,
        session=session
        )
        
        if not login_session:
            return Message(code=200,message="User Not Found")
        
        return Message(message="Successfully logged in with otp",data=login_session)
    
    return Message(code=400,message="Expired or Invalid Otp")

