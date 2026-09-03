from datetime import datetime, timezone
from bson import ObjectId
from app.database import get_db
from app.common.exceptions import NotFoundError


async def _enrich_profile(profile: dict) -> dict:
    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(profile["user_id"])})
    return {
        "id": str(profile["_id"]),
        "user_id": profile["user_id"],
        "full_name": user["full_name"] if user else "Unknown",
        "email": user["email"] if user else "",
        "university": profile.get("university", ""),
        "major": profile.get("major", ""),
        "student_id": profile.get("student_id", ""),
        "phone": profile.get("phone", ""),
        "start_date": profile.get("start_date"),
        "is_active": user.get("is_active", True) if user else False,
    }


async def list_interns(onboarding_id: str | None = None) -> list[dict]:
    db = get_db()
    if onboarding_id:
        onboarding = await db.onboardings.find_one({"_id": ObjectId(onboarding_id)})
        if not onboarding:
            return []
        intern_ids = onboarding.get("intern_ids", [])
        profiles = db.intern_profiles.find({"user_id": {"$in": intern_ids}})
    else:
        profiles = db.intern_profiles.find()

    return [await _enrich_profile(p) async for p in profiles]


async def get_intern(user_id: str) -> dict:
    db = get_db()
    profile = await db.intern_profiles.find_one({"user_id": user_id})
    if not profile:
        raise NotFoundError("Intern profile")
    return await _enrich_profile(profile)


async def update_intern(user_id: str, data: dict) -> dict:
    db = get_db()
    update_data = {k: v for k, v in data.items() if v is not None}
    if not update_data:
        return await get_intern(user_id)

    update_data["updated_at"] = datetime.now(timezone.utc)
    result = await db.intern_profiles.find_one_and_update(
        {"user_id": user_id},
        {"$set": update_data},
        return_document=True,
    )
    if not result:
        raise NotFoundError("Intern profile")
    return await _enrich_profile(result)
