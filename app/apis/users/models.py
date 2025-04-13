from datetime import datetime
import uuid
from typing import Optional, List
from pydantic import EmailStr
from sqlmodel import Field, SQLModel,Column, JSON


# ---------- Role Models ----------
"""
Stores users roles and permissions.
Roles are used to manage user access and permissions within the application.

eg. 
{
  "id": "uuid-1",
  "name": "Customer",
  "permissions": ["view_order", "create_order"]
}
"""

# Base Model (Shared Fields)
class RoleBase(SQLModel):
    name: str = Field(max_length=50)
    permissions: List[str] = Field(default_factory=list)  # No DB-specific config here

# Input Model (Request)
class RoleCreateRequest(RoleBase):
    pass  # Inherits name and permissions as-is

# Database Model
class Role(RoleBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # Override permissions to add DB-specific config
    permissions: List[str] = Field(default_factory=list, sa_column=Column(JSON))

# Output Model (Response)
class RoleResponse(RoleBase):
    id: uuid.UUID

# Collection Response
class RolesResponse(SQLModel):
    data: List[RoleResponse]
    count: int


# ---------- User Models ----------
class UserBase(SQLModel):
    email: EmailStr = Field(max_length=255)
    user_name: str = Field(max_length=255)
    phone: str = Field(max_length=10)
    role_ids: Optional[List[str]] = Field(default_factory=lambda: []) 


# Input Model (Request)
class UserCreateRequest(UserBase):
        
        password: str = Field(min_length=8, max_length=40)


#    Database Model
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str = Field(max_length=255)
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: Optional[datetime] = Field(default=None, nullable=True)
    last_login: Optional[datetime] = Field(default=None, nullable=True)
    role_ids: List[str] = Field(default_factory=lambda: [], sa_column=Column(JSON))  # Stores role UUIDs

# Output Model (Response)
class UserResponsePublic(SQLModel):
    id: uuid.UUID
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime]
    last_login: Optional[datetime]

class UserResponse(UserResponsePublic):
    permissions: List[str]  # Populated by app logic

# Collection Response
class UsersResponse(SQLModel):
    data: List[UserResponse]
    count: int

class UsersResponsePublic(SQLModel):
    data: List[UserResponsePublic]
    count: int


class UserSIgnInRequest(SQLModel):
        
        password: str 
        email: EmailStr 
