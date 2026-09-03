from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.leave_requests import service
from app.leave_requests.schemas import LeaveRequestCreate
from app.common.dependencies import get_current_user, require_roles
from app.common.enums import Role
from app.common.response import success_response

router = APIRouter(prefix="/api/leave-requests", tags=["Leave Requests"])


@router.get("")
async def list_leave_requests(
    status: Optional[str] = Query(None),
    user: dict = Depends(get_current_user),
):
    if user["role"] == Role.INTERN:
        requests = await service.list_leave_requests(user_id=user["id"], status_filter=status)
    elif user["role"] == Role.LEADER:
        from app.database import get_db
        db = get_db()
        batches = db.onboardings.find({"leader_ids": user["id"]})
        intern_ids = set()
        async for batch in batches:
            intern_ids.update(batch.get("intern_ids", []))
        requests = await service.list_leave_requests(intern_ids=list(intern_ids), status_filter=status)
    else:
        requests = await service.list_leave_requests(status_filter=status)
    return success_response(data=requests)


@router.post("")
async def create_leave_request(
    body: LeaveRequestCreate,
    user: dict = Depends(require_roles(Role.INTERN)),
):
    request = await service.create_leave_request(user["id"], body.model_dump())
    return success_response(data=request, message="Leave request created")


@router.put("/{request_id}/approve")
async def approve_leave(
    request_id: str,
    user: dict = Depends(require_roles(Role.ADMIN, Role.LEADER)),
):
    request = await service.approve_leave(request_id, user["id"])
    return success_response(data=request, message="Leave request approved")


@router.put("/{request_id}/reject")
async def reject_leave(
    request_id: str,
    user: dict = Depends(require_roles(Role.ADMIN, Role.LEADER)),
):
    request = await service.reject_leave(request_id, user["id"])
    return success_response(data=request, message="Leave request rejected")


@router.put("/{request_id}/cancel")
async def cancel_leave(
    request_id: str,
    user: dict = Depends(require_roles(Role.INTERN)),
):
    request = await service.cancel_leave(request_id, user["id"])
    return success_response(data=request, message="Leave request cancelled")
