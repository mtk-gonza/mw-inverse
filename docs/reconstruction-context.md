# Contexto de reconstrucción

## Estado actual

`mw-inverse` es un clon independiente experimental con cliente Godot 4.7.2 y
servidor autoritativo Python asyncio sobre TCP/JSON. La persistencia usa SQLite.
La referencia original permanece separada y no es una dependencia distribuible.

## Validación más reciente

- 56 pruebas del servidor pasan.
- `scripts/check-all.ps1` pasa.
- `scripts/smoke-clean.ps1` arranca el cliente sin la biblioteca de referencia.

## Decisiones vigentes

- El servidor es la autoridad para movimiento, combate, inventario, moneda,
  comercio, chat y sesiones.
- Las solicitudes mutantes aceptan `request_id` y se deduplican por jugador.
- Los recursos recuperados se usan bajo demanda; fallbacks propios mantienen el
  cliente ejecutable sin ellos.
- `reference-original/`, junctions, credenciales, SQLite local y cachés no se
  incluyen en el cliente distribuible.

## Índice de código

- Proyecto codebase-memory: `mw-inverse`.
- Última reindexación: 2026-10-19.
- 702 nodos y 2.324 relaciones.
- Exclusiones intencionadas: `reference-original`, `client/assets/reference-local`,
  `server/data`, `__pycache__` y `.godot`.
- Hay recuperación parcial conocida en rangos de `client/scripts/main.gd` y
  `scripts/check-all.ps1`; no usar el grafo como única evidencia en esos rangos.

## Limitaciones abiertas

Todavía faltan contenido propio de producción, animaciones completas, instancias
cooperativas, economía avanzada, carga multicliente, export Windows reproducible
y observación runtime del ejecutable original.

## Comandos de regresión

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check-all.ps1
powershell -ExecutionPolicy Bypass -File scripts\smoke-clean.ps1
```
