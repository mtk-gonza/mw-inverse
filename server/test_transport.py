import asyncio
import json
import tempfile
import unittest
from pathlib import Path

import main
from storage import PlayerStorage


class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        main.PLAYERS.clear()
        self.directory = tempfile.TemporaryDirectory()
        main.STORAGE = PlayerStorage(str(Path(self.directory.name) / "players.sqlite3"))
        self.server = await asyncio.start_server(main.client_connected, "127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]

    async def asyncTearDown(self) -> None:
        self.server.close()
        await self.server.wait_closed()
        self.directory.cleanup()

    async def test_json_line_login_and_snapshot(self) -> None:
        reader, writer = await asyncio.open_connection("127.0.0.1", self.port)
        writer.write((json.dumps({"type": "login_request", "player_id": "wire-player"}) + "\n").encode())
        await writer.drain()
        login = json.loads((await reader.readline()).decode())
        self.assertEqual(login["type"], "login_result")
        self.assertTrue(login["ok"])

        writer.write((json.dumps({"type": "world_snapshot"}) + "\n").encode())
        await writer.drain()
        snapshot = json.loads((await reader.readline()).decode())
        self.assertEqual(snapshot["type"], "world_snapshot")
        self.assertEqual(snapshot["state"]["player_id"], "wire-player")
        writer.close()
        await writer.wait_closed()

    async def test_chat_broadcasts_to_two_connections(self) -> None:
        first_reader, first_writer = await asyncio.open_connection("127.0.0.1", self.port)
        second_reader, second_writer = await asyncio.open_connection("127.0.0.1", self.port)
        for writer, player_id in ((first_writer, "first"), (second_writer, "second")):
            writer.write((json.dumps({"type": "login_request", "player_id": player_id}) + "\n").encode())
            await writer.drain()
        await first_reader.readline()
        await second_reader.readline()

        first_writer.write((json.dumps({"type": "chat_message", "text": "hola grupo"}) + "\n").encode())
        await first_writer.drain()
        first_message = json.loads((await first_reader.readline()).decode())
        second_message = json.loads((await second_reader.readline()).decode())
        self.assertEqual(first_message, second_message)
        self.assertEqual(first_message["text"], "hola grupo")

        first_writer.close()
        second_writer.close()
        await first_writer.wait_closed()
        await second_writer.wait_closed()


if __name__ == "__main__":
    unittest.main()
