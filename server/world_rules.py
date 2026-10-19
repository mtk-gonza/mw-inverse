"""Geometry rules for the authoritative prototype world."""

import math
from collections.abc import Iterable

Obstacle = tuple[float, float, float]


def blocked_by_obstacle(
    obstacles: Iterable[Obstacle], x: float, z: float, radius: float = 0.55
) -> bool:
    return any(
        math.hypot(x - obstacle_x, z - obstacle_z) < obstacle_radius + radius
        for obstacle_x, obstacle_z, obstacle_radius in obstacles
    )


def has_line_of_sight(
    obstacles: Iterable[Obstacle],
    start_x: float,
    start_z: float,
    end_x: float,
    end_z: float,
) -> bool:
    distance = math.hypot(end_x - start_x, end_z - start_z)
    steps = max(1, int(distance / 0.35))
    for index in range(1, steps):
        ratio = index / steps
        if blocked_by_obstacle(
            obstacles,
            start_x + (end_x - start_x) * ratio,
            start_z + (end_z - start_z) * ratio,
            radius=0.0,
        ):
            return False
    return True
