# Matriz de reconstrucción

| Área | Evidencia REA | Estado del clon | Próxima ampliación |
|---|---|---|---|
| Movimiento/cámara | Controls, Entities | Implementado | colisiones y navegación avanzada |
| Targeting | Targeting | Implementado: selección por proximidad | perfil configurable y prioridades |
| Combate | Entities, CombatText, Blood | Implementado: daño, skills, guardia, feedback | estados, proyectiles y balance |
| PvP | Pvp | Implementado: opt-in persistente y daño autoritativo | sanciones, rankings y arenas |
| Nameplates | Nameplates.Core | Implementado: nombre/nivel/vida | party, guild, iconos y visibilidad |
| Exploración | Exploration | Implementado base: regiones, hunts de misión y shrines persistentes | rotaciones y tesoros avanzados |
| Decoración | HouseDecor.Core | Implementado base: piezas persistentes, colocación y retirada | draft, undo/redo y compra |
| Controles | Gameplay.Controls | Parcial: hotbar fija | configuración persistente de teclas |
| Conexión | Connection.Core | Parcial: reconexión básica TCP | estados de sesión y backoff |
| Comercio | LootFeed, Entities | Implementado: solicitudes, ofertas y commit | UI completa y auditoría económica |
| Clanes | Entities/feature model | Implementado: crear/unirse y persistencia | permisos, chat y guerras |
| IA | Entities | Implementado base: persecución autoritativa | navegación, aggro y habilidades |
| Sesiones | Connection.Core | Implementado: token de sesión compatible y validación opcional | TLS, refresh tokens y cuentas externas |
| Matchmaking | Pvp/Controls | Implementado base: cola de dos jugadores | arenas instanciadas y ranking |
| Cuentas | Connection.Core | Implementado: registro, PBKDF2, refresh token y MFA TOTP | proveedor externo y federación |
| Ranking | Pvp/Entities | Implementado: leaderboard local por nivel/kills/EXP | ranking distribuido y temporadas |
| Operación | Connection.Core | Implementado: configuración por entorno, migración SQLite, backup, métricas, TLS opcional y reconexión | métricas distribuidas y orquestación |
| Contenido | Exploration/Entities | Implementado: Bosque escarchado y enemigos wisp propios | campañas, bosses y mapas extensos |
| Referidos | Referral | Implementado base: código local estable | progreso social y recompensas propias |

La matriz no declara equivalencia total: sirve para medir trabajo pendiente sin
confundir el prototipo funcional con una reproducción completa.
