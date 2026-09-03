from pydantic import BaseModel, EmailStr
from typing import Optional
from app.common.enums import Role


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Role = Role.INTERN


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[Role] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
