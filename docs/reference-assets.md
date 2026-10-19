# Biblioteca local de referencia

La extracción completa se conserva fuera del cliente en:

```text
reference-original/extracted/unitypy/
```

El catálogo reproducible está en:

```text
docs/reference-assets.json
```

Se genera con:

```powershell
python tools/build_reference_catalog.py `
  reference-original/extracted/unitypy `
  docs/reference-assets.json
```

El cliente solo usa una selección pequeña y explícita en:

```text
client/assets/reference-local/
```

La carga es opcional: si esa carpeta no existe, el cliente conserva el arte
procedural propio y arranca sin errores. `F11` alterna la música local de
referencia y los botones reproducen un efecto de interfaz cuando el audio está
disponible.
