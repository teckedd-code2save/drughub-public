from typing import Optional, List
import uuid
from pydantic import EmailStr
from sqlmodel import Field, SQLModel

# ---------- Create / Update / Response Schemas ----------

# Update Request (Partial update)
class UserUpdateRequest(SQLModel):
    email: Optional[EmailStr] = Field(default=None, max_length=255)
    user_name: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=10)
    role_ids: Optional[List[uuid.UUID]] = Field(default=None)

# Password Update Request
class UpdatePasswordRequest(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)