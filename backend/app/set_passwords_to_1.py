import asyncio
from app.database import connect_db, get_db
from app.auth.service import hash_password

async def update_all_passwords():
    await connect_db()
    db = get_db()
    
    new_hash = hash_password("1")
    result = await db.users.update_many(
        {},
        {"$set": {"hashed_password": new_hash}}
    )
    print(f"Successfully updated passwords to '1' for {result.modified_count} users!")

if __name__ == "__main__":
    asyncio.run(update_all_passwords())
