from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.config import get_settings
from app.database import get_db
from app.common.enums import Role
from bson import ObjectId

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(user_id), "is_active": True})
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")

    user["id"] = str(user["_id"])
    return user


def require_roles(*roles: Role):
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in [r.value for r in roles]:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return user
    return role_checker
