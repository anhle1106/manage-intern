from datetime import datetime, timezone
from bson import ObjectId
from app.database import get_db
from app.common.exceptions import NotFoundError, BadRequestError


async def _serialize(batch: dict) -> dict:
    db = get_db()
    leaders = []
    for lid in batch.get("leader_ids", []):
        user = await db.users.find_one({"_id": ObjectId(lid)})
        if user:
            leaders.append({
                "id": str(user["_id"]),
                "full_name": user["full_name"],
                "email": user["email"],
            })

    interns = []
    for iid in batch.get("intern_ids", []):
        user = await db.users.find_one({"_id": ObjectId(iid)})
        if user:
            interns.append({
                "id": str(user["_id"]),
                "full_name": user["full_name"],
                "email": user["email"],
            })

    return {
        "id": str(batch["_id"]),
        "name": batch["name"],
        "description": batch.get("description", ""),
        "start_date": batch["start_date"],
        "end_date": batch["end_date"],
        "status": batch["status"],
        "leaders": leaders,
        "interns": interns,
        "leader_ids": batch.get("leader_ids", []),
        "intern_ids": batch.get("intern_ids", []),
        "created_at": batch["created_at"].isoformat() if batch.get("created_at") else None,
    }


async def list_onboardings(user_id: str | None = None, role: str | None = None) -> list[dict]:
    db = get_db()
    query = {}
    if role == "LEADER" and user_id:
        query["leader_ids"] = user_id
    elif role == "INTERN" and user_id:
        query["intern_ids"] = user_id

    cursor = db.onboardings.find(query).sort("created_at", -1)
    return [await _serialize(b) async for b in cursor]


async def get_onboarding(onboarding_id: str) -> dict:
    db = get_db()
    batch = await db.onboardings.find_one({"_id": ObjectId(onboarding_id)})
    if not batch:
        raise NotFoundError("Onboarding batch")
    return await _serialize(batch)


async def create_onboarding(data: dict) -> dict:
    db = get_db()
    doc = {
        **data,
        "leader_ids": [],
        "intern_ids": [],
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.onboardings.insert_one(doc)
    doc["_id"] = result.inserted_id
    return await _serialize(doc)


async def update_onboarding(onboarding_id: str, data: dict) -> dict:
    db = get_db()
    update_data = {k: v for k, v in data.items() if v is not None}
    if not update_data:
        return await get_onboarding(onboarding_id)

    update_data["updated_at"] = datetime.now(timezone.utc)
    result = await db.onboardings.find_one_and_update(
        {"_id": ObjectId(onboarding_id)},
        {"$set": update_data},
        return_document=True,
    )
    if not result:
        raise NotFoundError("Onboarding batch")
    return await _serialize(result)


async def add_leader(onboarding_id: str, user_id: str) -> dict:
    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(user_id), "role": "LEADER"})
    if not user:
        raise BadRequestError("User is not a leader")

    result = await db.onboardings.find_one_and_update(
        {"_id": ObjectId(onboarding_id)},
        {"$addToSet": {"leader_ids": user_id}},
        return_document=True,
    )
    if not result:
        raise NotFoundError("Onboarding batch")
    return await _serialize(result)


async def remove_leader(onboarding_id: str, user_id: str) -> dict:
    db = get_db()
    result = await db.onboardings.find_one_and_update(
        {"_id": ObjectId(onboarding_id)},
        {"$pull": {"leader_ids": user_id}},
        return_document=True,
    )
    if not result:
        raise NotFoundError("Onboarding batch")
    return await _serialize(result)


async def add_intern(onboarding_id: str, user_id: str) -> dict:
    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(user_id), "role": "INTERN"})
    if not user:
        raise BadRequestError("User is not an intern")

    result = await db.onboardings.find_one_and_update(
        {"_id": ObjectId(onboarding_id)},
        {"$addToSet": {"intern_ids": user_id}},
        return_document=True,
    )
    if not result:
        raise NotFoundError("Onboarding batch")
    return await _serialize(result)


async def remove_intern(onboarding_id: str, user_id: str) -> dict:
    db = get_db()
    result = await db.onboardings.find_one_and_update(
        {"_id": ObjectId(onboarding_id)},
        {"$pull": {"intern_ids": user_id}},
        return_document=True,
    )
    if not result:
        raise NotFoundError("Onboarding batch")
    return await _serialize(result)
