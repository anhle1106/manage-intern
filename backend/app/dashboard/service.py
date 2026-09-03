from datetime import datetime, timezone
from bson import ObjectId
from app.database import get_db
from app.common.enums import Role, LeaveStatus, OnboardingStatus
from app.learning.service import get_progress


async def get_dashboard(user: dict) -> dict:
    role = user["role"]
    if role == Role.INTERN:
        return await _intern_dashboard(user)
    elif role == Role.LEADER:
        return await _leader_dashboard(user)
    else:
        return await _admin_dashboard(user)


async def _get_intern_doc_progresses(intern_ids_list: list[str], leader_id: str = None) -> list[dict]:
    db = get_db()
    if not intern_ids_list:
        return []

    results = []
    for iid in intern_ids_list:
        try:
            intern_user = await db.users.find_one({"_id": ObjectId(iid)})
            if not intern_user:
                continue

            batch_query = {"intern_ids": iid}
            if leader_id:
                # Strictly restrict to batches managed by this leader!
                batch_query["leader_ids"] = leader_id

            batches = await db.onboardings.find(batch_query).to_list(None)
            batch_ids = [str(b["_id"]) for b in batches]
            batch_names = [b["name"] for b in batches]

            if not batch_ids and leader_id:
                # Intern has no batches managed by this leader, skip
                continue

            doc_query = {}
            if batch_ids:
                doc_query = {"$or": [{"onboarding_id": {"$in": batch_ids}}, {"onboarding_id": None}]}

            docs = await db.documents.find(doc_query).to_list(None)
            
            for d in docs:
                doc_id_str = str(d["_id"])
                topics = await db.learning_topics.find({"document_id": doc_id_str}).to_list(None)
                total_topics = len(topics)
                if total_topics == 0:
                    continue

                topic_ids = [str(t["_id"]) for t in topics]

                total_subtopics = 0
                completed_subtopics = 0
                for t in topics:
                    subs = t.get("subtopics", [])
                    num_subs = len(subs) if subs else 1
                    total_subtopics += num_subs
                    
                    prog = await db.learning_progress.find_one({"user_id": iid, "topic_id": str(t["_id"])})
                    if prog:
                        if prog.get("completed"):
                            completed_subtopics += num_subs
                        else:
                            completed_subtopics += len(prog.get("completed_subtopics", []))

                completed_topics_count = await db.learning_progress.count_documents({
                    "user_id": iid,
                    "completed": True,
                    "topic_id": {"$in": topic_ids},
                })

                percentage = round((completed_subtopics / total_subtopics) * 100, 1) if total_subtopics > 0 else 0.0

                doc_batch_name = "Chung"
                if d.get("onboarding_id"):
                    matching_batch = next((b for b in batches if str(b["_id"]) == str(d["onboarding_id"])), None)
                    if matching_batch:
                        doc_batch_name = matching_batch["name"]

                results.append({
                    "intern_id": iid,
                    "intern_name": intern_user["full_name"],
                    "intern_email": intern_user["email"],
                    "batch_names": batch_names,
                    "doc_id": doc_id_str,
                    "filename": d["filename"],
                    "doc_batch_name": doc_batch_name,
                    "total_topics": total_topics,
                    "completed_topics": completed_topics_count,
                    "percentage": percentage,
                })
        except Exception as e:
            print(f"[Dashboard Progress Error] {e}")

    # Sort Alphabetically (A-Z) by Intern Full Name
    results.sort(key=lambda x: x["intern_name"].lower())
    return results


