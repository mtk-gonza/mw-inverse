# Alcance de investigación

## Artefacto de referencia

`D:\Juegos\MagicWings2\current`

La instalación observada contiene un juego Unity con ensamblados administrados
en `Magic Wings_Data/Managed/` y BepInEx instalado. Esto sugiere una primera
fase de análisis centrada en las DLL administradas, sin modificar los originales.

## Módulos prioritarios

1. `Assembly-CSharp.dll`
2. `MagicWings.Entities.dll`
3. `MagicWings.Gameplay.Combat.Pvp.dll`
4. `MagicWings.Gameplay.Combat.Targeting.dll`
5. `MagicWings.Features.Exploration.dll`
6. `MagicWings.App.Connection.Core.dll`

## Límites

- El clon tendrá implementación y recursos propios.
- No se copiarán DLLs, assets, textos, música, mapas ni datos propietarios.
- El servidor original no se tratará como una dependencia.
- Las observaciones se registrarán como hechos, inferencias o incógnitas.

## Primera evidencia estática

### `Assembly-CSharp.dll`

- Es un PE/CLI x86 con implementación CIL y familia de runtime `unity-mono`.
- Tamaño observado: 7.764.480 bytes.
- Metadata completa en esta inspección: 5.499 tipos, 37.668 métodos y 39.511 campos.
- SHA-256: `e9894464f0551b307f26c26dcafa89e8e49c282b4e715527b37404ae34abf04e`.
- Evidencia REA: `ev_eac7b641d5a149f2b11aba4245be7c86da964eeda3e0effcd2d8dbcecf714ac5`.

La inspección de miembros de esta DLL excedió el presupuesto de representación
de REA; se continuará por módulos pequeños y tipos seleccionados.

### Módulos pequeños prioritarios

| Módulo | Tipos | Métodos | Aristas de llamadas |
|---|---:|---:|---:|
| `MagicWings.Entities.dll` | 128 | 845 | 4.414 |
| `MagicWings.Gameplay.Combat.Pvp.dll` | 11 | 9 | 42 |
| `MagicWings.Gameplay.Combat.Targeting.dll` | 27 | 119 | 572 |
| `MagicWings.Features.Exploration.dll` | 30 | 228 | 560 |
| `MagicWings.App.Connection.Core.dll` | 12 | 23 | 109 |

Estos conteos son observaciones de metadata, no una descripción completa del
comportamiento en ejecución.

### `ClientModule.dll`

La inspección no encontró un transporte de red principal. El módulo se centra
en presentación y datos visuales: `AppearanceTypeData`, elevación, orden de
renderizado y componentes de fluidos, objetos colgables y salpicaduras. También
expone estados visuales, animaciones y propiedades de objetos como bloqueos de
paso, velocidad del suelo, escritura, iluminación y automapa.

- 41 tipos y 191 métodos.
- SHA-256: `348d6046ae99dbeecfd45c6455b55dd896c6aebccfc899732810be9dad51ba68`.
- Evidencia REA: `ev_8f476c4b85e2cbcd5305aa13f19b7ce70be208b446d0f066076ca8b66ff2466f`.

Esto refuerza la separación del clon entre estado de juego y presentación:
los atributos visuales no deben entrar en la autoridad del servidor.
