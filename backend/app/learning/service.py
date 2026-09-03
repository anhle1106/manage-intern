from datetime import datetime, timezone
from bson import ObjectId
from app.database import get_db
from app.common.exceptions import NotFoundError, BadRequestError


def _serialize_audit(audit: dict) -> dict:
    return {
        "id": str(audit["_id"]),
        "onboarding_id": audit["onboarding_id"],
        "intern_id": audit["intern_id"],
        "topic_id": audit["topic_id"],
        "leader_id": audit["leader_id"],
        "leader_name": audit.get("leader_name", "TechLead"),
        "status": audit.get("status", "PASSED"),
        "score": audit.get("score"),
        "feedback": audit.get("feedback", ""),
        "audited_at": audit["audited_at"].isoformat() if audit.get("audited_at") else "",
    }


async def _serialize_topic(topic: dict, user_id: str | None = None, target_intern_id: str | None = None) -> dict:
    db = get_db()
    effective_intern_id = target_intern_id or user_id

    document_name = "Training Document"
    if topic.get("document_id"):
        try:
            doc = await db.documents.find_one({"_id": ObjectId(topic["document_id"])})
            if doc:
                document_name = doc.get("filename", "Training Document")
        except Exception:
            pass

    completed = False
    completed_subtopics = []
    if effective_intern_id:
        progress = await db.learning_progress.find_one({
            "user_id": effective_intern_id,
            "topic_id": str(topic["_id"]),
        })
        if progress:
            completed = bool(progress.get("completed"))
            completed_subtopics = progress.get("completed_subtopics", [])

    # Fetch audit review for this topic and intern
    audit_review = None
    if effective_intern_id:
        audit = await db.audit_reviews.find_one({
            "topic_id": str(topic["_id"]),
            "intern_id": effective_intern_id,
        })
        if audit:
            audit_review = _serialize_audit(audit)

    return {
        "id": str(topic["_id"]),
        "document_id": topic.get("document_id", ""),
        "document_name": document_name,
        "onboarding_id": topic.get("onboarding_id"),
        "title": topic["title"],
        "summary": topic["summary"],
        "key_concepts": topic.get("key_concepts", []),
        "subtopics": topic.get("subtopics", []),
        "source_reference": topic.get("source_reference", ""),
        "order": topic.get("order", 0),
        "completed": completed,
        "completed_subtopics": completed_subtopics,
        "audit_review": audit_review,
    }


async def save_audit_review(leader: dict, data: dict) -> dict:
    db = get_db()
    
    # Validate topic exists
    topic = await db.learning_topics.find_one({"_id": ObjectId(data["topic_id"])})
    if not topic:
        raise NotFoundError("Learning Topic")

    audit_doc = {
        "onboarding_id": data["onboarding_id"],
        "intern_id": data["intern_id"],
        "topic_id": data["topic_id"],
        "leader_id": leader["id"],
        "leader_name": leader.get("full_name", "TechLead"),
        "status": data.get("status", "PASSED"),
        "score": data.get("score"),
        "feedback": data.get("feedback", ""),
        "audited_at": datetime.now(timezone.utc),
    }

    result = await db.audit_reviews.find_one_and_update(
        {
            "topic_id": data["topic_id"],
            "intern_id": data["intern_id"],
        },
        {"$set": audit_doc},
        upsert=True,
        return_document=True,
    )
    
    if not result:
        result = await db.audit_reviews.find_one({
            "topic_id": data["topic_id"],
            "intern_id": data["intern_id"],
        })

    return _serialize_audit(result)


async def list_topics(
    user_id: str | None = None,
    document_id: str | None = None,
    onboarding_id: str | None = None,
    target_intern_id: str | None = None,
) -> list[dict]:
    db = get_db()
    query = {}
    if document_id:
        query["document_id"] = document_id
    if onboarding_id:
        query["onboarding_id"] = onboarding_id

    cursor = db.learning_topics.find(query).sort("order", 1)
    return [await _serialize_topic(t, user_id, target_intern_id) async for t in cursor]


