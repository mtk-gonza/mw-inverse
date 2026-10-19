"""Authoritative progression and local matchmaking rules."""

from typing import Any


def advance_after_defeat(player: Any, target_id: str, quests: dict[str, dict]) -> bool:
    previous_level = player.level
    player.kills += 1
    player.experience += 25
    for quest_id, quest in quests.items():
        progress = player.quests.setdefault(quest_id, {"progress": 0, "completed": False})
        if not progress["completed"] and target_id.startswith(quest["target"]):
            progress["progress"] = min(quest["goal"], int(progress["progress"]) + 1)
            if progress["progress"] >= quest["goal"]:
                progress["completed"] = True
                player.experience += quest["experience_reward"]
    while player.experience >= player.level * 100:
        player.experience -= player.level * 100
        player.level += 1
        player.max_health += 10
        player.health = player.max_health
        player.attack += 2
    return player.level > previous_level


def try_create_match(queue: list[str], matches: dict[str, set[str]], counter: int) -> tuple[str, int]:
    if len(queue) < 2:
        return "", counter
    first = queue.pop(0)
    second = queue.pop(0)
    counter += 1
    match_id = f"arena-{counter}"
    matches[match_id] = {first, second}
    return match_id, counter
