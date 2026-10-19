# Asset pack propio

Estos SVG son recursos originales creados para MW Inverse. No proceden del
juego de referencia ni contienen material extraído de él. Se pueden sustituir
por arte final manteniendo los mismos nombres y tamaños.

El pack incluye avatares, enemigos y efectos vectoriales propios. El script de
validación fuerza la importación headless antes del smoke test para que un clone
nuevo no dependa de artefactos locales de `.godot/imported`.

Estructura de producción:

- `sprites/characters/`: avatar del jugador.
- `sprites/enemies/`: enemigos de fuego y hielo.
- `sprites/effects/`: impactos y loot.
- `sprites/world/`: portales y santuarios.
- `ui/icons/`: iconos de hotbar e inventario.
- `ui/`: logo del cliente.

También incluye sprites propios para portales, santuarios y recompensas de
loot; se usan como capas billboard sobre la geometría 3D para mantener un
estilo consistente mientras se reemplazan por arte final.

Cuando se configura el override privado, esas capas se reemplazan en memoria
por las texturas locales que coincidan por nombre de archivo.
