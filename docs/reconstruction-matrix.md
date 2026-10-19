# Matriz de reconstrucción

| Área | Evidencia REA | Estado del clon | Próxima ampliación |
|---|---|---|---|
| Movimiento/cámara | Controls, Entities | Implementado: locomoción, cámara con bob y feedback visual | colisiones y navegación avanzada |
| Targeting | Targeting | Implementado: selección por proximidad, exclusiones y perfil serializable propio | conectar scorer al flujo completo y validar prioridades en runtime |
| Combate | Entities, CombatText, Blood | Implementado: daño, skills, guardia, proyectiles propios, sprites y feedback | estados y balance |
| PvP | Pvp | Implementado: opt-in, daño autoritativo, mark/skull y timeline temporal propios | validar sanciones, rankings y arenas en runtime |
| Nameplates | Nameplates.Core | Implementado: nombre/nivel/vida | party, guild, iconos y visibilidad |
| Exploración | Exploration | Implementado base: regiones, hunts de misión y shrines persistentes | rotaciones y tesoros avanzados |
| Decoración | HouseDecor.Core | Implementado base: piezas persistentes, colocación y retirada | draft, undo/redo y compra |
| Controles | Gameplay.Controls | Parcial: hotbar fija | configuración persistente de teclas |
| Conexión | Connection.Core | Implementado: estados TCP, sesión protegida, stalled y errores de protocolo | backoff/razones detalladas confirmadas en runtime |
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
