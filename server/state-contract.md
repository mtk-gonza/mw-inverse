# Estado compartido

El servidor no dependerá de `Node3D`, escenas ni scripts visuales. El estado
serializable mínimo de un jugador es:

```json
{
  "state_version": 1,
  "player_id": "player-001",
  "position": {"x": 0, "y": 1.1, "z": 0},
  "health": 100,
  "max_health": 100,
  "level": 1,
  "experience": 0,
  "attack": 10,
  "currency": 100,
  "equipment": {},
  "region_id": "training_meadow",
  "party_id": "",
  "quests": {"training_hunt": {"progress": 0, "completed": false}},
  "inventory": {"monster_core": 1}
}
```

El cliente puede predecir movimiento y mostrar UI, pero el servidor debe
validar posición, vida, inventario y recompensas antes de emitir un snapshot.