async def _get_progresses_grouped_by_batch(batches: list[dict]) -> list[dict]:
    db = get_db()
    if not batches:
        return []

    # 1. Collect all intern ObjectIds and batch IDs
    all_intern_ids = set()
    all_batch_id_strs = []
    for b in batches:
        b_id = str(b["_id"])
        all_batch_id_strs.append(b_id)
        for iid in b.get("intern_ids", []):
            if iid:
                all_intern_ids.add(iid)

    if not all_intern_ids:
        return [{
            "batch_id": str(b["_id"]),
            "batch_name": b["name"],
            "batch_status": b["status"],
            "avg_percentage": 0.0,
            "interns": [],
        } for b in batches]

    # 2. Batch fetch all intern users in 1 query
    user_obj_ids = [ObjectId(i) for i in all_intern_ids if ObjectId.is_valid(i)]
    users_cursor = db.users.find({"_id": {"$in": user_obj_ids}})
    user_map = {str(u["_id"]): u async for u in users_cursor}

    # 3. Batch fetch all documents
    docs = await db.documents.find({
        "$or": [{"onboarding_id": {"$in": all_batch_id_strs}}, {"onboarding_id": None}]
    }).to_list(None)

    doc_ids = [str(d["_id"]) for d in docs]

    # 4. Batch fetch all learning topics
    topics = await db.learning_topics.find({"document_id": {"$in": doc_ids}}).to_list(None)
    
    # Map topics by document_id
    doc_topics_map = {}
    for t in topics:
        d_id = t.get("document_id")
        if d_id not in doc_topics_map:
            doc_topics_map[d_id] = []
        doc_topics_map[d_id].append(t)

    # 5. Batch fetch all learning_progress for all interns in 1 query
    progress_cursor = db.learning_progress.find({"user_id": {"$in": list(all_intern_ids)}})
    progress_map = {}
    async for p in progress_cursor:
        key = (p["user_id"], p["topic_id"])
        progress_map[key] = p

    # Build response in-memory
    group_results = []
    for b in batches:
        batch_id_str = str(b["_id"])
        intern_ids = b.get("intern_ids", [])
        
        # Filter docs relevant to this batch
        batch_docs = [d for d in docs if not d.get("onboarding_id") or d.get("onboarding_id") == batch_id_str]
        batch_intern_list = []

        for iid in intern_ids:
            intern_user = user_map.get(iid)
            if not intern_user:
                continue

            doc_progresses = []
            for d in batch_docs:
                doc_id_str = str(d["_id"])
                t_list = doc_topics_map.get(doc_id_str, [])
                if not t_list:
                    continue

                total_subtopics = 0
                completed_subtopics = 0
                completed_topics_count = 0

                for t in t_list:
                    t_id = str(t["_id"])
                    subs = t.get("subtopics", [])
                    num_subs = len(subs) if subs else 1
                    total_subtopics += num_subs

                    prog = progress_map.get((iid, t_id))
                    if prog:
                        if prog.get("completed"):
                            completed_subtopics += num_subs
                            completed_topics_count += 1
                        else:
                            completed_subtopics += len(prog.get("completed_subtopics", []))

                pct = round((completed_subtopics / total_subtopics) * 100, 1) if total_subtopics > 0 else 0.0
                doc_progresses.append({
                    "doc_id": doc_id_str,
                    "filename": d["filename"],
                    "total_topics": len(t_list),
                    "completed_topics": completed_topics_count,
                    "percentage": pct,
                })

            overall_pct = round(sum(dp["percentage"] for dp in doc_progresses) / len(doc_progresses), 1) if doc_progresses else 0.0

            batch_intern_list.append({
                "intern_id": iid,
                "intern_name": intern_user["full_name"],
                "intern_email": intern_user["email"],
                "overall_percentage": overall_pct,
                "docs": doc_progresses,
            })

        batch_intern_list.sort(key=lambda x: x["intern_name"].lower())
        group_avg_pct = round(sum(i["overall_percentage"] for i in batch_intern_list) / len(batch_intern_list), 1) if batch_intern_list else 0.0

        group_results.append({
            "batch_id": batch_id_str,
            "batch_name": b["name"],
            "batch_status": b["status"],
            "avg_percentage": group_avg_pct,
            "interns": batch_intern_list,
        })

    return group_results


