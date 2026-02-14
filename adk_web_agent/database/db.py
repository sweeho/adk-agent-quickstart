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
    """Initialize the database: create tables, run migrations, and seed default admin user."""
    from adk_web_agent.auth.password import hash_password

    db = await get_db()
    try:
        # Create tables from schema
        schema_sql = SCHEMA_PATH.read_text()
        await db.executescript(schema_sql)

        # Run migrations for existing databases
        await _run_migrations(db)

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


async def _run_migrations(db: aiosqlite.Connection):
    """Add columns that may be missing in older databases."""
    migrations = [
        # Messages table: thought summary & delegation columns
        ("messages", "thought_summary", "ALTER TABLE messages ADD COLUMN thought_summary TEXT"),
        ("messages", "delegated_agent", "ALTER TABLE messages ADD COLUMN delegated_agent TEXT"),
        ("messages", "delegation_chain", "ALTER TABLE messages ADD COLUMN delegation_chain TEXT"),
        # Agent executions table: thought & delegation columns
        ("agent_executions", "thought_summary", "ALTER TABLE agent_executions ADD COLUMN thought_summary TEXT"),
        ("agent_executions", "delegated_agent", "ALTER TABLE agent_executions ADD COLUMN delegated_agent TEXT"),
        ("agent_executions", "delegation_chain", "ALTER TABLE agent_executions ADD COLUMN delegation_chain TEXT"),
        ("agent_executions", "thinking_tokens", "ALTER TABLE agent_executions ADD COLUMN thinking_tokens INTEGER"),
    ]
    for table, column, sql in migrations:
        try:
            cursor = await db.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in await cursor.fetchall()]
            if column not in columns:
                await db.execute(sql)
                print(f"[migration] Added column {table}.{column}")
        except Exception as e:
            print(f"[migration] Skipping {table}.{column}: {e}")
    await db.commit()
