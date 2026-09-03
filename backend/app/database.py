from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings

_client: AsyncIOMotorClient | None = None


async def connect_db():
    global _client
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongodb_uri)


async def close_db():
    global _client
    if _client:
        _client.close()
        _client = None


def get_db():
    if not _client:
        raise RuntimeError("Database not connected")
    return _client.get_default_database()