async def _intern_dashboard(user: dict) -> dict:
    db = get_db()
    user_id = user["id"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    weekday = datetime.now(timezone.utc).weekday()

    today_schedules_cursor = await db.schedules.find({
        "user_id": user_id,
        "$or": [
            {"is_recurring": True, "days_of_week": weekday},
            {"is_recurring": False, "day_of_week": weekday},
        ],
        "start_date": {"$lte": today},
        "end_date": {"$gte": today},
    }).sort("start_time", 1).to_list(None)

    today_schedule = [{
        "id": str(s["_id"]),
        "subject": s["subject"],
        "start_time": s["start_time"],
        "end_time": s["end_time"],
        "location": s.get("location", ""),
        "is_today": True,
    } for s in today_schedules_cursor]

    upcoming_schedules_cursor = await db.schedules.find({
        "user_id": user_id,
        "end_date": {"$gte": today},
    }).sort([("start_date", 1), ("start_time", 1)]).to_list(10)

    upcoming_schedule = [{
        "id": str(s["_id"]),
        "subject": s["subject"],
        "is_recurring": s.get("is_recurring", False),
        "days_of_week": s.get("days_of_week", [s.get("day_of_week", 0)]),
        "day_of_week": s.get("day_of_week", 0),
        "start_date": s["start_date"],
        "end_date": s["end_date"],
        "start_time": s["start_time"],
        "end_time": s["end_time"],
        "location": s.get("location", ""),
    } for s in upcoming_schedules_cursor]

    pending_leaves = await db.leave_requests.count_documents({
        "user_id": user_id,
        "status": LeaveStatus.PENDING,
    })

    batches = await db.onboardings.find({"intern_ids": user_id}).to_list(None)
    batch_progresses = await _get_progresses_grouped_by_batch(batches)
    batch_info = [{
        "id": str(b["_id"]),
        "name": b["name"],
        "status": b["status"],
        "avg_percentage": next((bp["avg_percentage"] for bp in batch_progresses if bp["batch_id"] == str(b["_id"])), 0.0),
    } for b in batches]

    progress_data = await get_progress(user_id)

    return {
        "role": "INTERN",
        "today_schedule": today_schedule,
        "upcoming_schedules": upcoming_schedule,
        "pending_leaves": pending_leaves,
        "onboarding_batches": batch_info,
        "learning_progress": {
            "total": progress_data["total_topics"],
            "completed": progress_data["completed_topics"],
            "percentage": progress_data["percentage"],
        },
    }


async def _leader_dashboard(user: dict) -> dict:
    db = get_db()
    user_id = user["id"]

    batches = await db.onboardings.find({"leader_ids": user_id}).to_list(None)
    intern_ids = set()
    for b in batches:
        intern_ids.update(b.get("intern_ids", []))

    intern_count = len(intern_ids)

    pending_leaves = await db.leave_requests.count_documents({
        "user_id": {"$in": list(intern_ids)},
        "status": LeaveStatus.PENDING,
    })

    batch_info = [{
        "id": str(b["_id"]),
        "name": b["name"],
        "status": b["status"],
        "leader_count": len(b.get("leader_ids", [])),
        "intern_count": len(b.get("intern_ids", [])),
    } for b in batches]

    recent_docs = await db.documents.find().sort("created_at", -1).to_list(5)
    docs = [{
        "id": str(d["_id"]),
        "filename": d["filename"],
        "processing_status": d["processing_status"],
    } for d in recent_docs]

    batch_progresses = await _get_progresses_grouped_by_batch(batches)
    intern_doc_progresses = await _get_intern_doc_progresses(list(intern_ids), leader_id=user_id)

    return {
        "role": "LEADER",
        "intern_count": intern_count,
        "pending_leaves": pending_leaves,
        "onboarding_batches": batch_info,
        "recent_documents": docs,
        "batch_progresses": batch_progresses,
        "intern_doc_progresses": intern_doc_progresses,
    }


async def _admin_dashboard(user: dict) -> dict:
    db = get_db()

    total_interns = await db.users.count_documents({"role": "INTERN", "is_active": True})
    total_leaders = await db.users.count_documents({"role": "LEADER", "is_active": True})
    active_batches = await db.onboardings.count_documents({"status": OnboardingStatus.ACTIVE})
    pending_leaves = await db.leave_requests.count_documents({"status": LeaveStatus.PENDING})

    doc_stats = {
        "total": await db.documents.count_documents({}),
        "processing": await db.documents.count_documents({"processing_status": "PROCESSING"}),
        "completed": await db.documents.count_documents({"processing_status": "COMPLETED"}),
        "failed": await db.documents.count_documents({"processing_status": "FAILED"}),
    }

    batches = await db.onboardings.find().sort("created_at", -1).to_list(None)
    batch_info = [{
        "id": str(b["_id"]),
        "name": b["name"],
        "intern_count": len(b.get("intern_ids", [])),
    } for b in batches]

    all_interns = await db.users.find({"role": "INTERN", "is_active": True}).to_list(None)
    all_intern_ids = [str(u["_id"]) for u in all_interns]
    batch_progresses = await _get_progresses_grouped_by_batch(batches)
    intern_doc_progresses = await _get_intern_doc_progresses(all_intern_ids, leader_id=None)

    return {
        "role": "ADMIN",
        "total_interns": total_interns,
        "total_leaders": total_leaders,
        "active_batches": active_batches,
        "pending_leaves": pending_leaves,
        "document_stats": doc_stats,
        "onboarding_batches": batch_info,
        "batch_progresses": batch_progresses,
        "intern_doc_progresses": intern_doc_progresses,
    }
