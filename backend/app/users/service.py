from datetime import datetime, timezone
from bson import ObjectId
from app.database import get_db
from app.auth.service import hash_password
from app.common.exceptions import NotFoundError, BadRequestError


def _serialize(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"],
        "is_active": user.get("is_active", True),
        "created_at": user.get("created_at", "").isoformat() if user.get("created_at") else None,
    }


async def list_users(role_filter: str | None = None) -> list[dict]:
    db = get_db()
    query = {}
    if role_filter:
        query["role"] = role_filter
    cursor = db.users.find(query).sort("created_at", -1)
    return [_serialize(u) async for u in cursor]


async def get_user(user_id: str) -> dict:
    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise NotFoundError("User")
    return _serialize(user)


async def create_user(data: dict) -> dict:
    db = get_db()
    existing = await db.users.find_one({"email": data["email"]})
    if existing:
        raise BadRequestError("Email already exists")

    doc = {
        "email": data["email"],
        "hashed_password": hash_password(data["password"]),
        "full_name": data["full_name"],
        "role": data.get("role", "INTERN"),
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.users.insert_one(doc)
    doc["_id"] = result.inserted_id

    if doc["role"] == "INTERN":
        await db.intern_profiles.insert_one({
            "user_id": str(result.inserted_id),
            "university": "",
            "major": "",
            "student_id": "",
            "phone": "",
            "start_date": None,
            "created_at": datetime.now(timezone.utc),
        })

    return _serialize(doc)


async def update_user(user_id: str, data: dict) -> dict:
    db = get_db()
    update_data = {k: v for k, v in data.items() if v is not None}
    if not update_data:
        raise BadRequestError("No fields to update")

    update_data["updated_at"] = datetime.now(timezone.utc)
    result = await db.users.find_one_and_update(
        {"_id": ObjectId(user_id)},
        {"$set": update_data},
        return_document=True,
    )
    if not result:
        raise NotFoundError("User")
    return _serialize(result)


async def delete_user(user_id: str) -> None:
    db = get_db()
    result = await db.users.find_one_and_update(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}},
    )
    if not result:
        raise NotFoundError("User")
