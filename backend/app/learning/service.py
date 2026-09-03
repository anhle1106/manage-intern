import asyncio
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


async def _serialize_topics_batch(topics: list[dict], user_id: str | None = None, target_intern_id: str | None = None) -> list[dict]:
    if not topics:
        return []
    db = get_db()
    effective_intern_id = target_intern_id or user_id

    # 1. Collect all document ObjectIds and topic String IDs
    doc_obj_ids = set()
    topic_ids = []
    for t in topics:
        topic_ids.append(str(t["_id"]))
        if t.get("document_id") and ObjectId.is_valid(t["document_id"]):
            doc_obj_ids.add(ObjectId(t["document_id"]))

    # 2. Execute parallel queries over WAN with MongoDB Lean Projections
    async def _fetch_docs():
        if not doc_obj_ids:
            return {}
        cursor = db.documents.find(
            {"_id": {"$in": list(doc_obj_ids)}},
            projection={"_id": 1, "filename": 1}  # Lean projection
        )
        return {str(d["_id"]): d.get("filename", "Training Document") async for d in cursor}

    async def _fetch_progress():
        if not effective_intern_id:
            return {}
        cursor = db.learning_progress.find({
            "user_id": effective_intern_id,
            "topic_id": {"$in": topic_ids},
        })
        return {p["topic_id"]: p async for p in cursor}

    async def _fetch_audits():
        if not effective_intern_id:
            return {}
        cursor = db.audit_reviews.find({
            "intern_id": effective_intern_id,
            "topic_id": {"$in": topic_ids},
        })
        return {a["topic_id"]: _serialize_audit(a) async for a in cursor}

    # Parallel WAN execution of all 3 queries
    doc_map, progress_map, audit_map = await asyncio.gather(
        _fetch_docs(),
        _fetch_progress(),
        _fetch_audits()
    )

    results = []
    for t in topics:
        t_id_str = str(t["_id"])
        document_name = doc_map.get(t.get("document_id", ""), "Training Document")
        
        completed = False
        completed_subtopics = []
        prog = progress_map.get(t_id_str)
        if prog:
            completed = bool(prog.get("completed"))
            completed_subtopics = prog.get("completed_subtopics", [])

        audit_review = audit_map.get(t_id_str)

        results.append({
            "id": t_id_str,
            "document_id": t.get("document_id", ""),
            "document_name": document_name,
            "onboarding_id": t.get("onboarding_id"),
            "title": t["title"],
            "summary": t["summary"],
            "key_concepts": t.get("key_concepts", []),
            "subtopics": t.get("subtopics", []),
            "source_reference": t.get("source_reference", ""),
            "order": t.get("order", 0),
            "completed": completed,
            "completed_subtopics": completed_subtopics,
            "audit_review": audit_review,
        })

    return results


async def _serialize_topic(topic: dict, user_id: str | None = None, target_intern_id: str | None = None) -> dict:
    res = await _serialize_topics_batch([topic], user_id, target_intern_id)
    return res[0] if res else {}


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
    topics = [t async for t in cursor]
    return await _serialize_topics_batch(topics, user_id, target_intern_id)


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
    raw_topics = [t async for t in topics_cursor]
    topics = await _serialize_topics_batch(raw_topics, user_id, effective_intern_id)

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
