# TODO maestro — MW Inverse

Este documento es el plan de finalización del experimento. Las casillas se
marcan únicamente después de implementar y validar el comportamiento. La
referencia original permanece aislada en `reference-original/`; el cliente y
el servidor deben seguir siendo independientes y usar código propio.

## 0. Reglas de trabajo y criterios de aceptación

- [x] Mantener cliente Godot 4.7.2 y servidor autoritativo.
- [x] Mantener TCP/JSON como transporte local versionado.
- [x] No copiar automáticamente DLL, escenas, prefabs ni código propietario.
- [x] Mantener la biblioteca recuperada separada del pack propio.
- [x] Validar cada cambio con arranque headless, compilación y pruebas.
- [x] Añadir identificador de versión de protocolo y rechazo de versiones incompatibles.
- [x] Definir compatibilidad de partidas guardadas mediante `SAVE_STATE_VERSION`.
- [x] Smoke test de instalación limpia sin la carpeta de referencia.
- [x] Smoke test de ejecución con la carpeta de referencia desconectada.
- [ ] Crear un informe final reproducible de capacidades y limitaciones.

## 1. Pipeline de assets y presentación

- [x] Extraer PNG y WAV compatibles con UnityPy.
- [x] Catalogar hashes, tamaños, dimensiones y categorías.
- [x] Separar `reference-original/extracted/` del cliente.
- [x] Crear pack runtime opcional y manifiesto validable.
- [x] Conectar HUD, mapa, minimapa, logo, hotbar y audio de interfaz.
- [x] Conectar sprites recuperados al jugador y enemigos durante gameplay.
- [x] Conectar iconos recuperados a combate, defensa, pociones y progresión.
- [x] Conectar efectos visuales y audio a ataques y habilidades.
- [ ] Conectar sprites/modelos de personajes recuperados a NPCs y entidades
      únicamente cuando se confirme que son representaciones de mundo y no
      iconos de interfaz.
- [x] Añadir visor de inspección de la biblioteca completa.
- [x] Crear `AssetResolver` con fallback por categoría y cache LRU limitado para
      texturas y audio de referencia.
- [ ] Evitar rutas hardcodeadas dispersas en scripts de gameplay.
- [x] Añadir caché LRU acotada de texturas y audio.
- [ ] Añadir precarga por región y descarga al salir de región.
- [ ] Convertir texturas grandes a variantes comprimidas para runtime.
- [ ] Crear atlas propio para iconos de hotbar e inventario.
- [ ] Añadir materiales 3D propios con texturas recuperadas solo como referencia visual.
- [ ] Sustituir sprites temporales por modelos propios cuando no exista mesh exportable.
- [x] Exportar los meshes Unity legibles a OBJ y usarlos como props naturales
      mediante un parser OBJ propio de Godot.
- [x] Aplicar texturas de terreno y vegetación recuperadas a la isla y árboles.
- [ ] Crear animaciones propias de idle, caminar, ataque, daño y muerte.
- [x] Añadir animación procedural de idle, movimiento, ataque y flotación de
      entidades para el vertical slice.
- [ ] Añadir audio propio distribuible separado del audio de referencia.

## 2. Cliente: núcleo jugable

- [x] Movimiento WASD, cámara cenital y colisiones básicas.
- [x] Selección automática de objetivos.
- [x] Ataque local y ataque autoritativo.
- [x] Habilidades, energía, cooldown y guardia.
- [x] Mostrar cooldowns de habilidades en la hotbar y bloquear su uso local.
- [x] Daño, muerte, respawn y loot.
- [x] Añadir máquina de estados del jugador: idle, move, attack, cast, hit, dead.
- [x] Bloquear movimiento durante ventanas de casteo configurables en servidor.
- [ ] Añadir telegráficos de habilidades y áreas de impacto.
- [x] Añadir proyectiles visibles y autoridad del servidor sobre su resultado.
- [x] Añadir proyectiles visuales, impactos y efecto de guardia al flujo de combate.
- [x] Añadir feedback de cooldown en hotbar.
- [x] Añadir selección manual con clic y target frame.
- [x] Añadir selección manual con clic, objetivo persistente y target marker.
- [x] Añadir selección manual con clic, objetivo persistente y target marker.
- [x] Añadir rango, línea de visión y obstáculos autoritativos.
- [ ] Añadir interpolación y reconciliación del jugador local.
- [ ] Añadir predicción limitada de movimiento con corrección del servidor.
- [ ] Añadir feedback de latencia, pérdida y estado de conexión.
- [ ] Añadir cámara con zoom, rotación opcional y límites de mapa.
- [x] Añadir cámara con zoom de rueda, rotación Q/Z y límites de distancia.
- [ ] Añadir controles configurables y soporte de mando.

## 3. Mundo, regiones y contenido

