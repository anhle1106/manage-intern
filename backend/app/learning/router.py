from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.learning import service
from app.learning.schemas import AuditReviewCreate
from app.common.dependencies import get_current_user, require_roles
from app.common.enums import Role
from app.common.response import success_response

router = APIRouter(prefix="/api/learning", tags=["Learning"])


@router.get("/topics")
async def list_topics(
    document_id: Optional[str] = None,
    onboarding_id: Optional[str] = None,
    intern_id: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    topics = await service.list_topics(user["id"], document_id, onboarding_id, target_intern_id=intern_id)
    return success_response(data=topics)


@router.get("/progress")
async def get_progress(
    onboarding_id: Optional[str] = None,
    intern_id: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    progress = await service.get_progress(user["id"], onboarding_id, target_intern_id=intern_id)
    return success_response(data=progress)


@router.put("/topics/{topic_id}/complete")
async def complete_topic(topic_id: str, user: dict = Depends(require_roles(Role.INTERN))):
    topic = await service.complete_topic(topic_id, user["id"])
    return success_response(data=topic, message="Topic marked complete")


@router.put("/topics/{topic_id}/uncomplete")
async def uncomplete_topic(topic_id: str, user: dict = Depends(require_roles(Role.INTERN))):
    topic = await service.uncomplete_topic(topic_id, user["id"])
    return success_response(data=topic, message="Topic marked incomplete")


@router.put("/topics/{topic_id}/subtopics/{subtopic_index}/toggle")
async def toggle_subtopic(topic_id: str, subtopic_index: int, user: dict = Depends(require_roles(Role.INTERN))):
    topic = await service.toggle_subtopic(topic_id, subtopic_index, user["id"])
    return success_response(data=topic, message="Subtopic progress updated")


@router.post("/audits")
async def save_audit_review(
    body: AuditReviewCreate,
    user: dict = Depends(require_roles(Role.LEADER, Role.ADMIN)),
):
    audit = await service.save_audit_review(user, body.model_dump())
    return success_response(data=audit, message="TechLead audit review saved successfully")
