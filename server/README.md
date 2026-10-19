# Servidor autoritativo local

El servidor valida movimiento, combate, inventario, economía, chat, regiones,
sesiones y persistencia. El transporte TCP/JSON está separado en
`server/transport.py`, `server/session.py`, `server/auth.py`,
`server/combat.py`, `server/economy.py`, `server/social.py` y
`server/world_rules.py`, `server/world_simulation.py`, `server/progression.py`;
`server/main.py` conserva el
dispatcher y el contrato actual para mantener compatibilidad con el cliente y
las pruebas existentes.

## Ejecución local

Requiere Python 3.11+ y no utiliza paquetes externos:

```powershell
python server/main.py
```

Escucha por defecto en `127.0.0.1:24500`. Se puede configurar con
`MW_INVERSE_HOST`, `MW_INVERSE_PORT`, `MW_INVERSE_TLS_CERT` y
`MW_INVERSE_TLS_KEY`.

Los mensajes son objetos JSON delimitados por línea. Incluyen autenticación,
snapshots de mundo, movimiento, combate, habilidades, regiones, NPCs,
exploración, inventario, crafting, tienda, comercio, chat, grupos, clanes,
PvP, matchmaking, métricas, backups y guardado. El transporte limita cada
mensaje a 64 KiB y las solicitudes mutantes soportan `request_id`.

El estado se persiste en `server/data/mw_inverse.sqlite3`, que está excluido
del repositorio.

Pruebas del almacenamiento:

```powershell
python -m unittest discover -s server -p "test_*.py"
```
