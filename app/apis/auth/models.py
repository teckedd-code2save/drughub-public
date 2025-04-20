from typing import Optional
import uuid
from sqlmodel import Field, SQLModel,Column, JSON
from datetime import datetime

class SessionModel(SQLModel):
    session_token : str = Field(max_length=50, nullable=False)
    ip : str = Field(max_length=50, nullable=False)
    account_id :str = Field(max_length=50, nullable=False)
    created_at : datetime = Field(default_factory=datetime.utcnow, nullable=False)
    last_login : Optional[datetime] = Field(default=None, nullable=True)
    

class SessionResponse(SQLModel):
    session_token : str 
    account_id :str
    created_at : datetime
    last_login : Optional[datetime] 
    
    