from pydantic import BaseModel
from typing import Optional
from app.common.enums import OnboardingStatus


class OnboardingCreate(BaseModel):
    name: str
    description: str = ""
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    status: OnboardingStatus = OnboardingStatus.DRAFT


class OnboardingUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[OnboardingStatus] = None


class MemberAction(BaseModel):
    user_id: str
