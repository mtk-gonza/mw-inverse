import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from storage import PlayerStorage


class PlayerStorageTests(unittest.TestCase):
    def test_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "players.sqlite3")
            storage = PlayerStorage(path)
            state = {
                "player_id": "test-player",
                "position": {"x": 3.0, "y": 1.1, "z": -2.0},
                "health": 80,
                "max_health": 100,
                "inventory": {"monster_core": 2},
            }
            storage.save("test-player", state)
            loaded = storage.load("test-player")
            self.assertEqual(loaded["player_id"], state["player_id"])
            self.assertEqual(loaded["inventory"], state["inventory"])
            self.assertEqual(loaded["state_version"], 1)

    def test_missing_player(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            storage = PlayerStorage(str(Path(directory) / "players.sqlite3"))
            self.assertIsNone(storage.load("missing"))

    def test_legacy_state_gets_default_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            storage = PlayerStorage(str(Path(directory) / "players.sqlite3"))
            legacy = {"player_id": "legacy", "inventory": {}}
            storage.save("legacy", legacy)
            loaded = storage.load("legacy")
            self.assertEqual(loaded["state_version"], 1)

    def test_state_journal_keeps_recent_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            storage = PlayerStorage(str(Path(directory) / "players.sqlite3"))
            storage.save("journaled", {"player_id": "journaled", "value": 1})
            storage.save("journaled", {"player_id": "journaled", "value": 2})
            entries = storage.journal("journaled")
            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[0]["state"]["value"], 2)

    def test_rotating_backup_creates_sqlite_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            storage = PlayerStorage(str(Path(directory) / "players.sqlite3"))
            storage.save("backup", {"player_id": "backup", "inventory": {}})
            backup_dir = Path(directory) / "backups"
            backup = Path(storage.rotating_backup(str(backup_dir), keep=2))
            storage.save("backup", {"player_id": "backup", "inventory": {"version": 2}})
            storage.rotating_backup(str(backup_dir), keep=2)
            storage.save("backup", {"player_id": "backup", "inventory": {"version": 3}})
            storage.rotating_backup(str(backup_dir), keep=2)
            backups = sorted(backup_dir.glob("mw_inverse_*.sqlite3"), key=lambda path: path.stat().st_mtime, reverse=True)
            self.assertEqual(len(backups), 2)
            backup = backups[0]
            self.assertTrue(backup.exists())
            import sqlite3
            with closing(sqlite3.connect(backup)) as connection:
                self.assertIsNotNone(connection.execute("SELECT state_json FROM players WHERE player_id = 'backup'").fetchone())
            restored_path = Path(directory) / "restored.sqlite3"
            restored = PlayerStorage(str(restored_path))
            restored_path.unlink(missing_ok=True)
            with closing(sqlite3.connect(backup)) as source, closing(sqlite3.connect(restored_path)) as target:
                source.backup(target)
            self.assertEqual(restored.load("backup")["player_id"], "backup")


if __name__ == "__main__":
    unittest.main()
