# Auditoría de assets de referencia

## Resultado

Los contenedores `resources.assets`, `sharedassets*.assets`, `.resource` y
`.resS` fueron copiados únicamente a `reference-original/`, una carpeta local
ignorada por Git. Su inventario reproducible está en:

```text
docs/unity-container-audit.json
```

Se puede regenerar con:

```powershell
python tools/audit_unity_containers.py `
  "reference-original/Magic Wings_Data" `
  docs/unity-container-audit.json
```

El inventario registra tamaño, SHA-256, cabecera reconocida, posible stream
`.resS` asociado y si se extrajo el contenido.

## Limitación REA

REA inspeccionó las DLL administradas y sus sistemas de consumo, pero rechazó
`resources.assets` como formato binario no soportado por su proveedor actual.
Por tanto no se afirma que REA haya enumerado texturas, meshes o clips dentro
de esos contenedores. No se extraen ni se incorporan al clon.

El cliente usa un pack visual propio en `client/assets/` y geometría procedural
para mantener separados el experimento de reconstrucción y los recursos de
referencia.

## Datos recuperables sin extractor

También se genera un índice de cadenas legibles —nombres y rutas candidatas,
no texturas ni meshes— mediante:

```powershell
python tools/index_unity_strings.py `
  "reference-original/Magic Wings_Data" `
  reference-original/extracted/unity-string-index.json
```

Ese índice permanece dentro de la carpeta ignorada de referencia.

## Extracción habilitada

Se instalaron `UnityPy 1.25.4` y `Pillow 13.0.0`. El extractor propio:

```powershell
python tools/extract_unity_assets.py `
  "reference-original/Magic Wings_Data" `
  reference-original/extracted/unitypy
```

Exporta cuando UnityPy puede decodificar el objeto:

- `Texture2D` y `Sprite` como PNG;
- `AudioClip` en el formato exportable disponible;
- `Mesh` en el formato exportable disponible.

Los objetos no soportados quedan registrados en `extraction-report.json` y no
se modifican los contenedores fuente.

Para audio se incluye una pasada especializada:

```powershell
python tools/extract_unity_audio.py `
  "reference-original/Magic Wings_Data" `
  reference-original/extracted/unitypy
```

Los `Mesh` ahora se exportan a OBJ mediante la API de UnityPy:

```powershell
python tools/extract_unity_meshes.py `
  "reference-original/Magic Wings_Data" `
  reference-original/extracted/unitypy
```

El resultado se registra en `mesh-extraction-report.json`. Los OBJ son una
conversión técnica para reconstrucción independiente; no se incorporan al
cliente automáticamente sin revisión de materiales, escala y semántica.

También se genera una relación de escenas y componentes:

```powershell
python tools/inventory_unity_scene_objects.py `
  "reference-original/Magic Wings_Data" `
  docs/unity-scene-inventory.json
```

AssetRipper 2.0.0 fue probado en modo headless, pero rechazó esta copia con
`game structure processor could not find any valid assets`; por eso la ruta
reproducible actual usa UnityPy para objetos compatibles y parsers propios para
OBJ. Esto deja explícitamente pendientes los prefabs, escenas y animaciones
que no están representados como recursos exportables independientes.
