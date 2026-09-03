from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings

_client: AsyncIOMotorClient | None = None


async def connect_db():
    global _client
    settings = get_settings()
    _client = AsyncIOMotorClient(
        settings.mongodb_uri,
        maxPoolSize=50,
        minPoolSize=10,
        maxIdleTimeMS=45000,
        connectTimeoutMS=5000,
        serverSelectionTimeoutMS=5000,
    )
    # Ensure database indexes for instant query lookups
    db = _client.get_default_database()
    await db.users.create_index("email")
    await db.schedules.create_index("user_id")
    await db.leave_requests.create_index("user_id")
    await db.intern_profiles.create_index("user_id")
    await db.learning_progress.create_index([("user_id", 1), ("topic_id", 1)])
    await db.documents.create_index("onboarding_id")


async def close_db():
    global _client
    if _client:
        _client.close()
        _client = None


def get_db():
    if not _client:
        raise RuntimeError("Database not connected")
    return _client.get_default_database()
