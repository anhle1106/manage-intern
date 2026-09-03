from pydantic import BaseModel
from typing import Optional


class InternProfileUpdate(BaseModel):
    university: Optional[str] = None
    major: Optional[str] = None
    student_id: Optional[str] = None
    phone: Optional[str] = None
    start_date: Optional[str] = None


class InternProfileResponse(BaseModel):
    id: str
    user_id: str
    full_name: str
    email: str
    university: str
    major: str
    student_id: str
    phone: str
    start_date: Optional[str] = None
    is_active: bool = True
