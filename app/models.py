
from sqlmodel import Field, SQLModel
from typing import List, Optional
from pydantic import EmailStr, BaseModel



# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str
    exp: int
    permissions: List[str] = []


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)


# Auth User model
class AuthUser(SQLModel):
    id: str
    permissions: List[str] = []
    is_active: bool = True
    is_verified: bool = False


class EmailSchema(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str