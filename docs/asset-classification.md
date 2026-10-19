# Clasificación exhaustiva de assets

Se clasifica cada recurso extraído por nombre, extensión y dimensiones cuando
es una imagen. La clasificación no sustituye una revisión humana: los
recursos con nombres genéricos quedan en `unknown`.

```powershell
python tools/classify_extracted_assets.py `
  reference-original/extracted/unitypy `
  docs/extracted-assets.json
```

Galerías de revisión visual:

```text
docs/asset-galleries/
```

Categorías visuales: `map`, `hud`, `combat`, `character`, `progression`,
`effects` y `unknown`. El audio se separa en `audio_music`, `audio_ui`,
`audio_creature`, `audio_combat`, `audio_environment` y `unknown` según el
nombre semántico. Los assets se cargan bajo demanda mediante
`ReferenceAssetLibrary`; no se asignan por posición ni por orden de archivo.

## Uso dentro del cliente

La tecla `F8` abre el visor integrado de la biblioteca. Permite recorrer todos
los recursos clasificados, incluidos los 2.520 `unknown`, visualizar cada PNG y
reproducir cada WAV individualmente. El índice se carga al iniciar, pero el
contenido multimedia se carga únicamente al seleccionar un recurso. `F12`
conserva la acción de exploración de red.
