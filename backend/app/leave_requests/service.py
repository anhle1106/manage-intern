from datetime import datetime, timezone
from bson import ObjectId
from app.database import get_db
from app.common.enums import LeaveStatus
from app.common.exceptions import NotFoundError, BadRequestError, ForbiddenError


async def _serialize_list(requests: list[dict]) -> list[dict]:
    if not requests:
        return []
    db = get_db()
    user_ids = [ObjectId(r["user_id"]) for r in requests if ObjectId.is_valid(r.get("user_id"))]
    user_map = {}
    if user_ids:
        cursor = db.users.find({"_id": {"$in": user_ids}})
        async for u in cursor:
            user_map[str(u["_id"])] = u.get("full_name", "Unknown")

    results = []
    for req in requests:
        results.append({
            "id": str(req["_id"]),
            "user_id": req["user_id"],
            "user_name": user_map.get(req["user_id"], "Unknown"),
            "leave_type": req["leave_type"],
            "start_datetime": req["start_datetime"],
            "end_datetime": req["end_datetime"],
            "reason": req["reason"],
            "attachment_url": req.get("attachment_url"),
            "status": req["status"],
            "created_schedule_id": req.get("created_schedule_id"),
            "reviewed_by": req.get("reviewed_by"),
            "reviewed_at": req["reviewed_at"].isoformat() if req.get("reviewed_at") else None,
            "created_at": req["created_at"].isoformat() if req.get("created_at") else "",
        })
    return results


async def _serialize(req: dict) -> dict:
    res = await _serialize_list([req])
    return res[0] if res else {}


async def list_leave_requests(
    user_id: str | None = None,
    status_filter: str | None = None,
    intern_ids: list[str] | None = None,
) -> list[dict]:
    db = get_db()
    query = {}
    if user_id:
        query["user_id"] = user_id
    if status_filter:
        query["status"] = status_filter
    if intern_ids is not None:
        query["user_id"] = {"$in": intern_ids}

    cursor = db.leave_requests.find(query).sort("created_at", -1)
    reqs = [req async for req in cursor]
    return await _serialize_list(reqs)


async def create_leave_request(user_id: str, data: dict) -> dict:
    db = get_db()

    created_schedule_id = None
    if data.get("create_schedule") or data.get("schedule_subject"):
        try:
            start_dt = datetime.fromisoformat(data["start_datetime"])
            end_dt = datetime.fromisoformat(data["end_datetime"])
            
            subject = data.get("schedule_subject") or f"Lịch nghỉ: {data['reason']}"
            schedule_doc = {
                "user_id": user_id,
                "subject": subject,
                "day_of_week": start_dt.weekday(),
                "start_time": start_dt.strftime("%H:%M"),
                "end_time": end_dt.strftime("%H:%M"),
                "location": "",
                "note": f"Tự động tạo từ Đơn xin nghỉ ({data['leave_type']}): {data['reason']}",
                "start_date": start_dt.strftime("%Y-%m-%d"),
                "end_date": end_dt.strftime("%Y-%m-%d"),
                "created_at": datetime.now(timezone.utc),
            }
            s_res = await db.schedules.insert_one(schedule_doc)
            created_schedule_id = str(s_res.inserted_id)
        except Exception as e:
            print(f"[Auto Schedule Creation Warning] {e}")

    doc = {
        "user_id": user_id,
        "leave_type": data["leave_type"],
        "start_datetime": data["start_datetime"],
        "end_datetime": data["end_datetime"],
        "reason": data["reason"],
        "attachment_url": data.get("attachment_url"),
        "status": LeaveStatus.PENDING,
        "created_schedule_id": created_schedule_id,
        "reviewed_by": None,
        "reviewed_at": None,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.leave_requests.insert_one(doc)
    doc["_id"] = result.inserted_id
    return await _serialize(doc)


async def approve_leave(request_id: str, reviewer_id: str) -> dict:
    db = get_db()
    req = await db.leave_requests.find_one({"_id": ObjectId(request_id)})
    if not req:
        raise NotFoundError("Leave request")
    if req["status"] != LeaveStatus.PENDING:
        raise BadRequestError(f"Cannot approve a {req['status']} request")

    result = await db.leave_requests.find_one_and_update(
        {"_id": ObjectId(request_id)},
        {"$set": {
            "status": LeaveStatus.APPROVED,
            "reviewed_by": reviewer_id,
            "reviewed_at": datetime.now(timezone.utc),
        }},
        return_document=True,
    )
    return await _serialize(result)


async def reject_leave(request_id: str, reviewer_id: str) -> dict:
    db = get_db()
    req = await db.leave_requests.find_one({"_id": ObjectId(request_id)})
    if not req:
        raise NotFoundError("Leave request")
    if req["status"] != LeaveStatus.PENDING:
        raise BadRequestError(f"Cannot reject a {req['status']} request")

    result = await db.leave_requests.find_one_and_update(
        {"_id": ObjectId(request_id)},
        {"$set": {
            "status": LeaveStatus.REJECTED,
            "reviewed_by": reviewer_id,
            "reviewed_at": datetime.now(timezone.utc),
        }},
        return_document=True,
    )
    return await _serialize(result)


async def cancel_leave(request_id: str, user_id: str) -> dict:
    db = get_db()
    req = await db.leave_requests.find_one({"_id": ObjectId(request_id)})
    if not req:
        raise NotFoundError("Leave request")
    if req["user_id"] != user_id:
        raise ForbiddenError("Not your leave request")
    if req["status"] not in (LeaveStatus.PENDING,):
        raise BadRequestError("Can only cancel pending requests")

    result = await db.leave_requests.find_one_and_update(
        {"_id": ObjectId(request_id)},
        {"$set": {"status": LeaveStatus.CANCELLED}},
        return_document=True,
    )
    return await _serialize(result)
