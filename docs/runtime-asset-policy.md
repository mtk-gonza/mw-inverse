# Política de assets de runtime

La biblioteca de referencia completa no se carga entera en cada partida.

## Capas

1. `reference-original/extracted/unitypy/`: biblioteca completa de análisis,
   ignorada por Git y fuera de los builds.
2. `docs/reference-assets.json`: catálogo de la biblioteca completa.
3. `client/assets/reference-library/`: junction local de toda la biblioteca,
   accesible mediante `ReferenceAssetLibrary` con carga bajo demanda.
4. `client/assets/reference-local/`: selección local usada por la escena,
   también ignorada por Git.
5. `client/assets/`: recursos propios y reemplazables del clon.

El pack runtime se valida mediante:

```powershell
python tools/validate_reference_pack.py `
  client/assets/reference-local `
  client/assets/reference-local/manifest.json
```

La escena usa fallback procedural si el pack local no está presente.