- [x] Pradera de entrenamiento, puerto y segunda región propia.
- [x] Portal funcional de transición al puerto con cambio de ambiente y HUD.
- [x] Cambiar música de referencia según la región activa.
- [x] Filtrar enemigos y NPCs visibles por región activa.
- [x] Filtrar también snapshots autoritativos de enemigos por región.
- [x] Añadir NPC de intendencia para la región del puerto.
- [x] Añadir landmarks propios diferenciados para puerto y bosque escarchado.
- [x] Añadir santuarios visibles por región y descubrimiento persistente con `R`.
- [x] Añadir portal visual propio para puerto y bosque escarchado.
- [x] NPCs, diálogos, santuarios y decoraciones persistentes.
- [x] Enemigos básicos, wisps y guardián.
- [ ] Crear una escena propia por región con entrada, salida y loading.
- [x] Añadir límites físicos y colisión básica por obstáculos.
- [ ] Añadir spawn points y respawn por región.
- [ ] Añadir clima, ciclo día/noche y variación de ambiente.
- [ ] Añadir objetos interactivos: cofres, recursos, puertas y portales.
- [ ] Añadir recolección y nodos de recursos con respawn.
- [ ] Añadir vendedores con inventario visible y rotación de stock.
- [ ] Añadir mapa completo por región y minimapa con marcadores.
- [ ] Añadir waypoints y viaje rápido desbloqueable.
- [ ] Añadir streaming de sectores para mapas mayores.
- [ ] Añadir contenido de exploración, logros y coleccionables.
- [ ] Añadir un jefe con fases, telegráficos y recompensas propias.

## 4. Servidor autoritativo

- [x] Login local, sesiones, refresh tokens y MFA TOTP.
- [x] Persistencia SQLite, migración, backups y métricas básicas.
- [x] Validación de movimiento, combate, inventario y chat.
- [x] Presencia, grupos, clanes, comercio y matchmaking local.
- [x] IA básica de persecución y respawn de enemigos.
- [x] Versionar formalmente todos los mensajes del protocolo.
- [ ] Separar conexión, sesión, dominio y persistencia en módulos.
- [x] Añadir timeout autoritativo de inactividad y cierre limpio de sesión.
- [x] Aplicar límites de movimiento por solicitud y rechazo de posiciones bloqueadas.
- [x] Añadir límites de movimiento del mundo y validación autoritativa de rango.
- [x] Idempotencia para ataques, compras y confirmación de comercio mediante `request_id`.
- [ ] Añadir locks transaccionales para inventario y moneda.
- [ ] Añadir journal de eventos para recuperación tras caída.
- [x] Añadir journal de snapshots de estado y consulta limitada por jugador.
- [ ] Añadir persistencia de enemigos y estado de regiones.
- [ ] Añadir colas de trabajo para guardado y backups.
- [x] Añadir endpoint local de health y métricas legibles mediante `health_request`.
- [ ] Añadir TLS probado con certificados locales de desarrollo.
- [ ] Añadir configuración de producción sin secretos en el repositorio.
- [ ] Añadir pruebas de reconexión durante combate, comercio y transición.

## 5. Combate, IA y balance

- [x] Daño básico, habilidades, guardia, energía y cooldown.
- [x] PvP opt-in y respawn.
- [ ] Definir estadísticas de jugador, enemigo, arma, armadura y habilidad.
- [ ] Definir fórmulas de daño, mitigación, crítico, resistencia y curación.
- [ ] Añadir estados: slow, stun, silence, shield, burn, freeze y poison.
- [x] Añadir estado `slow` autoritativo para `frost_nova` y aplicarlo a la IA.
- [ ] Añadir amenaza y selección de objetivo de enemigos.
- [ ] Añadir patrulla, retorno a spawn, huida y leash.
- [ ] Añadir ataques telegráficos y cancelación segura.
- [x] Añadir ataques autoritativos de enemigos en rango y mitigación por guardia.
- [x] Añadir tabla de loot diferenciada por enemigo y evento de recompensas.
- [ ] Añadir balance automatizado y simulaciones de combate.
- [ ] Añadir pruebas deterministas de combate.
- [ ] Añadir anti-cheat básico basado en autoridad y límites.

## 6. Progresión, economía e inventario

- [x] Experiencia, niveles, misiones, moneda e inventario.
- [x] Compra y equipamiento de arma.
- [ ] Añadir slots de equipo completos y estadísticas derivadas.
- [ ] Añadir inventario por slots, stack máximo y peso opcional.
- [ ] Añadir tooltip completo de objeto.
- [x] Mostrar iconos recuperados de objetos en el inventario runtime.
- [x] Usar automáticamente poción de vida o maná según el estado del jugador.
- [ ] Añadir rareza, mejora, reparación y destrucción segura.
- [ ] Añadir crafting, materiales y recetas.
- [x] Añadir loot diferenciado de frostwood y crafting autoritativo de frost_blade
      y health_potion.
- [ ] Añadir economía de vendedor con compra/venta.
- [x] Añadir venta autoritativa de materiales con cantidad, precio y persistencia.
- [ ] Añadir comercio con confirmación doble y expiración.
- [ ] Añadir recompensas diarias, logros y títulos.
- [ ] Añadir misiones ramificadas, requisitos y elecciones.
- [ ] Añadir diario de misiones y marcadores del mundo.

