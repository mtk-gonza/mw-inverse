# MW Inverse

Reimplementación independiente y experimental de un MMORPG Unity estudiado de
forma autorizada. El proyecto no contiene código, assets, textos ni datos
propietarios del juego original.

## Estructura

- `client/`: cliente Godot.
- `server/`: contrato e implementación del servidor autoritativo.
- `docs/`: especificación derivada de observaciones y decisiones de diseño.
- `tools/`: herramientas locales de análisis y conversión, cuando sean necesarias.

## Primer objetivo

Construir un vertical slice offline/local:

`crear personaje -> entrar al mapa -> moverse -> combatir -> obtener objeto -> guardar`

Después se conectará a un servidor autoritativo.

## Estado

Fase 1: juego experimental ampliado y servidor autoritativo local completados.

El alcance cerrado del experimento está descrito en
`docs/experimental-complete.md`.

## MVP actual

- escena 3D y movimiento `WASD`;
- enemigo de entrenamiento y combate con `Espacio`;
- targeting local básico;
- botín e inventario;
- guardado local con `F5`/`F9`;
- login y snapshots por TCP/JSON;
- movimiento y combate validados por servidor;
- persistencia del servidor en SQLite;
- 45 pruebas automatizadas del servidor.

La matriz de trabajo y las limitaciones están en
`docs/reconstruction-matrix.md` y `docs/implementation-status.md`.
El plan maestro de finalización está en `docs/TODO-completo.md`.

## Motor local

Godot `4.7.2.stable` está instalado en:

`D:\projects\Godot_v4.7.2-stable_win64\Godot_v4.7.2-stable_win64.exe`

## Ejecución rápida

Desde PowerShell:

```powershell
.\scripts\run-dev.ps1
```

Para detener el servidor local:

```powershell
.\scripts\stop-dev.ps1
```

Validación completa local:

```powershell
.\scripts\check-all.ps1
```

Smoke test del cliente sin la biblioteca de referencia:

```powershell
.\scripts\smoke-clean.ps1
```

El servidor también dispone de `server/.env.example` y de un `docker-compose.yml`
opcional para persistencia local.
