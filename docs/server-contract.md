# Contrato inicial cliente-servidor

El servidor será autoritativo. El cliente enviará intenciones y el servidor
responderá con eventos confirmados.

## Mensajes iniciales

```text
client -> server: login_request
server -> client: login_result
client -> server: enter_world_request
server -> client: world_snapshot
client -> server: move_intent
server -> client: movement_snapshot
client -> server: target_request
server -> client: target_result
client -> server: attack_request
server -> client: combat_event
server -> client: inventory_event
server -> client: save_ack
```

El cliente nunca decide por sí mismo daño, recompensas, inventario, moneda o
posición final. El contrato se ampliará después de observar más sistemas.
