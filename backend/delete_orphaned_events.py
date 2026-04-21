import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.database import AsyncSessionLocal
from sqlalchemy import text

async def run():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("DELETE FROM events WHERE source_post_id IS NULL"))
        await session.commit()
        print(f"Deleted {result.rowcount} orphaned dummy events!")

if __name__ == "__main__":
    asyncio.run(run())
