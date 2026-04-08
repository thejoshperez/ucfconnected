"""
One-time migration: adds rso_name column to the events table.
SQLAlchemy's create_all() only creates missing tables, not new columns —
this script handles the ALTER TABLE for existing deployments.
Run once: python db/migrate_add_rso_name.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from sqlalchemy import text
from db.database import AsyncSessionLocal, init_db

async def run() -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        await session.execute(
            text("ALTER TABLE events ADD COLUMN IF NOT EXISTS rso_name VARCHAR(300)")
        )
        await session.commit()
        print("Migration complete: rso_name column added (or already existed).")

if __name__ == "__main__":
    asyncio.run(run())