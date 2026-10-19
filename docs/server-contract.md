# Contrato cliente-servidor

El servidor será autoritativo. El cliente enviará intenciones y el servidor
responderá con eventos confirmados.

## Transporte

La conexión usa TCP con objetos JSON delimitados por línea. La versión vigente
es `protocol_version = 1`; las versiones incompatibles se rechazan. El límite
de tamaño de mensaje es 64 KiB.

## Familias de mensajes

```text
| Área | Solicitudes principales | Eventos/respuestas |
|---|---|---|
| Sesión | `login_request`, `auth_login`, `auth_refresh`, MFA | `login_result`, `auth_result` |
| Mundo | `world_snapshot`, `move_intent`, `world_tick`, regiones | snapshots y `region_event` |
| Combate | `attack_request`, `skill_request`, `pvp_attack`, `respawn_request` | `combat_event`, `skill_event`, `pvp_event` |
| Progresión | `consume_request`, `craft_request`, `equip_request`, `buy_request`, `sell_request` | item, crafting, equipment y shop events |
| Social | chat, bloqueo, grupos, clanes, comercio | chat, social, party, clan y trade events |
| Operación | `health_request`, `metrics_request`, `backup_request`, `save_request`, `journal_request` | health, metrics, backup, save y journal events |
```

El cliente nunca decide por sí mismo daño, recompensas, inventario, moneda o
posición final. Las solicitudes mutantes aceptan `request_id` y el servidor
deduplica el resultado por jugador.
