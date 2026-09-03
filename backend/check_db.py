import asyncio
from app.database import get_db

async def check():
    db = get_db()
    user = await db.users.find_one({"email": "intern1@devops.com"})
    print("USER:", user["_id"], user["full_name"])
    
    schedules = await db.schedules.find({"user_id": str(user["_id"])}).to_list(None)
    print("\n=== SCHEDULES IN DB ===")
    for s in schedules:
        print(s)
        
    leaves = await db.leave_requests.find({"user_id": str(user["_id"])}).to_list(None)
    print("\n=== LEAVE REQUESTS IN DB ===")
    for l in leaves:
        print(l)

if __name__ == "__main__":
    asyncio.run(check())
