from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from fastapi.responses import RedirectResponse
from typing import Optional
from app.config import get_settings
from app.documents import service
from app.auth.service import decode_token
from app.common.dependencies import get_current_user, require_roles
from app.common.enums import Role
from app.common.response import success_response
from app.common.exceptions import UnauthorizedError

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    onboarding_id: Optional[str] = Form(None),
    user: dict = Depends(require_roles(Role.ADMIN, Role.LEADER)),
):
    doc = await service.upload_document(file, user["id"], onboarding_id)
    return success_response(data=doc, message="Document uploaded")


@router.get("")
async def list_documents(
    onboarding_id: Optional[str] = None,
    _: dict = Depends(get_current_user),
):
    docs = await service.list_documents(onboarding_id)
    return success_response(data=docs)


@router.get("/{doc_id}")
async def get_document(doc_id: str, _: dict = Depends(get_current_user)):
    doc = await service.get_document(doc_id)
    return success_response(data=doc)


@router.get("/{doc_id}/download")
async def download_document(
    doc_id: str,
    token: Optional[str] = Query(None),
):
    if not token:
        raise UnauthorizedError("Token is required for document download")

    try:
        decode_token(token)
    except Exception as e:
        print(f"[Download Auth Warning] Token decode failed: {e}")
        raise UnauthorizedError("Invalid or expired download token")

    doc = await service.get_document(doc_id)
    url = doc["cloudinary_url"]
    # Force Cloudinary attachment header with original filename format
    if "/upload/" in url and "/fl_attachment/" not in url:
        url = url.replace("/upload/", "/upload/fl_attachment/")
    return RedirectResponse(url=url)


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    user: dict = Depends(require_roles(Role.ADMIN, Role.LEADER)),
):
    await service.delete_document(doc_id, user)
    return success_response(message="Document and associated roadmap topics deleted")
