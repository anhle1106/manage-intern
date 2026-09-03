import os
import re
import asyncio
import tempfile
import traceback
import cloudinary
import cloudinary.uploader
from datetime import datetime, timezone
from bson import ObjectId
from fastapi import UploadFile
from app.config import get_settings
from app.database import get_db
from app.common.enums import ProcessingStatus, Role
from app.common.exceptions import NotFoundError, BadRequestError, ForbiddenError


def _init_cloudinary():
    settings = get_settings()
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
    )


async def _serialize(doc: dict) -> dict:
    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(doc["uploaded_by"])})
    batch_name = "General"
    if doc.get("onboarding_id"):
        batch = await db.onboardings.find_one({"_id": ObjectId(doc["onboarding_id"])})
        if batch:
            batch_name = batch["name"]

    return {
        "id": str(doc["_id"]),
        "filename": doc["filename"],
        "file_type": doc["file_type"],
        "file_size": doc["file_size"],
        "cloudinary_url": doc["cloudinary_url"],
        "uploaded_by": doc["uploaded_by"],
        "uploader_name": user["full_name"] if user else "Unknown",
        "onboarding_id": doc.get("onboarding_id"),
        "onboarding_name": batch_name,
        "processing_status": doc["processing_status"],
        "created_at": doc["created_at"].isoformat() if doc.get("created_at") else "",
    }


async def _process_ai_in_background(document_id: str, temp_path: str, onboarding_id: str | None):
    print(f"[Async AI Task] Background analysis started for doc_id: {document_id}")
    try:
        from app.ai.service import analyze_document_file
        await analyze_document_file(document_id, temp_path, onboarding_id)
        
        db = get_db()
        await db.documents.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {"processing_status": ProcessingStatus.COMPLETED}}
        )
        print(f"[Async AI Task] Finished successfully!")
    except Exception as e:
        print(f"[Async AI Task Error] AI Roadmap generation failed for doc {document_id}: {e}")
        traceback.print_exc()
        db = get_db()
        await db.documents.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {"processing_status": ProcessingStatus.FAILED}}
        )
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f"[Temp Cleanup Warning] {e}")


async def upload_document(file: UploadFile, uploaded_by: str, onboarding_id: str | None = None) -> dict:
    settings = get_settings()
    _init_cloudinary()

    filename = file.filename or "file.pdf"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ("pdf", "docx"):
        raise BadRequestError("Only PDF and DOCX files are allowed")

    content = await file.read()
    file_size = len(content)
    max_size = settings.max_upload_size_mb * 1024 * 1024
    if file_size > max_size:
        raise BadRequestError(f"File too large. Max {settings.max_upload_size_mb}MB")

    # Sanitize base filename and preserve exact extension in Cloudinary public_id
    raw_base = filename.rsplit(".", 1)[0]
    safe_base = re.sub(r'[^a-zA-Z0-9_-]', '_', raw_base)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    public_id_with_ext = f"{timestamp}_{safe_base}.{ext}"

    # Non-blocking Cloudinary upload in thread pool
    result = await asyncio.to_thread(
        cloudinary.uploader.upload,
        content,
        resource_type="raw",
        folder="intern-docs",
        public_id=public_id_with_ext,
    )

    db = get_db()
    doc = {
        "filename": filename,
        "file_type": ext,
        "file_size": file_size,
        "cloudinary_url": result["secure_url"],
        "cloudinary_public_id": result.get("public_id", public_id_with_ext),
        "uploaded_by": uploaded_by,
        "onboarding_id": onboarding_id if onboarding_id and onboarding_id.strip() else None,
        "processing_status": ProcessingStatus.PROCESSING,
        "created_at": datetime.now(timezone.utc),
    }
    insert_result = await db.documents.insert_one(doc)
    doc["_id"] = insert_result.inserted_id

    # Save temporary file on disk for Gemini Files API
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"upload_{insert_result.inserted_id}_{safe_base}.{ext}")
    
    with open(temp_path, "wb") as f:
        f.write(content)

    # Launch AI document analysis in background task for instant 200 OK API response!
    asyncio.create_task(_process_ai_in_background(str(insert_result.inserted_id), temp_path, onboarding_id))

    return await _serialize(doc)


async def list_documents(onboarding_id: str | None = None) -> list[dict]:
    db = get_db()
    query = {}
    if onboarding_id:
        query["onboarding_id"] = onboarding_id
    cursor = db.documents.find(query).sort("created_at", -1)
    return [await _serialize(d) async for d in cursor]


async def get_document(doc_id: str) -> dict:
    db = get_db()
    doc = await db.documents.find_one({"_id": ObjectId(doc_id)})
    if not doc:
        raise NotFoundError("Document")
    return await _serialize(doc)


async def delete_document(doc_id: str, user: dict) -> None:
    db = get_db()
    doc = await db.documents.find_one({"_id": ObjectId(doc_id)})
    if not doc:
        raise NotFoundError("Document")

    # Enforce deletion rule: Leaders can ONLY delete files uploaded by themselves!
    if user["role"] == Role.LEADER.value and doc.get("uploaded_by") != user["id"]:
        raise ForbiddenError("Leaders can only delete documents uploaded by themselves")

    # Delete from Cloudinary
    _init_cloudinary()
    try:
        if doc.get("cloudinary_public_id"):
            await asyncio.to_thread(cloudinary.uploader.destroy, doc["cloudinary_public_id"], resource_type="raw")
    except Exception as e:
        print(f"[Cloudinary Delete Warning] {e}")

    # Delete topics generated from this document
    topics = db.learning_topics.find({"document_id": doc_id})
    topic_ids = [str(t["_id"]) async for t in topics]

    if topic_ids:
        await db.learning_progress.delete_many({"topic_id": {"$in": topic_ids}})
        await db.learning_topics.delete_many({"document_id": doc_id})

    # Delete document record
    await db.documents.delete_one({"_id": ObjectId(doc_id)})
