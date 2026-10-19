# Juego experimental — alcance completado

## Bucle jugable

```text
Iniciar cliente → conectar servidor → entrar al mundo
→ moverse → seleccionar objetivo → atacar
→ ver daño → derrotar enemigo → recoger botín
→ completar misión → ganar experiencia → subir de nivel
→ comprar/equipar objeto → hablar con NPC → usar chat/grupo
→ guardar estado → reconectar y restaurar partida
```

## Sistemas incluidos

- Cliente 3D Godot 4.7.2.
- Servidor autoritativo TCP/JSON.
- Persistencia SQLite.
- Regiones y snapshots de mundo.
- Jugadores remotos interpolados.
- Enemigos, vida, daño y recompensas.
- Selector de objetivos.
- Inventario, moneda y equipamiento.
- Experiencia y niveles.
- Misiones persistentes.
- NPCs y diálogos.
- Chat multiplayer.
- Grupos de jugadores.
- PvP opt-in con guardia y respawn.
- Comercio directo entre jugadores.
- Clanes básicos persistentes.
- Tokens de sesión y cola de matchmaking local.
- Cuentas locales, refresh tokens y clasificación.
- MFA TOTP local.
- Segunda región propia, enemigos adicionales y reconexión automática.
- Jefe propio de región, métricas, backup administrativo protegido y TLS opcional.
- IA autoritativa de persecución.
- Exploración con santuarios.
- Decoración persistente y códigos de referidos.
- HUD inspirado en la referencia.
- Cámara cenital/isométrica.
- Agua procedural, isla, árboles y efectos de combate.
- Guardado local y recuperación de estados antiguos.
- 34 pruebas automatizadas y pruebas TCP reales.

## Alcance fuera de este experimento

La equivalencia total con el original no se afirma: el MMO completo requiere contenido, IA, animaciones, audio, seguridad,
escalado, matchmaking, instancias y operación de producción. Esos elementos
están definidos como fases posteriores, no como fallos del vertical slice.