## 7. Social y multijugador

- [x] Chat, presencia, grupos, clanes y matchmaking local.
- [x] Jugadores remotos interpolados.
- [x] Añadir bloqueo social persistente y filtrado autoritativo de chat.
- [x] Chat por canales local, grupo, clan, susurro y sistema.
- [x] Añadir canales local, grupo, clan y sistema con filtrado autoritativo.
- [ ] Añadir roles y permisos de clan.
- [ ] Añadir invitaciones, expulsiones y liderazgo persistente.
- [x] Añadir party frames con vida, nivel y distancia de miembros visibles.
- [ ] Añadir matchmaking con cancelación, timeout y resultado.
- [ ] Añadir instancia cooperativa de 2–4 jugadores.
- [ ] Añadir sincronización de emotes y animaciones sociales.

## 8. UI/UX y accesibilidad

- [x] HUD funcional con vida, energía, experiencia, misión, chat y minimapa.
- [x] Panels de inventario, quests, mapa y estado de red.
- [ ] Añadir navegación completa con teclado y mando.
- [ ] Añadir tooltips, focus states y feedback de botones.
- [ ] Añadir ventanas de comercio, clan, grupo y configuración.
- [ ] Añadir configuración de audio, vídeo, controles y accesibilidad.
- [x] Añadir configuración runtime de volumen, pantalla completa y panel de ajustes.
- [ ] Añadir escala de UI y resoluciones ultrawide.
- [ ] Añadir subtítulos y registro de combate.
- [ ] Añadir colores alternativos para daltonismo.
- [ ] Añadir control de volumen independiente por canal.
- [ ] Añadir pantalla de login, selección de personaje y loading.
- [ ] Añadir manejo visual de errores y reconexión.

## 9. Audio, efectos y pulido

- [x] Música y click de interfaz recuperados integrados.
- [x] Audio de combate y efectos visuales de ataque integrados.
- [ ] Crear buses Master/Music/SFX/UI/Voice.
- [x] Crear buses Music/SFX/UI y asignar reproductores del cliente.
- [ ] Añadir crossfade entre regiones.
- [x] Añadir crossfade entre regiones.
- [ ] Añadir variaciones aleatorias de impactos, pasos y criaturas.
- [x] Añadir variaciones aleatorias de impactos y casteos.
- [ ] Añadir audio de ambiente por región.
- [ ] Añadir partículas reutilizables para cada habilidad.
- [ ] Añadir decals, flashes, trails y números de daño estilizados.
- [ ] Añadir pantalla de muerte, respawn y transición de región.
- [x] Añadir overlay de muerte y botón de respawn conectado al servidor.
- [ ] Añadir postprocesado por región y calidad gráfica.

## 10. QA, pruebas y rendimiento

- [x] Suite de servidor existente y arranque headless de Godot.
- [x] Validación de pack de assets.
- [ ] Añadir tests de protocolo para cada mensaje.
- [ ] Añadir tests de persistencia y migraciones.
- [ ] Añadir tests de autoridad contra entradas maliciosas.
- [ ] Añadir tests de cliente para inventario, targeting y HUD.
- [x] Smoke test de arranque con y sin referencia.
- [ ] Añadir prueba multicliente automatizada.
- [ ] Añadir prueba de carga de 50/100/500 jugadores simulados.
- [ ] Medir FPS, memoria, tiempo de carga y tráfico por región.
- [ ] Añadir profiling y límites de logs.
- [ ] Añadir verificación de archivos y hashes en CI.
- [x] Añadir script automatizado `scripts/check-all.ps1` para regresión local.
- [x] Documentar checklist manual de regresión en `docs/regression-checklist.md`.

## 11. Operación y distribución

- [x] Scripts locales de inicio y detención.
- [x] Añadir configuración `.env.example` completa.
- [x] Añadir Dockerfile y compose opcionales para servidor local.
- [x] Healthcheck y graceful shutdown del servidor.
- [ ] Añadir rotación de logs y backups retenidos.
- [x] Añadir backups SQLite rotativos con retención configurable.
- [x] Restauración de backup probada.
- [ ] Añadir export del cliente Godot para Windows.
- [ ] Añadir paquete de assets propios distribuible.
- [ ] Excluir siempre referencia original, junctions y credenciales.
- [x] Documentación de instalación limpia añadida al README.
- [ ] Añadir changelog y versión del experimento.

## 12. Cierre y límites

- [x] Ejecutar todos los tests y smoke tests.
- [ ] Completar matriz de funcionalidades implementadas.
- [ ] Revisar que ninguna dependencia obligatoria apunte a referencia local.
- [ ] Revisar separación de assets propios y de análisis.
- [ ] Documentar explícitamente recursos no extraídos: meshes, prefabs,
      escenas y animaciones Unity no soportadas por la extracción actual.
- [ ] Generar informe final con comandos reproducibles y resultados.
