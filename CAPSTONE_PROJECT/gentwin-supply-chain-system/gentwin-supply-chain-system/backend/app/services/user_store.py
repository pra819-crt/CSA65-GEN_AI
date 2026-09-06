"""
User Store.

A lightweight, thread-safe SQLite-backed store for user accounts. Kept
dependency-free (stdlib `sqlite3`) to avoid pulling in a full ORM for what
is a small, well-defined accounts table. A default admin account is seeded
on first startup so there's always at least one admin login available.
"""

from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone
from typing import Optional

from app.core.config import get_settings
from app.core.security import hash_password, verify_password
from app.models.schemas import UserOut, UserRole

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    full_name TEXT,
    hashed_password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    created_at TEXT NOT NULL
);
"""


class UserStore:
    """Thread-safe singleton wrapping a SQLite `users` table."""

    _instance: Optional["UserStore"] = None
    _instance_lock = threading.Lock()

    def __new__(cls) -> "UserStore":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        settings = get_settings()
        self._lock = threading.RLock()
        self._db_path = settings.DB_PATH
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.execute(_CREATE_TABLE_SQL)
            self._conn.commit()
        self._seed_default_admin()

    def _seed_default_admin(self) -> None:
        settings = get_settings()
        if self.get_user_row(settings.DEFAULT_ADMIN_USERNAME) is not None:
            return
        self.create_user(
            username=settings.DEFAULT_ADMIN_USERNAME,
            password=settings.DEFAULT_ADMIN_PASSWORD,
            full_name="System Administrator",
            role=UserRole.ADMIN,
        )

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def get_user_row(self, username: str) -> Optional[sqlite3.Row]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            )
            return cur.fetchone()

    def get_user_out(self, username: str) -> Optional[UserOut]:
        row = self.get_user_row(username)
        if row is None:
            return None
        return _row_to_user_out(row)

    def username_exists(self, username: str) -> bool:
        return self.get_user_row(username) is not None

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def create_user(
        self,
        username: str,
        password: str,
        full_name: Optional[str] = None,
        role: UserRole = UserRole.USER,
    ) -> UserOut:
        if self.username_exists(username):
            raise ValueError(f"Username '{username}' is already taken.")

        hashed = hash_password(password)
        created_at = datetime.now(timezone.utc).isoformat()

        with self._lock:
            self._conn.execute(
                "INSERT INTO users (username, full_name, hashed_password, role, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (username, full_name, hashed, role.value, created_at),
            )
            self._conn.commit()

        return UserOut(
            username=username,
            full_name=full_name,
            role=role,
            created_at=datetime.fromisoformat(created_at),
        )

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def authenticate(self, username: str, password: str) -> Optional[UserOut]:
        row = self.get_user_row(username)
        if row is None:
            return None
        if not verify_password(password, row["hashed_password"]):
            return None
        return _row_to_user_out(row)


def _row_to_user_out(row: sqlite3.Row) -> UserOut:
    return UserOut(
        username=row["username"],
        full_name=row["full_name"],
        role=UserRole(row["role"]),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def get_user_store() -> UserStore:
    return UserStore()
