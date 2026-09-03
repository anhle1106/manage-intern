from pydantic import BaseModel, model_validator
from typing import Optional
from app.common.enums import LeaveType


class LeaveRequestCreate(BaseModel):
    leave_type: LeaveType
    start_datetime: str  # ISO format: 2026-09-05T08:00:00
    end_datetime: str  # ISO format: 2026-09-05T12:00:00
    reason: str
    attachment_url: Optional[str] = None
    create_schedule: Optional[bool] = False
    schedule_subject: Optional[str] = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_datetime >= self.end_datetime:
            raise ValueError("start_datetime must be before end_datetime")
        if not self.reason.strip():
            raise ValueError("Reason is required")
        return self


class LeaveRequestResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    leave_type: str
    start_datetime: str
    end_datetime: str
    reason: str
    attachment_url: Optional[str] = None
    status: str
    created_schedule_id: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    created_at: str
