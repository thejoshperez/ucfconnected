"""
Manual migration v2 — adds email verification, event scheduling, and attendance schema.

This script safely ALTERs existing Postgres tables using IF NOT EXISTS / DO-NOTHING
guards. New tables (event_attendance, email_delivery_log) are created by init_db()
via SQLAlchemy's create_all(), which is called at the top of this script.

Run once:
    cd backend && python db/manual_migration_v2.py

Safe to re-run — all statements are idempotent.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from sqlalchemy import text
from db.database import AsyncSessionLocal, init_db


async def run() -> None:
    # init_db() runs create_all(), which creates event_attendance and
    # email_delivery_log tables if they don't exist yet. Existing tables
    # (users, events, squads, squad_members) are left untouched by create_all().
    print("Initialising database (create_all for new tables) …")
    await init_db()

    async with AsyncSessionLocal() as session:
        print("Running ALTER TABLE migrations …")

        # ── users: email verification columns ─────────────────────────────
        await session.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255)"
        ))
        # Unique index — CREATE INDEX CONCURRENTLY is not supported inside a
        # transaction, so we use a standard unique index here.
        await session.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes
                    WHERE tablename = 'users' AND indexname = 'ix_users_email'
                ) THEN
                    CREATE UNIQUE INDEX ix_users_email ON users (email)
                        WHERE email IS NOT NULL;
                END IF;
            END $$;
        """))
        await session.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE"
        ))
        await session.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_code VARCHAR(6)"
        ))
        await session.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS auto_invites_enabled BOOLEAN NOT NULL DEFAULT TRUE"
        ))
        await session.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS notify_squad_on_rsvp BOOLEAN NOT NULL DEFAULT TRUE"
        ))
        print("  ✓ users: email, email_verified, verification_code, auto_invites_enabled, notify_squad_on_rsvp")

        # ── events: structured time + all-day flag ─────────────────────────
        await session.execute(text(
            "ALTER TABLE events ADD COLUMN IF NOT EXISTS start_at TIMESTAMPTZ"
        ))
        await session.execute(text(
            "ALTER TABLE events ADD COLUMN IF NOT EXISTS end_at TIMESTAMPTZ"
        ))
        await session.execute(text(
            "ALTER TABLE events ADD COLUMN IF NOT EXISTS all_day BOOLEAN NOT NULL DEFAULT FALSE"
        ))
        print("  ✓ events: start_at, end_at, all_day")

        # ── squads: owner foreign key ──────────────────────────────────────
        await session.execute(text(
            "ALTER TABLE squads ADD COLUMN IF NOT EXISTS owner_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL"
        ))
        await session.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes
                    WHERE tablename = 'squads' AND indexname = 'ix_squads_owner_user_id'
                ) THEN
                    CREATE INDEX ix_squads_owner_user_id ON squads (owner_user_id);
                END IF;
            END $$;
        """))
        print("  ✓ squads: owner_user_id")

        # ── squad_members: replace member_name with user_id ───────────────
        # Step 1: Add user_id as nullable FK (existing rows will be NULL).
        await session.execute(text(
            "ALTER TABLE squad_members ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE"
        ))
        await session.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes
                    WHERE tablename = 'squad_members' AND indexname = 'ix_squad_members_user_id'
                ) THEN
                    CREATE INDEX ix_squad_members_user_id ON squad_members (user_id);
                END IF;
            END $$;
        """))
        # Step 2: Make member_name nullable so ORM can insert rows without it.
        await session.execute(text(
            "ALTER TABLE squad_members ALTER COLUMN member_name DROP NOT NULL"
        ))
        # Step 3: Add unique constraint on (squad_id, user_id).
        # The WHERE user_id IS NOT NULL partial index avoids constraint violations
        # for existing rows that have NULL user_id.
        await session.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'uq_squad_member_user'
                ) THEN
                    ALTER TABLE squad_members
                        ADD CONSTRAINT uq_squad_member_user UNIQUE (squad_id, user_id);
                END IF;
            END $$;
        """))
        print("  ✓ squad_members: user_id added, member_name made nullable, unique constraint added")

        await session.commit()

    print("\nMigration v2 complete. New tables (event_attendance, email_delivery_log) were handled by init_db().")


if __name__ == "__main__":
    asyncio.run(run())
