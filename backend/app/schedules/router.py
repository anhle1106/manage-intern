from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.schedules import service
from app.schedules.schemas import ScheduleCreate, ScheduleUpdate
from app.common.dependencies import get_current_user
from app.common.enums import Role
from app.common.response import success_response

router = APIRouter(prefix="/api/schedules", tags=["Schedules"])


@router.get("")
async def list_schedules(
    user_id: Optional[str] = Query(None),
    user: dict = Depends(get_current_user),
):
    target_id = user_id if user_id and user["role"] != Role.INTERN else user["id"]
    schedules = await service.list_schedules(target_id)
    return success_response(data=schedules)


@router.post("")
async def create_schedule(
    body: ScheduleCreate,
    user: dict = Depends(get_current_user),
):
    entry = await service.create_schedule(user["id"], body.model_dump())
    return success_response(data=entry, message="Schedule created")


@router.put("/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    body: ScheduleUpdate,
    user: dict = Depends(get_current_user),
):
    entry = await service.update_schedule(schedule_id, user["id"], body.model_dump(exclude_unset=True))
    return success_response(data=entry, message="Schedule updated")


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    user: dict = Depends(get_current_user),
):
    await service.delete_schedule(schedule_id, user["id"])
    return success_response(message="Schedule deleted")


@router.get("/availability")
async def check_availability(
    user_id: str = Query(...),
    day_of_week: int = Query(...),
    start_time: str = Query(...),
    end_time: str = Query(...),
    _: dict = Depends(get_current_user),
):
    available = await service.check_availability(user_id, day_of_week, start_time, end_time)
    return success_response(data={"available": available})
