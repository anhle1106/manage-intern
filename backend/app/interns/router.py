from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.interns import service
from app.interns.schemas import InternProfileUpdate
from app.common.dependencies import get_current_user, require_roles
from app.common.enums import Role
from app.common.response import success_response

router = APIRouter(prefix="/api/interns", tags=["Interns"])


@router.get("")
async def list_interns(
    onboarding_id: Optional[str] = Query(None),
    user: dict = Depends(get_current_user),
):
    if user["role"] == Role.LEADER:
        from app.database import get_db
        db = get_db()
        batches = db.onboardings.find({"leader_ids": user["id"]})
        all_interns = []
        async for batch in batches:
            interns = await service.list_interns(str(batch["_id"]))
            all_interns.extend(interns)
        seen = set()
        unique = []
        for i in all_interns:
            if i["user_id"] not in seen:
                seen.add(i["user_id"])
                unique.append(i)
        return success_response(data=unique)

    interns = await service.list_interns(onboarding_id)
    return success_response(data=interns)


@router.get("/{user_id}")
async def get_intern(user_id: str, _: dict = Depends(get_current_user)):
    intern = await service.get_intern(user_id)
    return success_response(data=intern)


@router.put("/{user_id}")
async def update_intern(
    user_id: str,
    body: InternProfileUpdate,
    user: dict = Depends(get_current_user),
):
    if user["role"] == Role.INTERN and user["id"] != user_id:
        from app.common.exceptions import ForbiddenError
        raise ForbiddenError("Can only update your own profile")
    intern = await service.update_intern(user_id, body.model_dump(exclude_unset=True))
    return success_response(data=intern, message="Profile updated")
