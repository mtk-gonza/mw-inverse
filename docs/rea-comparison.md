# Comparativa REA — referencia vs. MW Inverse

## Alcance de esta pasada

Referencia seleccionada:

```text
C:\Users\gonzalo.gonzalez\AppData\Local\MagicWingsBOTeado\current
```

Se inspeccionaron estáticamente los assemblies prioritarios y sus miembros
managed. Esto establece inventario, firmas, CIL y aristas estáticas; no prueba
reglas runtime, servidor real, balance ni flujo de red.

## Identidad del build

| Assembly | SHA-256 | MVID | Metadata |
|---|---|---|---:|
| `Assembly-CSharp.dll` | `e9894464f0551b307f26c26dcafa89e8e49c282b4e715527b37404ae34abf04e` | `8b2e122c-59c0-49e1-a103-895aad1629f6` | 5.499 tipos / 37.668 métodos |
| `MagicWings.Entities.dll` | `c6564118611405025d45abfd69acf3fe24b9dee201173de2939a25ef788f976a` | `0422e4c4-0578-42e7-ab22-267bf27efa90` | 128 tipos / 845 métodos |
| `MagicWings.Gameplay.Combat.Targeting.dll` | `5b4a2d15da03df25e0bd14e3dfbf9c87a1a8a9cb0f578c93cdac7aa7aeef1c59` | `ed3cd74a-2d4d-4894-8afb-f5f58ffee929` | 27 tipos / 119 métodos |
| `MagicWings.Gameplay.Combat.Pvp.dll` | `8df4503544dd872ef35c4e822f3321750473dd566611bae209717abc0ae87dc3` | `a80c03d1-adb8-40ff-b874-93abab4ce2ed` | 11 tipos / 9 métodos |
| `MagicWings.Features.Exploration.dll` | `56cf9817cf58de4ca2abea5a99156a9680995c12b3e85aaa75db53ca52fd3479` | `018dbbed-072b-433d-a0a1-3ef3e33291c0` | 30 tipos / 228 métodos |
| `MagicWings.App.Connection.Core.dll` | `3610a6bcba1440120162626aa2e2d8a2c28946d02272e186f7f7f976912a7351` | `fb196685-b0ee-4ff7-af08-f8fc15a4c1cd` | 12 tipos / 23 métodos |

## Matriz 1:1 inicial

| Sistema | Observado en referencia | Estado actual del clon | Diferencia prioritaria |
|---|---|---|---|
| Targeting | `TargetCandidate`, `TargetExclusion`, `TargetingContext`, `RankedTarget`, `TargetScorer`, criterios, radios, perfiles JSON y `CombatAwareness` con memoria temporal | Selección local/proximidad y validación server-side básica | Implementar perfil configurable, exclusiones, prioridades y memoria de impactos |
| PvP | `PvpStatusSnapshot`, `PvpSkull`, `PvpMark`, `PvpTimeLine`, `PvpDuration`, `PvpStatusModel`; CIL expone ventanas de 60 s, 1 h y 1 día | Opt-in, daño, guardia, kills y estados propios mark/skull/timeline | Validar semántica exacta de ventanas y sanciones mediante runtime |
| Exploración | `StartSession`/`EndSession`, tokens con `SessionGeneration` y `RequestVersion`, snapshots aceptables/rechazables, regiones resueltas, shrines, semillas, hunts y rotaciones | regiones, transición, shrines, hunts simples y persistencia | Añadir sesión/generación/versiones antes de seeds/rotaciones |
| Conexión | `ConnectionLadder`, pasos, protección, silencio/reconnect, outcomes y razones de desconexión | token, reconexión TCP y errores básicos | Implementar máquina de estados visible y razones normalizadas |
| Entidades | outfits, mounts, misiles, efectos, addons y locomoción visual | entidades propias/procedurales, enemigos y proyectiles básicos | Solo incorporar equivalentes propios cuando la semántica esté confirmada |
| Núcleo | 5.499 tipos y 37.668 métodos; no es razonable reconstruirlo 1:1 por metadata | vertical slice independiente | Usar Assembly-CSharp solo para descubrir subsistemas, nunca como contrato completo |

La primera parte de la máquina de conexión propia ya está implementada en
`client/scripts/network_client.gd`: emite `state_changed` para
`connecting`, `connected`, `reconnecting` y `closed`. Los estados de protección,
silencio y razones detalladas siguen bloqueados hasta observación runtime.

## Evidencia REA

- `Assembly-CSharp.dll`: `ev_d8d4ecd2d6305572b3a6d1da6739801dc533eaf202c991776663f10fde0a3f28`.
- `MagicWings.Entities.dll`: `ev_adfaa1375e8f413e4622c2f9db064e9931bddadd6f9a79d0dcd076d84ec76798`.
- Targeting members: `ev_4376977b9fb993b6ca7fb8284a6d8766b2b34bfcf914c1ae6c05d22e27909b0a`.
- PvP members: `ev_31c25ff44dbc48bec47752b86bf3ca292d0fdaf463d5650217060574e1f4e441`.
- Exploration members: `ev_8160ce6b54f07bb79df7c710e3a7aaed99f35eac4f7c07ccd1a64175079b3e1a`.
- Connection members: `ev_a4489301cb5d420bd88a747220289fe71b67c8b99f468317f4d88f0863c52e1d`.

## Corrección aplicada

`client/scripts/domain/combat_awareness.gd` ahora limita la memoria local a 128
impactos por objetivo. La capacidad 128 está observada en el constructor y en
las operaciones de `CombatAwareness` del assembly Targeting; el servidor sigue
siendo la autoridad y esto solo limita el hint visual local.

## Próximas pasadas

1. Inspeccionar tipos y métodos seleccionados de Targeting, PvP, Exploration y
   Connection, guardando firmas, constantes, strings y aristas relevantes.
2. Comparar cada resultado contra un módulo propio del clon, no contra nombres
   aislados.
3. Ejecutar observación runtime únicamente para preguntas que CIL no resuelva:
   targeting real, transición de regiones, conexión y estados PvP.
4. Convertir únicamente diferencias confirmadas en tareas de implementación.
