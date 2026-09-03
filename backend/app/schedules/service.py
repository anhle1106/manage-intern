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


async def list_schedules(user_id: str) -> list[dict]:
    db = get_db()
    cursor = db.schedules.find({"user_id": user_id}).sort("start_date", 1)
    return [_serialize(s) async for s in cursor]


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
    return _serialize(doc)


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
    return _serialize(result)


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
