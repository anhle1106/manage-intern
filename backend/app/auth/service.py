import bcrypt
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.config import get_settings
from app.database import get_db
from app.common.exceptions import BadRequestError, UnauthorizedError


def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


def create_token(user_id: str, role: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours)
    payload = {"sub": user_id, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise UnauthorizedError(f"Invalid or expired token: {e}")


async def authenticate(email: str, password: str) -> dict:
    db = get_db()
    user = await db.users.find_one({"email": email, "is_active": True})
    if not user or not verify_password(password, user["hashed_password"]):
        raise BadRequestError("Invalid email or password")
    return user
