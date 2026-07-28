from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from datetime import timezone
from enum import Enum
from pydantic import BaseModel
class UserRole(str, Enum):
    customer = "customer"
    organizer = "organizer"
    staff = "staff"
    admin = "admin"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: str
    # Role is intentionally nullable: a freshly registered user has no role
    # until they go through the one-time role-selection step.
    role: Optional[UserRole] = Field(default=None)
    role_selected: bool = Field(default=False)
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)
    
class UserCreate(BaseModel):
    email : str 
    full_name : str
    password : str
    
class UserLogin(BaseModel):
    email : str
    password : str

class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    role: Optional[UserRole]
    role_selected: bool

class RoleSelect(BaseModel):
    role: UserRole