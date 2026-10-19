# Override privado de assets de referencia

El cliente puede usar assets locales de una instalación autorizada sin copiar
ningún archivo al repositorio. El puente está en
`client/scripts/reference_override.gd`.

## Extracción local

Para generar la carpeta privada desde la instalación indicada:

```powershell
uv run --with UnityPy python tools\extract_reference_assets.py
```

El destino es:

```text
client/assets/reference-private/
```

Ese directorio está excluido de Git mediante `.gitignore` y contiene un
`manifest.json` con los nombres y tipos extraídos.

Después de la extracción, el cliente lo selecciona automáticamente y usa estos
slots iniciales:

| Slot | Asset extraído |
|---|---|
| `player_avatar` | `player.png` |
| `enemy_fire` / `enemy_frost` | `monster.png` |
| `target_ring` | `AutoTargetRing.png` |
| `spell_effect` / `spell_projectile` | `defaultspells.png` |
| `attack_projectile` | `autoattack_nearest.png` |
| `guard_effect` | `shieldAndHeal.png` |
| `loot` | `batwing.png` |
| `portal` | `destination.png` |
| `shrine` | `shrine.png` |

Estos mapeos son defaults reemplazables: se pueden cambiar luego sin tocar la
lógica del juego.

Configurar una sola vez:

```json
{
  "root": "C:/ruta/a/tu/exportacion/local/de/assets",
  "slots": {
    "player_avatar": "player.png",
    "enemy_fire": "enemy_fire.png",
    "enemy_frost": "enemy_frost.png",
    "spell_effect": "spell_effect.png",
    "attack_projectile": "attack.png",
    "guard_effect": "shield.png"
  }
}
```

Guardar como:

```text
user://mw_inverse_reference_override.json
```

También se puede establecer la variable de entorno:

```text
MW_INVERSE_REFERENCE_ROOT=C:/ruta/a/tu/exportacion/local/de/assets
```

El valor por defecto apunta a la instalación local indicada para la
investigación. Si esa instalación contiene bundles y no archivos de imagen
sueltos, primero hay que exportar los assets con una herramienta autorizada;
el clon no extrae ni redistribuye contenido automáticamente.

Orden de resolución:

1. archivo local privado encontrado por nombre;
2. asset de comparación ya existente en `res://assets/reference-local`;
3. fallback vectorial original del clon.

La búsqueda privada se hace por nombre de archivo, por lo que también funciona
si una exportación autorizada conserva otra estructura de carpetas.

Los slots permiten mapear nombres lógicos del clon a los nombres reales de la
exportación privada sin modificar ninguna escena ni copiar recursos.

## Reemplazo futuro sin tocar código

Para sustituir el arte más adelante, usar las rutas estables de:

```text
client/assets/slots/
```

El cliente prioriza esos archivos del proyecto. Si no existen, usa el override
privado y finalmente los fallbacks propios. De esta forma el reemplazo final
consiste en sustituir archivos en `slots/`, sin cambiar scripts ni escenas.

Los archivos privados quedan fuera de Git y del paquete del proyecto.
