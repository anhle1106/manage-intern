from pydantic import BaseModel
from typing import Optional, List


class AuditReviewCreate(BaseModel):
    onboarding_id: str
    intern_id: str
    topic_id: str
    status: str = "PASSED"  # PASSED, NEEDS_IMPROVEMENT, EXCELLENT, PENDING
    score: Optional[float] = None
    feedback: str = ""


class AuditReviewResponse(BaseModel):
    id: str
    onboarding_id: str
    intern_id: str
    topic_id: str
    leader_id: str
    leader_name: str
    status: str
    score: Optional[float] = None
    feedback: str
    audited_at: str


class LearningTopicResponse(BaseModel):
    id: str
    document_id: str
    onboarding_id: Optional[str] = None
    title: str
    summary: str
    key_concepts: List[str] = []
    subtopics: List[dict] = []
    source_reference: str = ""
    order: int = 0
    completed: bool = False
    completed_subtopics: List[int] = []
    audit_review: Optional[AuditReviewResponse] = None


class ProgressResponse(BaseModel):
    total_topics: int
    completed_topics: int
    percentage: float
    topics: List[LearningTopicResponse] = []