async def get_topic(topic_id: str, user_id: str | None = None, target_intern_id: str | None = None) -> dict:
    db = get_db()
    topic = await db.learning_topics.find_one({"_id": ObjectId(topic_id)})
    if not topic:
        raise NotFoundError("Learning topic")
    return await _serialize_topic(topic, user_id, target_intern_id)


async def complete_topic(topic_id: str, user_id: str) -> dict:
    db = get_db()
    topic = await db.learning_topics.find_one({"_id": ObjectId(topic_id)})
    if not topic:
        raise NotFoundError("Learning topic")

    subtopics = topic.get("subtopics", [])
    all_subtopic_indices = list(range(len(subtopics)))

    await db.learning_progress.update_one(
        {"user_id": user_id, "topic_id": topic_id},
        {"$set": {
            "completed": True,
            "completed_subtopics": all_subtopic_indices,
            "updated_at": datetime.now(timezone.utc),
        }},
        upsert=True
    )
    return await _serialize_topic(topic, user_id)


async def toggle_subtopic(topic_id: str, subtopic_index: int, user_id: str) -> dict:
    db = get_db()
    topic = await db.learning_topics.find_one({"_id": ObjectId(topic_id)})
    if not topic:
        raise NotFoundError("Learning topic")

    subtopics = topic.get("subtopics", [])
    if subtopic_index < 0 or subtopic_index >= len(subtopics):
        raise BadRequestError("Invalid subtopic index")

    progress = await db.learning_progress.find_one({"user_id": user_id, "topic_id": topic_id})
    completed_subtopics = progress.get("completed_subtopics", []) if progress else []

    if subtopic_index in completed_subtopics:
        completed_subtopics.remove(subtopic_index)
    else:
        completed_subtopics.append(subtopic_index)

    is_all_completed = len(completed_subtopics) == len(subtopics) and len(subtopics) > 0

    await db.learning_progress.update_one(
        {"user_id": user_id, "topic_id": topic_id},
        {"$set": {
            "completed": is_all_completed,
            "completed_subtopics": completed_subtopics,
            "updated_at": datetime.now(timezone.utc),
        }},
        upsert=True
    )
    return await _serialize_topic(topic, user_id)


async def get_progress(
    user_id: str,
    onboarding_id: str | None = None,
    target_intern_id: str | None = None,
) -> dict:
    db = get_db()
    effective_intern_id = target_intern_id or user_id

    query = {}
    if onboarding_id:
        query["onboarding_id"] = onboarding_id

    topics_cursor = db.learning_topics.find(query).sort("order", 1)
    topics = [await _serialize_topic(t, user_id, effective_intern_id) async for t in topics_cursor]

    total_topics = len(topics)
    if total_topics == 0:
        return {"total_topics": 0, "completed_topics": 0, "percentage": 0.0, "topics": []}

    total_subtopics_count = 0
    completed_subtopics_count = 0

    for t in topics:
        subtopics = t.get("subtopics", [])
        num_sub = len(subtopics)
        completed_subs = t.get("completed_subtopics", [])
        
        if num_sub == 0:
            num_sub = 1
            total_subtopics_count += 1
            if t.get("completed"):
                completed_subtopics_count += 1
        else:
            total_subtopics_count += num_sub
            if t.get("completed"):
                completed_subtopics_count += num_sub
            else:
                completed_subtopics_count += len(completed_subs)

    completed_topics_count = sum(1 for t in topics if t.get("completed"))
    percentage = round((completed_subtopics_count / total_subtopics_count) * 100, 1) if total_subtopics_count > 0 else 0.0

    return {
        "total_topics": total_topics,
        "completed_topics": completed_topics_count,
        "percentage": percentage,
        "topics": topics,
    }
