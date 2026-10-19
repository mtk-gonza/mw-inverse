# Especificación inicial de sistemas

| Sistema | Estado actual | Próxima ampliación |
|---|---|---|
| Cliente Godot | 3D, cámara cenital y HUD funcional | loading, controles configurables y pulido |
| Servidor autoritativo | TCP/JSON, autoridad de estado y transporte separado | módulos de dominio y persistencia |
| Login | cuentas locales, PBKDF2, refresh tokens y MFA TOTP | proveedor externo |
| Personajes | atributos, nivel, equipo, energía y progresión | clases y estadísticas derivadas |
| Movimiento | validación de límites, obstáculos y región | predicción y reconciliación |
| Combate | tiempo real, skills, guardia, PvP y loot | estados, balance y telegráficos |
| Inventario | objetos, consumibles, equipo, compra, venta y crafting | slots, peso y economía avanzada |
| Misiones | progreso persistente y recompensas | ramas y elecciones |
| Persistencia | SQLite, migración, journal y backups | locks y despliegue distribuido |
| Red | snapshots, tokens, rate limits y reconexión | TLS probado y carga multicliente |

## Primer modelo de dominio observado

El módulo `MagicWings.Gameplay.Combat.Pvp.dll` contiene tipos explícitos para:

- `PvpStatusSnapshot`;
- `PvpSkull` y `PvpMark`;
- `PvpTimeLine` y `PvpTimeRow`;
- `PvpDuration` y `PvpDurationKind`;
- `PvpStatusView` y `PvpStatusModel`.

`PvpStatusModel` expone operaciones `Build`, `Mark` y `Split`. Esto sugiere que
el PvP mantiene un estado calculado, marcas y segmentos temporales. Es una
hipótesis de diseño para nuestro clon, no una afirmación sobre las reglas
completas del juego.

Evidencia REA: `ev_7669ab10db7689279ff5337a0cbc35f2e412232afa59220fc5f4b0c6331bb1c7`.

La primera lectura de `MagicWings.Entities.dll` está dominada por presentación
y entidades visuales: `OutfitController`, `MountController`, `SkinController`,
`MissileController`, `EffectController`, `AddonController` y tipos de
locomoción. Por ello no se debe asumir que esta DLL contiene el modelo completo
de jugador o inventario; esos sistemas probablemente están en otros módulos.

Evidencia REA: `ev_ac6b5241e0d5646fd725488e3d0ba6a82d4e0cd3e1626167c480c193fde379c`.

## Selección de objetivos

`MagicWings.Gameplay.Combat.Targeting.dll` define un sistema bastante
independiente del renderizado:

- `CombatAwareness` registra impactos por identificador, atacante y momento.
- `ICombatRelations` distingue jugador local, líder, miembros del grupo y
  atacantes externos.
- `TargetCandidate`, `TargetExclusion`, `TargetingContext` y `RankedTarget`
  forman el modelo de candidatos.
- `TargetScorer` implementa búsqueda por radio, filtrado, puntuación,
  ordenamiento y explicación del motivo de selección.
- `TargetingProfile` mantiene criterios, marcas, cadenas y orden de objetivos.
- `TargetingProfileJson` indica que el perfil puede serializarse a JSON.
- `HoldToConfigureGesture` y `ProtectionPauseHold` modelan interacción y
  pausa/reconexión durante la selección.

Esto permite iniciar en el clon un sistema de targeting con autoridad del
servidor: el cliente puede sugerir el objetivo, pero el servidor valida rango,
relaciones y disponibilidad.

Evidencia REA: `ev_ee1a7ce7071b71a000e2453575d59a5122fdb3acc7e391e5695c5ba3c82603cf`.

## Estado de conexión

`MagicWings.App.Connection.Core.dll` no parece ser el transporte de red en sí,
sino una capa de estado, mensajes de interfaz y políticas de desconexión. Se
observaron:

- `ConnectionStep`, `ConnectionLadder` y `LadderInput`;
- `ConnectionWire` para interpretar avisos de finalización y protección;
- `SilenceReconnectRule` y `ProtectionDisplayRule`;
- `DisconnectReasons`, `DisconnectReasonInfo`, `ReasonGroup` y `EndPolicy`;
- tokens de estado como `unresponsive`, `stalled`, `reconnecting`, `network_changed`,
  `maintenance`, `antibot`, `login_refused`, `protocol_error`, `rate_limit` y
  `admin_kick`.

También existe una salida JSON de UI y códigos `MW-NET-*`, `MW-SRV-*` y
`MW-CLI-*`. No constituye todavía el protocolo completo del servidor, pero sí
justifica diseñar una máquina de estados de conexión explícita en nuestro clon.

Evidencia REA: `ev_3bf4287455cdc72ea33c094ef36227812ae939b6c96438bd0d7da49b0adcb117`.

## Exploración y regiones

`MagicWings.Features.Exploration.dll` muestra un sistema de datos por sesión,
región y colecciones cargadas de forma versionada:

- `ExplorationPosition` representa posiciones de exploración.
- `ExplorationRegionDescriptor`, `ExplorationRegionResolver` y
  `ExplorationResolvedRegion` resuelven regiones y agrupan datos.
- Hay colecciones separadas para santuarios, semillas y cacerías.
- `ExplorationDataStore` usa sesiones, generaciones y versiones de petición para
  aceptar o descartar resultados de carga antiguos.
- `ExplorationSessionModel` expone el estado activo y snapshots de esas
  colecciones.
- `TreasureRotationData` y `TreasureRotationRegion` contienen rotaciones,
  niveles, puntos, regiones bloqueadas, recompensas y límites semanales.

Para el clon implementaremos primero un `WorldState` con regiones y una sesión
local; la sincronización de regiones se moverá luego al servidor autoritativo.

Evidencia REA: `ev_d578f186064fc960b359dd27f89351c9026de3a9f9352026ce03f7164dbdc5e3`.
