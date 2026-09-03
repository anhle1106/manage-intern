import asyncio
from app.database import connect_db, get_db

async def fix():
    await connect_db()
    database = get_db()
    # Update 'ngủ' schedule day_of_week to 5 (Saturday)
    result = await database.schedules.update_many(
        {"subject": "ngủ"},
        {"$set": {"day_of_week": 5}}
    )
    print(f"Updated {result.modified_count} schedule entries for 'ngủ'")

if __name__ == "__main__":
    asyncio.run(fix())
