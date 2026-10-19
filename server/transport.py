"""TCP transport lifecycle for the local authoritative server.

This module deliberately knows nothing about the game domain.  The domain
handler and the small runtime registries are injected by ``main.py`` so the
wire protocol can be tested independently from the message implementation.
"""

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any


async def client_connected(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    *,
    handle_message: Callable[[Any, dict[str, Any]], Awaitable[tuple[Any, dict[str, Any]]]],
    response: Callable[..., dict[str, Any]],
    presence_snapshot: Callable[[], dict[str, Any]],
    chat_recipient_allowed: Callable[[Any, Any, str, str], bool],
    max_message_bytes: int,
    active_writers: set[asyncio.StreamWriter],
    writer_players: dict[asyncio.StreamWriter, str],
    online_player_ids: set[str],
    players: dict[str, Any],
) -> None:
    """Read newline-delimited JSON and route responses to connected clients."""
    player: Any | None = None
    try:
        while line := await reader.readline():
            if len(line) > max_message_bytes:
                result = response("error", code="message_too_large")
                writer.write((json.dumps(result, separators=(",", ":")) + "\n").encode())
                await writer.drain()
                break
            try:
                message = json.loads(line)
                if not isinstance(message, dict):
                    raise ValueError("message must be an object")
                player, result = await handle_message(player, message)
            except (ValueError, TypeError, json.JSONDecodeError) as error:
                result = response("error", code="invalid_message", detail=str(error))

            if player is not None:
                active_writers.add(writer)
                writer_players[writer] = player.player_id
                online_player_ids.add(player.player_id)

            encoded = (json.dumps(result, separators=(",", ":")) + "\n").encode()
            if result.get("type") == "chat_event" and result.get("ok", False):
                for recipient in list(active_writers):
                    recipient_player = players.get(writer_players.get(recipient, ""))
                    if not chat_recipient_allowed(
                        player, recipient_player, result.get("channel", "local"), result.get("recipient_id", "")
                    ):
                        continue
                    try:
                        recipient.write(encoded)
                        await recipient.drain()
                    except (ConnectionError, OSError):
                        active_writers.discard(recipient)
            elif result.get("type") == "movement_snapshot":
                writer.write(encoded)
                await writer.drain()
                presence = (json.dumps(presence_snapshot(), separators=(",", ":")) + "\n").encode()
                for recipient in list(active_writers):
                    try:
                        recipient.write(presence)
                        await recipient.drain()
                    except (ConnectionError, OSError):
                        active_writers.discard(recipient)
            else:
                writer.write(encoded)
                await writer.drain()
    finally:
        active_writers.discard(writer)
        writer_players.pop(writer, None)
        if player is not None and not any(
            session_player == player.player_id
            for session_player in online_player_ids
            if session_player != player.player_id
        ):
            online_player_ids.discard(player.player_id)
        writer.close()
        try:
            await writer.wait_closed()
        except (ConnectionError, OSError):
            # The peer may already have closed its socket during shutdown.
            pass
