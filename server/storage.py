"""Small SQLite persistence layer for the local prototype."""

import json
import sqlite3
import time
from datetime import datetime, timezone
from contextlib import closing
from pathlib import Path
from typing import Any


class PlayerStorage:
    def __init__(self, path: str = "server/data/mw_inverse.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection:
            with connection:
                connection.execute("PRAGMA user_version = 2")
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS players (
                        player_id TEXT PRIMARY KEY,
                        state_json TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS state_journal (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        player_id TEXT NOT NULL,
                        state_json TEXT NOT NULL,
                        created_at REAL NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS accounts (
                        username TEXT PRIMARY KEY,
                        player_id TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        refresh_hash TEXT NOT NULL
                    )
                    """
                )
                for statement in (
                    "ALTER TABLE accounts ADD COLUMN mfa_secret TEXT NOT NULL DEFAULT ''",
                    "ALTER TABLE accounts ADD COLUMN mfa_enabled INTEGER NOT NULL DEFAULT 0",
                ):
                    try:
                        connection.execute(statement)
                    except sqlite3.OperationalError:
                        pass

    def load(self, player_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as connection:
            with connection:
                row = connection.execute(
                    "SELECT state_json FROM players WHERE player_id = ?", (player_id,)
                ).fetchone()
        if row is None:
            return None
        state = json.loads(row[0])
        if "state_version" not in state:
            state["state_version"] = 1
        return state

    def save(self, player_id: str, state: dict[str, Any]) -> None:
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO players(player_id, state_json) VALUES(?, ?)
                    ON CONFLICT(player_id) DO UPDATE SET state_json = excluded.state_json
                    """,
                    (player_id, json.dumps(state, separators=(",", ":"))),
                )
                connection.execute(
                    "INSERT INTO state_journal(player_id, state_json, created_at) VALUES(?, ?, ?)",
                    (player_id, json.dumps(state, separators=(",", ":")), time.time()),
                )

    def journal(self, player_id: str, limit: int = 20) -> list[dict[str, Any]]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT state_json, created_at FROM state_journal WHERE player_id = ? ORDER BY id DESC LIMIT ?",
                (player_id, max(1, min(limit, 100))),
            ).fetchall()
        return [{"state": json.loads(row[0]), "created_at": row[1]} for row in rows]

    def create_account(self, username: str, player_id: str, password_hash: str, refresh_hash: str) -> bool:
        with closing(self._connect()) as connection:
            try:
                with connection:
                    connection.execute(
                        "INSERT INTO accounts(username, player_id, password_hash, refresh_hash) VALUES(?, ?, ?, ?)",
                        (username, player_id, password_hash, refresh_hash),
                    )
                return True
            except sqlite3.IntegrityError:
                return False

    def account(self, username: str) -> dict[str, str] | None:
        with closing(self._connect()) as connection:
            cursor = connection.execute("SELECT * FROM accounts WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row is None:
                return None
            columns = [description[0] for description in cursor.description]
            values = dict(zip(columns, row))
        return {"username": values["username"], "player_id": values["player_id"],
                "password_hash": values["password_hash"], "refresh_hash": values["refresh_hash"],
                "mfa_secret": values.get("mfa_secret", ""), "mfa_enabled": str(values.get("mfa_enabled", 0))}

    def update_refresh_hash(self, username: str, refresh_hash: str) -> None:
        with closing(self._connect()) as connection:
            with connection:
                connection.execute("UPDATE accounts SET refresh_hash = ? WHERE username = ?", (refresh_hash, username))

    def update_mfa(self, username: str, secret: str, enabled: bool) -> None:
        with closing(self._connect()) as connection:
            with connection:
                connection.execute("UPDATE accounts SET mfa_secret = ?, mfa_enabled = ? WHERE username = ?",
                                   (secret, int(enabled), username))

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def backup(self, destination: str) -> str:
        """Create a consistent SQLite backup for local operations."""
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as source:
            with closing(sqlite3.connect(target)) as copy:
                source.backup(copy)
        return str(target)

    def rotating_backup(self, directory: str, keep: int = 5) -> str:
        target_dir = Path(directory)
        target_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        destination = target_dir / f"mw_inverse_{stamp}.sqlite3"
        result = self.backup(str(destination))
        backups = sorted(target_dir.glob("mw_inverse_*.sqlite3"), key=lambda path: path.stat().st_mtime, reverse=True)
        for old_backup in backups[max(1, keep):]:
            old_backup.unlink(missing_ok=True)
        return result
