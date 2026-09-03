from pydantic import BaseModel
from typing import Optional


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    cloudinary_url: str
    uploaded_by: str
    uploader_name: str
    onboarding_id: Optional[str] = None
    processing_status: str
    created_at: str
