# Estado de implementación

## Funcional y validado

- Cliente Godot 4.7.2 con escena 3D.
- Movimiento local y sincronizado.
- Servidor autoritativo TCP/JSON.
- Login de prototipo.
- Persistencia SQLite.
- Enemigos y combate server-side.
- Recompensas, inventario y equipamiento.
- Experiencia, niveles y misiones.
- Regiones y transiciones.
- NPCs y diálogos.
- Moneda y compra de objetos.
- Chat por región, grupo, clan, sistema y susurro privado.
- Grupos de jugadores.
- Presencia y avatares remotos interpolados.
- Validación de entradas inválidas.
- Versionado y normalización de partidas antiguas.
- Pruebas TCP reales de login, snapshots y chat.
- Ejecución automatizada con PowerShell.
- Skills de energía, guardia, consumibles y respawn.
- PvP opt-in, comercio entre jugadores y clanes básicos.
- IA autoritativa básica de persecución y sincronización de posiciones.
- Límite de tamaño de mensaje y rate limit de chat.
- Tokens de sesión y matchmaking local de arena.
- Cuentas locales con hash PBKDF2, refresh tokens y leaderboard.
- MFA TOTP local con activación y verificación.
- Migración SQLite v2, backup local y configuración de host/puerto por entorno.
- Reconexión automática con backoff y segunda región propia con enemigos.
- Auditoría estática REA de 13 módulos funcionales.
- Suite actual: 56 pruebas de servidor.
- Contrato de protocolo versionado y rechazo de versiones incompatibles.
- Sprites de referencia aplicados a HUD, hotbar y efectos; los sprites de
  interfaz no se fuerzan sobre entidades 3D sin confirmar su semántica.
- Efectos de combate y audio contextual conectados al flujo de habilidades.
- Idempotencia autoritativa para ataques, habilidades, consumo, compras, ventas y comercio.
- Ventanas de casteo, recuperación de ataques, línea de visión y obstáculos server-side.
- Bloqueo social persistente y filtrado de mensajes por jugador.
- Backups rotativos SQLite, journal de estados y restauración probada.
- Graceful shutdown, healthcheck y smoke test sin la biblioteca de referencia.
- Cooldowns de habilidades visibles y bloqueados localmente en la hotbar.
- TODO maestro de finalización en `docs/TODO-completo.md`.

## Estado del índice de conocimiento

- Proyecto: `mw-inverse`.
- Índice actualizado: 2026-10-19.
- Grafo: 702 nodos y 2.324 relaciones.
- Cobertura parcial conocida: `client/scripts/main.gd` y `scripts/check-all.ps1` tienen rangos con recuperación del parser.
- Se excluyen deliberadamente `reference-original`, `client/assets/reference-local`, datos SQLite locales y cachés.

## Pendiente para un juego completo

- Proveedores externos y cuentas distribuidas.
- Base de datos distribuida y migraciones multi-nodo.
- Mapas y assets originales propios.
- Animaciones, audio e interfaz final de producción.
- IA avanzada de enemigos.
- Estados avanzados, proyectiles y balance de combate.
- Misiones ramificadas y contenido.
- UI completa de comercio y economía avanzada.
- Permisos de clan, chat de clan y matchmaking.
- Instancias, raids y temporadas PvP.
- Proveedores externos y anti-abuso de producción.
- Escalado por zonas y despliegue dedicado.
- Backups distribuidos, observabilidad y recuperación ante fallos.

El proyecto actual es un juego experimental funcional con una matriz de
reconstrucción documentada, no una copia completa del juego original. La
equivalencia completa requeriría observación runtime, contenido propio extenso,
pruebas de carga y decisiones de diseño que no pueden inferirse solo desde DLLs.
