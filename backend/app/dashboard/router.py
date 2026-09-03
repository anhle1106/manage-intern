from fastapi import APIRouter, Depends
from app.dashboard import service
from app.common.dependencies import get_current_user
from app.common.response import success_response

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("")
async def get_dashboard(user: dict = Depends(get_current_user)):
    data = await service.get_dashboard(user)
    return success_response(data=data)
