# Asset slots reemplazables

Estas rutas son el contrato visual estable del clon. Para reemplazar el arte
no hay que modificar scripts: basta con colocar un archivo con el nombre
indicado y ejecutar la importación de Godot.

```text
slots/characters/player_avatar.png
slots/characters/npc_mentor_arin.png
slots/characters/npc_quartermaster_lynn.png
slots/characters/npc_warden_sela.png
slots/enemies/enemy_fire.png
slots/enemies/enemy_frost.png
slots/effects/target_ring.png
slots/effects/hit_spark.png
slots/effects/spell_effect.png
slots/effects/spell_projectile.png
slots/effects/attack_projectile.png
slots/effects/guard_effect.png
slots/world/loot.png
slots/world/portal.png
slots/world/shrine.png
```

Los slots son opcionales. Si faltan, el cliente usa primero el override local
configurado y luego los fallbacks vectoriales del clon.
