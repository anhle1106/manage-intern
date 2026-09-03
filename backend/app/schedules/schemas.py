from pydantic import BaseModel, model_validator
from typing import Optional, List


class ScheduleCreate(BaseModel):
    subject: str
    is_recurring: bool = False  # False = Specific date range; True = Weekly recurring on selected days
    days_of_week: List[int] = []  # e.g., [0, 1, 2, 3, 4] for Mon-Fri
    day_of_week: Optional[int] = 0
    start_time: str  # HH:MM
    end_time: str  # HH:MM
    location: str = ""
    note: str = ""
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD

    @model_validator(mode="after")
    def validate_times(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        if self.start_date > self.end_date:
            raise ValueError("start_date must be before end_date")
        return self


class ScheduleUpdate(BaseModel):
    subject: Optional[str] = None
    is_recurring: Optional[bool] = None
    days_of_week: Optional[List[int]] = None
    day_of_week: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    note: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ScheduleResponse(BaseModel):
    id: str
    user_id: str
    subject: str
    is_recurring: bool = False
    days_of_week: List[int] = []
    day_of_week: int
    start_time: str
    end_time: str
    location: str
    note: str
    start_date: str
    end_date: str
