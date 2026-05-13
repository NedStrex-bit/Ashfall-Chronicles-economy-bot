import os
import sqlite3
from pathlib import Path


DB_PATH = Path(os.getenv("ASHFALL_DB_PATH", "ashfall.db"))


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                total_marks INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS branch_progress (
                user_id INTEGER NOT NULL,
                branch TEXT NOT NULL,
                marks INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, branch)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                admin_id INTEGER NOT NULL,
                branch TEXT NOT NULL,
                action_type TEXT NOT NULL,
                base_marks INTEGER NOT NULL,
                bonus_marks INTEGER NOT NULL DEFAULT 0,
                total_marks INTEGER NOT NULL,
                proof_url TEXT,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                branch TEXT NOT NULL,
                action_type TEXT NOT NULL,
                proof_url TEXT NOT NULL,
                description TEXT,
                metrics TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                reviewer_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TIMESTAMP
            )
            """
        )

        connection.commit()
