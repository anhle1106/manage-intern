import asyncio
from app.database import connect_db, get_db

async def check():
    await connect_db()
    database = get_db()
    
    schedules = await database.schedules.find({}).to_list(None)
    print("\n=== ALL SCHEDULES IN DB ===")
    for s in schedules:
        print(s)

if __name__ == "__main__":
    asyncio.run(check())
