# TODO de gaps REA — comparación referencia/clon

Este backlog convierte observaciones REA en trabajo verificable. Una diferencia
estática no se implementa automáticamente: primero se confirma si afecta al
comportamiento del clon y se conserva la separación entre código propio y la
referencia.

## P0 — cerrar evidencia y contratos

- [x] Fijar la ruta y la identidad SHA-256/MVID del build actual.
- [x] Inspeccionar assemblies prioritarios y miembros managed.
- [x] Crear matriz comparativa inicial en `docs/rea-comparison.md`.
- [x] Limitar `CombatAwareness` local a 128 impactos por objetivo.
- [ ] Ejecutar una pasada runtime controlada sobre login, conexión, targeting,
      transición de región, combate y PvP.
- [ ] Registrar cada observación runtime con Evidence y separar hecho,
      inferencia e incógnita.

## P1 — targeting y combate

- [x] Completar `TargetingProfile` propio: radio, criterios, prioridades,
      exclusiones y modo de cambio.
- [x] Persistir/importar perfiles JSON propios sin copiar strings ni datos.
- [ ] Usar el mismo scorer para hint local y solicitud al servidor.
- [ ] Confirmar runtime de `CombatAwareness` antes de replicar reglas temporales.
- [x] Modelar estados PvP propios: skull/mark, duración y timeline.
- [ ] Confirmar las ventanas de 60 s, 1 h y 1 día observadas en CIL mediante
      runtime antes de convertirlas en balance.
- [ ] Añadir pruebas deterministas para rango, prioridad, exclusión y estados.

## P1 — conexión y sesiones

- [x] Implementar una máquina de estados propia: connecting, connected,
      protected, reconnecting, stalled, refused, protocol_error y closed.
- [x] Exponer razón/código de desconexión en HUD.
- [x] Añadir generación de sesión y versión de solicitud para exploración.
- [x] Exponer estados `connecting`, `connected`, `reconnecting` y `closed` en
      el cliente TCP.
- [x] Exponer estados `protected`, `stalled` y `protocol_error` en el cliente.
- [ ] Probar reconexión durante combate, comercio y transición de región.

## P2 — exploración y contenido

- [ ] Implementar snapshots propios de shrines, seeds y hunts con estado
      loading/completed/error.
- [x] Rechazar snapshots obsoletos por `session_generation` y `request_version`.
- [ ] Crear modelo propio de regiones resueltas con collections separadas.
- [ ] Diseñar rotaciones de tesoros propias solo después de confirmar runtime.
- [ ] Añadir seeds, hunts y recompensas con datos propios.

## P2 — comparación visual/entidades

- [x] Auditar entidades visuales, nameplates, misiles, efectos y locomoción.
- [x] Añadir sprites vectoriales originales para avatar, enemigos y golpes.
- [x] Añadir animación procedural de idle, movimiento, ataque, impacto y vuelo
      visual de enemigos.
- [x] Añadir muerte animada, chispas de impacto, cámara con bob y NPCs con
      idle visual.
- [x] Añadir sprites propios para portales, santuarios y recompensas de loot.
- [x] Sustituir iconos de hotbar por el set vectorial propio del clon.
- [x] Añadir puente privado para resolver texturas autorizadas fuera del
      repositorio mediante `MW_INVERSE_REFERENCE_ROOT` o `user://`.
- [x] Añadir slots privados para avatar, enemigos, NPCs, targeting, efectos,
      portales, santuarios y loot.
- [x] Organizar los assets del clon en carpetas de producción bajo
      `client/assets/sprites` y `client/assets/ui`.
- [x] Crear slots estables para reemplazar sprites y efectos sin modificar
      código ni escenas.
- [x] Mantener equivalentes propios; no copiar prefabs, modelos, textos ni
      código recuperado.
- [ ] Validar semántica de cada asset antes de usarlo en una entidad 3D.

## Criterios de aceptación

- Cada gap implementado tiene una prueba o smoke test.
- El servidor sigue siendo autoritativo para estado, daño, loot e inventario.
- El cliente puede arrancar sin la referencia local.
- La matriz y este TODO se actualizan junto con cada cambio.
