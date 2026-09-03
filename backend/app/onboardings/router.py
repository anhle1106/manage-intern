from fastapi import APIRouter, Depends
from app.onboardings import service
from app.onboardings.schemas import OnboardingCreate, OnboardingUpdate, MemberAction
from app.common.dependencies import get_current_user, require_roles
from app.common.enums import Role
from app.common.response import success_response

router = APIRouter(prefix="/api/onboardings", tags=["Onboardings"])


@router.get("")
async def list_onboardings(user: dict = Depends(get_current_user)):
    batches = await service.list_onboardings(user["id"], user["role"])
    return success_response(data=batches)


@router.get("/{onboarding_id}")
async def get_onboarding(onboarding_id: str, _: dict = Depends(get_current_user)):
    batch = await service.get_onboarding(onboarding_id)
    return success_response(data=batch)


@router.post("")
async def create_onboarding(
    body: OnboardingCreate,
    _: dict = Depends(require_roles(Role.ADMIN)),
):
    batch = await service.create_onboarding(body.model_dump())
    return success_response(data=batch, message="Onboarding batch created")


@router.put("/{onboarding_id}")
async def update_onboarding(
    onboarding_id: str,
    body: OnboardingUpdate,
    _: dict = Depends(require_roles(Role.ADMIN)),
):
    batch = await service.update_onboarding(onboarding_id, body.model_dump(exclude_unset=True))
    return success_response(data=batch, message="Onboarding batch updated")


@router.post("/{onboarding_id}/leaders")
async def add_leader(
    onboarding_id: str,
    body: MemberAction,
    _: dict = Depends(require_roles(Role.ADMIN, Role.LEADER)),
):
    batch = await service.add_leader(onboarding_id, body.user_id)
    return success_response(data=batch, message="Leader added")


@router.delete("/{onboarding_id}/leaders/{user_id}")
async def remove_leader(
    onboarding_id: str,
    user_id: str,
    _: dict = Depends(require_roles(Role.ADMIN, Role.LEADER)),
):
    batch = await service.remove_leader(onboarding_id, user_id)
    return success_response(data=batch, message="Leader removed")


@router.post("/{onboarding_id}/interns")
async def add_intern(
    onboarding_id: str,
    body: MemberAction,
    _: dict = Depends(require_roles(Role.ADMIN, Role.LEADER)),
):
    batch = await service.add_intern(onboarding_id, body.user_id)
    return success_response(data=batch, message="Intern added")


@router.delete("/{onboarding_id}/interns/{user_id}")
async def remove_intern(
    onboarding_id: str,
    user_id: str,
    _: dict = Depends(require_roles(Role.ADMIN, Role.LEADER)),
):
    batch = await service.remove_intern(onboarding_id, user_id)
    return success_response(data=batch, message="Intern removed")
