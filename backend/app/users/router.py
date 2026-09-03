from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.users import service
from app.users.schemas import UserCreate, UserUpdate
from app.common.dependencies import require_roles, get_current_user
from app.common.enums import Role
from app.common.response import success_response

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("")
async def list_users(
    role: Optional[str] = Query(None),
    _: dict = Depends(require_roles(Role.ADMIN, Role.LEADER)),
):
    users = await service.list_users(role)
    return success_response(data=users)


@router.post("")
async def create_user(
    body: UserCreate,
    _: dict = Depends(require_roles(Role.ADMIN)),
):
    user = await service.create_user(body.model_dump())
    return success_response(data=user, message="User created")


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    _: dict = Depends(get_current_user),
):
    user = await service.get_user(user_id)
    return success_response(data=user)


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    body: UserUpdate,
    _: dict = Depends(require_roles(Role.ADMIN)),
):
    user = await service.update_user(user_id, body.model_dump(exclude_unset=True))
    return success_response(data=user, message="User updated")


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    _: dict = Depends(require_roles(Role.ADMIN)),
):
    await service.delete_user(user_id)
    return success_response(message="User deleted")
