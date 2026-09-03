from fastapi import APIRouter, Depends
from app.auth.schemas import LoginRequest, TokenResponse
from app.auth import service
from app.common.dependencies import get_current_user
from app.common.response import success_response

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login", response_model=dict)
async def login(body: LoginRequest):
    user = await service.authenticate(body.email, body.password)
    token = service.create_token(str(user["_id"]), user["role"])
    return success_response(
        data=TokenResponse(
            access_token=token,
            role=user["role"],
            user_id=str(user["_id"]),
            full_name=user["full_name"],
        ).model_dump(),
        message="Login successful",
    )


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return success_response(data={
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"],
    })
