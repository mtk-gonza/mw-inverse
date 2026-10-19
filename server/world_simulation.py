"""Authoritative enemy respawn and simulation rules."""

import math
import time
from typing import Any


def respawn_enemies(enemy_health: dict[str, int], respawn_at: dict[str, float]) -> None:
    now = time.monotonic()
    for enemy_id, respawn_time in list(respawn_at.items()):
        if now < respawn_time:
            continue
        enemy_health[enemy_id] = (
            120 if enemy_id == "frost_guardian"
            else 45 if enemy_id.startswith("frost_wisp")
            else 30
        )
        respawn_at.pop(enemy_id, None)


def update_enemy_ai(
    player: Any,
    enemy_positions: dict[str, dict[str, float]],
    enemy_health: dict[str, int],
    slowed_until: dict[str, float],
    attack_at: dict[tuple[str, str], float],
    storage: Any,
) -> list[dict[str, Any]]:
    attacks: list[dict[str, Any]] = []
    now = time.monotonic()
    for enemy_id, position in enemy_positions.items():
        if enemy_health.get(enemy_id, 0) <= 0:
            continue
        dx = player.x - position["x"]
        dz = player.z - position["z"]
        distance = math.hypot(dx, dz)
        if 1.5 < distance < 12.0:
            speed_factor = 0.45 if slowed_until.get(enemy_id, 0.0) > now else 1.0
            step = min(0.12 * speed_factor, (distance - 1.5) / max(distance, 0.001))
            position["x"] += dx / distance * step
            position["z"] += dz / distance * step
        if distance <= 1.7:
            cooldown_key = (player.player_id, enemy_id)
            if attack_at.get(cooldown_key, 0.0) <= now and player.health > 0:
                base_damage = 10 if enemy_id == "frost_guardian" else 4
                damage = base_damage // 2 if player.guarded_until > now else base_damage
                player.health = max(0, player.health - max(1, damage))
                attack_at[cooldown_key] = now + (2.5 if enemy_id == "frost_guardian" else 1.8)
                attacks.append({"enemy_id": enemy_id, "damage": damage, "health": player.health})
    if attacks:
        storage.save(player.player_id, player.snapshot())
    return attacks
