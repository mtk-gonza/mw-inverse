# Servidor

El servidor será autoritativo: el cliente solicitará acciones y el servidor
validará movimiento, combate, inventario y persistencia.

Durante el primer vertical slice se usará una sesión local. La implementación
de red se añadirá después de fijar el modelo de dominio y los mensajes.

## Prototipo local

Requiere Python 3.11+ y no utiliza paquetes externos:

```powershell
python server/main.py
```

Escucha únicamente en `127.0.0.1:24500`. Acepta mensajes JSON delimitados por
línea para `login_request`, `world_snapshot`, `move_intent`,
`grant_test_item` y `save_request`.

`world_snapshot` también devuelve el estado de los enemigos de la región.
El mensaje `chat_message` normaliza y limita mensajes a 200 caracteres antes
de emitir un `chat_event`.

El estado se persiste en `server/data/mw_inverse.sqlite3`, que está excluido
del repositorio.

Pruebas del almacenamiento:

```powershell
python -m unittest discover -s server -p "test_*.py"
```
