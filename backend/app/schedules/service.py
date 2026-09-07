from datetime import datetime, timezone
from bson import ObjectId
from app.database import get_db
from app.common.exceptions import NotFoundError, ForbiddenError


def _serialize(entry: dict) -> dict:
    return {
        "id": str(entry["_id"]),
        "user_id": entry["user_id"],
        "subject": entry["subject"],
        "is_recurring": entry.get("is_recurring", False),
        "days_of_week": entry.get("days_of_week", [entry.get("day_of_week", 0)]),
        "day_of_week": entry.get("day_of_week", 0),
        "start_time": entry["start_time"],
        "end_time": entry["end_time"],
        "location": entry.get("location", ""),
        "note": entry.get("note", ""),
        "start_date": entry["start_date"],
        "end_date": entry["end_date"],
    }


async def list_schedules(user_id: str | None = None, user_ids: list[str] | None = None) -> list[dict]:
    db = get_db()
    query = {}
    if user_ids:
        query["user_id"] = {"$in": user_ids}
    elif user_id and user_id != "ALL":
        query["user_id"] = user_id

    cursor = db.schedules.find(query).sort("start_date", 1)
    schedules = [s async for s in cursor]
    if not schedules:
        return []

    # Map user_id to user full_name for batch schedule response
    u_ids = list({ObjectId(s["user_id"]) for s in schedules if ObjectId.is_valid(s.get("user_id"))})
    user_map = {}
    if u_ids:
        u_cursor = db.users.find({"_id": {"$in": u_ids}})
        async for u in u_cursor:
            user_map[str(u["_id"])] = u.get("full_name", "Unknown User")

    results = []
    for s in schedules:
        item = _serialize(s)
        item["user_name"] = user_map.get(s.get("user_id"), "Unknown User")
        results.append(item)

    return results


async def create_schedule(user_id: str, data: dict) -> dict:
    db = get_db()

    # Ensure days_of_week or day_of_week is populated
    if not data.get("is_recurring"):
        # For non-recurring (date-range) schedules, calculate day_of_week from start_date
        if data.get("start_date"):
            try:
                dt = datetime.strptime(data["start_date"], "%Y-%m-%d")
                data["day_of_week"] = dt.weekday()
            except Exception:
                pass
        data["is_recurring"] = False
        data["days_of_week"] = []

    doc = {
        "user_id": user_id,
        **data,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.schedules.insert_one(doc)
    doc["_id"] = result.inserted_id
    
    # Attach user_name to created schedule
    res = _serialize(doc)
    user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
    res["user_name"] = user_doc.get("full_name", "Unknown User") if user_doc else "Unknown User"
    return res


async def update_schedule(schedule_id: str, user_id: str, data: dict) -> dict:
    db = get_db()
    entry = await db.schedules.find_one({"_id": ObjectId(schedule_id)})
    if not entry:
        raise NotFoundError("Schedule entry")
    if entry["user_id"] != user_id:
        raise ForbiddenError("Not your schedule entry")

    update_data = {k: v for k, v in data.items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)
    result = await db.schedules.find_one_and_update(
        {"_id": ObjectId(schedule_id)},
        {"$set": update_data},
        return_document=True,
    )
    res = _serialize(result)
    user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
    res["user_name"] = user_doc.get("full_name", "Unknown User") if user_doc else "Unknown User"
    return res


async def delete_schedule(schedule_id: str, user_id: str) -> None:
    db = get_db()
    entry = await db.schedules.find_one({"_id": ObjectId(schedule_id)})
    if not entry:
        raise NotFoundError("Schedule entry")
    if entry["user_id"] != user_id:
        raise ForbiddenError("Not your schedule entry")
    await db.schedules.delete_one({"_id": ObjectId(schedule_id)})


async def check_availability(user_id: str, day_of_week: int, start_time: str, end_time: str) -> bool:
    db = get_db()
    conflict = await db.schedules.find_one({
        "user_id": user_id,
        "$or": [
            {"is_recurring": True, "days_of_week": day_of_week},
            {"is_recurring": False, "day_of_week": day_of_week},
        ],
        "start_time": {"$lt": end_time},
        "end_time": {"$gt": start_time},
    })
    return conflict is None
