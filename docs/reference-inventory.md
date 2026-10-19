# Inventario de referencia

El inventario se genera desde la copia local ignorada mediante:

```powershell
python tools/inventory_reference.py `
  "reference-original/Magic Wings_Data" `
  docs/reference-inventory.json
```

El manifiesto contiene rutas relativas, tamaños, extensiones y SHA-256. No
incluye el contenido de los recursos ni debe sustituir una licencia de uso.
