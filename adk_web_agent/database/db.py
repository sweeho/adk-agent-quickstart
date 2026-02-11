"""Async SQLite connection manager for application data."""

import os
import aiosqlite
from pathlib import Path

DB_PATH = os.environ.get("APP_DB_PATH", "./app_data.db")
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


async def get_db() -> aiosqlite.Connection:
    """Get a new async database connection with WAL mode and foreign keys."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db():
    """Initialize the database: create tables and seed default admin user."""
    from adk_web_agent.auth.password import hash_password

    db = await get_db()
    try:
        # Create tables from schema
        schema_sql = SCHEMA_PATH.read_text()
        await db.executescript(schema_sql)

        # Seed admin user if users table is empty
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        count = row[0] if row else 0

        if count == 0:
            admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
            admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
            hashed = hash_password(admin_password)

            await db.execute(
                """INSERT INTO users (user_id, password_hash, is_admin, is_active)
                   VALUES (?, ?, TRUE, TRUE)""",
                (admin_email, hashed),
            )
            await db.commit()
            print(f"[init_db] Seeded admin user: {admin_email}")
        else:
            print(f"[init_db] Users table already has {count} user(s), skipping seed.")
    finally:
        await db.close()
