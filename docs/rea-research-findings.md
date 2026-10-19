# Auditoría REA de la referencia local

Esta auditoría usa únicamente la copia local de referencia y observa metadata,
firmas, CIL, literales y bordes estáticos. No afirma que el análisis estático
haya ejecutado el juego ni que reproduzca su protocolo de red.

## Evidencia principal

| Módulo | Resultado observado | Evidence |
|---|---|---|
| `Assembly-CSharp.dll` | PE/CLI Unity Mono, 5.499 tipos, 37.668 métodos en metadata; el inventario de miembros completo excede el presupuesto de representación | `ev_19cfec43a52f256caf9c2eaaf4893657e398494edd6de5ec1e3d7249e8030e21` |
| `MagicWings.Entities.dll` | outfits, mounts, misiles, efectos y controladores de entidades; 128 tipos, 845 métodos | `ev_47bd85d2d29b3a1073f255ba3601cb143ad0751bf46e70698aca413dcafbf7f2` |
| `MagicWings.Gameplay.Combat.Targeting.dll` | awareness de combate, relaciones de grupo, scoring, radios, criterios, marcas y perfiles JSON | `ev_c6bd942d6a7409117d02b857e3638df73adfe2d0c91dc6731fbbbc39d5222248` |
| `MagicWings.Gameplay.Combat.Pvp.dll` | snapshot, skull/mark, timeline y duración de estado PvP | `ev_bbdf073dff06ab3acba82631beb5e6086cc6b57f47b0a49247b594d52bed716c` |
| `MagicWings.Features.Exploration.dll` | sesiones, shrines, seeds, hunts, cargas versionadas y rotación de tesoros | `ev_ecfb93ec03fe8fd9cd0b798170bce5aa8cf89a2e24fa16493815eb349920c362` |
| `MagicWings.Features.HouseDecor.Core.dll` | draft de decoración, colocación, movimiento, rotación, undo/redo y carrito | `ev_f58e8cb1857568a19f6f967e61a2618cc18e4c506399698c019b515515073d4f` |
| `MagicWings.Features.CombatText.dll` | eventos de números de combate, relación, estilos, colores y anclajes | `ev_c743a702e6afc1395cbbba6d12abe2c7169e0978a2cd735b153f8d005df0355b` |
| `MagicWings.Features.Blood.dll` | perfiles, impactos, muertes, calidades y director de decals | `ev_b1a6572a7c9226c5e2054eb362655bb2dc2fc876892d97ba259562b27b49b71a` |
| `MagicWings.Features.LootFeed.dll` | filas y modelo de feed de botín | `ev_885123c2c0d7c117a0a5e9e911c2e6463a6cf8b2ac593f7530c8b9d3855ef20e` |
| `MagicWings.Presentation.Nameplates.Core.dll` | layout, vitals, party/guild, iconos, visibilidad y paleta de nameplates | `ev_184d01bd51a01a86a544637581fd21d0af8bd827d21481164ee2c94cedf71f00` |
| `MagicWings.Gameplay.Controls.dll` | chords, hotkeys, aim de suelo, modos de casteo, presets y sincronización de controles | `ev_ee3d4d5a73b24901721301290d4372ff1afab3a1b5071ddbe793d387355cbc4a` |
| `MagicWings.App.Connection.Core.dll` | ladder de conexión, reconexión, protección y razones de desconexión | `ev_77a825fdb44fd267a5dacafa3049467f935bc20dc4a80c9bc66dd0a7e2be0642` |

## Decisiones de reconstrucción

El clon implementa equivalentes propios de targeting, nameplates, combate
visual, hotbar, energía, habilidades, guardia, consumibles, respawn,
persistencia y PvP opt-in. No copia código, strings de interfaz, assets ni
datos internos de la referencia. Los sistemas que requieren observación de
runtime o servidor real permanecen explícitamente como hipótesis de diseño.
