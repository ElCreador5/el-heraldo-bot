## H-03 Test real — primer respaldo externo recuperado (2026-10-18)

Base GitHub comprobada y sincronizada: Pruebas@926f6d552f42aca1b63b0e8cbff6d8dd7b335d27.
Implementación directa autorizada por el propietario: worker con backup SQLite
online, bucket/identidad/clave exclusivos Test, recibo anterior a upload,
recuperación aislada por fecha y horario 06:15 UTC con catch-up. Se conserva el
cron sintético con sus credenciales y las generaciones históricas. 18 tests nuevos,
72 H-03 y 39 base OK; compilación y dependencias OK. Suite global SSH interrumpida:
pendiente CI. Transferencia REAL completada 18/10/2026 09:02:59 UTC: 479232 bytes SQLite,
89228 cifrados; descarga, AES-GCM, integridad/FK, esquema y contenido recuperados
correctos. Bot en el mismo proceso y copias previas conservadas. Programador
aún pendiente de despliegue/activación y verificación posterior.
Detalles operativos únicos en RESPALDOS_SUPABASE.md. PR #18 revisada, en borrador:
CI 39075261350 SUCCESS, 22 tests del guard; no integra publicador ni evita bypass.
No se fusionó la PR. main y producción conservan el bloqueo de DECISIONES.md.
Discord interactivo y recuperación independiente de clave ORIGINAL: no realizados.

## H-03 — Inventario exhaustivo de precondiciones (2026-10-18)

**AUDITADO:** `audit/H03_MATRIZ_DE_SALIDA_2026-10-18.md` describe estado verificado y pendientes de datos, almacenamiento, claves, permisos, retención, respaldos de archivos no SQLite, controlador con protección anti-bypass, rollback, avisos y cumplimiento de horario. **DETECTADO:** cron Lab protege exclusivamente SQLite sintética, no datos reales del worker; cinco copias de laboratorio al 18/10 06:15 UTC y única copia productiva antigua del 13/10; el mismo usuario de Storage puede leer/escribir prefijos Lab y producción; worker Test y bot oficial tienen `sleepApplication=true`; el check H03 obligatorio aún no existe. **PENDIENTE:** ciclo completo real de Test y recuperación de clave oficial; PR #18 en borrador. Se preservan todos los bloqueos vigentes y no se realizaron acciones sobre `main`, secretos ni Railway/Supabase producción. **VERIFICACIÓN EN DISCORD:** no realizada.

## H-03 — Contrato fail-closed de laboratorio (2026-10-17)

**IMPLEMENTADO SOLO EN `Pruebas`:** `tools/h03_release_controller_contract.py` (commit `fe65a2b3`), `tests/test_h03_release_controller_contract.py` (commit `25b2dc3b`), 15 pruebas negativas y positivas sin red ni secretos. Contrato sin publicador real y con prohibición programática de producción: exige copia simulada `verified_and_restored`, integridad del SHA de origen y destino y confirmación síncrona del despliegue; no se confunde un encolado con una publicación. **VERIFICADO AUTOMÁTICAMENTE:** CI `39089544729` SUCCESS en Python 3.11/3.12/3.13; 475 tests de la suite en Python 3.12 OK. **Discord:** no realizado. **PR #18:** sigue en borrador, sus primitivas no se integraron; no existe controlador confiable productivo ni check H-03 obligatorio. Detalles y pasos restantes en `audit/H03_CONTROLADOR_LAB_2026-10-17.md`. **PRODUCCIÓN/main:** intactos, bloqueo de `DECISIONES.md` vigente.

## Tarjetas de salida, expulsión y ban con formato compacto — 2026-10-17

**IMPLEMENTADO en `Pruebas@cfa65386a8b2ee37eb6a6acb44ce7ef6f030d025`:** los registros de miembros pasan a presentar líneas compactas de usuario, ID, ingreso relativo de Discord, roles, cantidad de miembros y avatar. En expulsiones y baneos aparecen motivo/autor cuando se conocen; los BAN muestran duración y vencimiento solo si existe un expediente de moderación reciente coincidente (si falta evidencia: «No consta»). La tarjeta específica de expulsión por falta de orientación reutiliza el mismo formato, preserva estado del DM, primera/segunda oportunidad y deduplicación de la salida. Se conserva el filtro de eventos, los canales específicos y el editor de plantillas de `/setup → Mensajes → Logs`. Enlaces a otros registros de Sapphire no se inventan porque la implementación no almacena URL equivalentes verificables. **VERIFICADO AUTOMÁTICAMENTE:** GitHub Actions `39072801052` SUCCESS Python 3.11/3.12/3.13 y `39072801040` SUCCESS Mensajes; 12 tests específicos nuevos y regresiones existentes correctas. Railway Test worker/cron SUCCESS. **VERIFICADO EN DISCORD:** pendiente inspección visual y evento real autorizado. `main` sin modificaciones. **Obsidian:** no conectado.

## Verificación: avisos repetidos tras redespliegues de Railway Test — 2026-10-17

**DETECTADO:** los avisos repetidos de 11 miembros no procedían de main; Railway Test los emitió durante cuatro arranques entre 21:18 y 21:23 UTC. El estado del último aviso se guardaba solo en RAM. **IMPLEMENTADO en `Pruebas@4b09b5ffc5d68ec8a0ed0de3837d34381793f377`:** `bot.py` persiste una huella SHA-256 de los IDs ordenados de pendientes y contradicciones en `meta` SQLite, aislada por servidor. Guarda el recibo únicamente cuando `log_embed` confirma entrega a Discord, no cambia `guild_config.updated_at` ni añade listas de usuarios a los embeds. Si desaparecen todos los pendientes, actualiza silenciosamente el recibo para avisar de una reaparición. Test solo puede iniciar plazos nuevos de conciliación en el servidor autorizado por `HERALDO_TEST_LAB_GUILD_ID`; en los demás informa sin rearmar. **AUTOMÁTICAMENTE VERIFICADO:** CI `39071427613` SUCCESS Python 3.11/3.12/3.13 y Mensajes `39071427760` SUCCESS; Railway Test worker y cron SUCCESS, Gateway conectado. El primer arranque posterior publicó una vez un aviso actualizado con 5 pendientes, sin probar su causa ni la entrega tras otro reinicio todavía. **DISCORD interactivo: no realizado.** `main` intacto, producción sin despliegue. Documentación Obsidian externa no disponible.

## Cierre automatizado — Conciliación de verificación (2026-10-17)

**VERIFICADO AUTOMÁTICAMENTE en `Pruebas@8fe6ad50`:** GitHub Actions `39070454746`, Python 3.11/3.12/3.13 SUCCESS, y Mensajes `39070454752`, SUCCESS. En Python 3.11 se ejecutaron las seis pruebas nuevas `VerificationReconciliationTests` satisfactoriamente (442 casos de tests/ en ese job). Railway Test: worker y cron SUCCESS; worker registró conexión al Gateway. **DISCORD REAL: NO REALIZADA.** La producción no se modificó; la desactivación de `sleepApplication` queda pendiente de recuperación productiva reciente y revisión de rollback. Código de la solución: `22078f82`.

## Verificación: recuperación conservadora tras desconexiones — 2026-10-17

**IMPLEMENTADO en `Pruebas@22078f822a6918ae29026d6ebdd3a9bb387ff67c`:** `bot.py` inicia un loop de conciliación cada 30 minutos que enumera miembros con la API de Discord y detecta rol Sin Verificar sin vencimiento persistido. Solo ingresos de menos de 15 minutos, con verificación activa, rol configurado, sin verificación previa, sanción o temporizador, reciben un plazo NUEVO; máximo 25 por ronda. Los demás se enumeran agregadamente para revisión, incluyendo contradicciones de rol; el bucle no expulsa ni cambia roles. Conserva la corrección ya vigente en Pruebas para reintentos y temporizadores simultáneos. `tests/test_verification_reconciliation.py` incluye seis casos offline, sin Gateway.

**PRUEBAS:** Mensajes run `39070271627` SUCCESS; run Python `39070271559` cancelado por avance concurrente de la rama, reejecutado como `39070308567` (resultado por confirmar). Railway Test está autodesplegando el código; SUCCESS de Railway no acredita Discord. Verificación interactiva: NO REALIZADA. **Producción:** `main@c6a5c164` intacto y Railway `sleepApplication=true`; no desactivar sin copia productiva reciente, recuperación y reversión verificadas. Pendiente distinguir los miembros antiguos desde Discord sin expulsarlos masivamente. Obsidian externo no conectado.

## Honeypot: confirmación temporal limpia y panel actualizado — 2026-10-17

**IMPLEMENTADO EN PRUEBAS** `cdb5995` y `8eb6019` (base `5f58bc7`). En `/setup → AutoMod → Honeypot → Configurar aviso → Publicar aviso` el primer clic difiere la actualización del mensaje original y envía una confirmación efímera separada; Confirmar acusa recibo inmediatamente antes de consultas o llamadas API, revalida permisos, borrador, plantilla, canales y estado, guarda la activación si corresponde, sincroniza avisos idempotentemente, actualiza el embed de la subvista original mostrando avisos publicados registrados y resultado, y retira la confirmación temporal. Cancelar retira el mensaje sin persistir. Errores parciales o fallo de edición del panel se comunican sin declarar éxito falso. **VERIFICADO AUTOMÁTICAMENTE:** regresiones Python 3.11/3.12/3.13 run `39070088743` SUCCESS, Mensajes `39070088787` SUCCESS, Railway Test cron/worker SUCCESS con `8eb6019`. **DISCORD REAL:** aceptación del nuevo flujo pendiente en Heraldo's Lab. `main` intacta. Otros confirmadores genéricos de `/setup` no se reescribieron en este lote.

## Honeypot — archivo omitido solo por origen, verificado en Pruebas (2026-10-17)

**IMPLEMENTADO Y VERIFICADO AUTOMÁTICAMENTE** en código `Pruebas@8816b319` (base inicial `6585883`, commits `aac28d5`, `e600809`, `8816b319`). La eliminación y purga cuyo origen explícito es Honeypot no conservan archivos de evidencia; se verifica miembro, servidor, permisos y rango al eliminar, tanto purga temporal como limitada por mensajes y detecciones duplicadas. La condena por Honeypot conserva expediente, tarjeta, DM y roles sin archivar pruebas; demás orígenes continúan con archivo verificable. Nuevas detecciones no registran contenido de mensajes en historia/logs; no se borra evidencia histórica. Regresiones nuevas y existentes aprobadas en Python 3.11/3.12/3.13 (Heraldo Lab `39062591876` SUCCESS) y Mensajes `39062591851` SUCCESS. Railway Test worker y cron SUCCESS con SHA de código `8816b319`. **Prueba real en Discord: NO REALIZADA.** Producción y main intactas.

## Honeypot: no conservar evidencia de medidas originadas en la trampa — 2026-10-17

**IMPLEMENTACIÓN preparada para Pruebas:** ruta de borrado específica de Honeypot que verifica autor, servidor, permisos y fecha sin enviar archivos al depósito. Incluye expulsión (24 h mínimas y configurable), aislamiento, condena con origen Honeypot y borrado del disparador. La condena conserva su expediente y tarjeta, sin recopilar prueba; otros orígenes conservan el archivo privado verificable. El historial y los logs nuevos de Honeypot registran metadatos sin contenido del mensaje. Datos archivados previamente no se alteran. Pruebas nuevas: `tests/test_honeypot_no_evidence.py`, más regresiones ajustadas. CI, Railway Test y Discord pendientes de verificación de este lote.

## Honeypot: publicar o actualizar el aviso desde /setup — 2026-10-17

**IMPLEMENTADO en `Pruebas`:** `/setup → AutoMod → Honeypot → Configurar aviso` incluye ahora **Publicar aviso** (verde), además de Editar texto y Editar diseño. El botón abre una confirmación independiente (Confirmar publicación verde, Cancelar rojo); hasta confirmar no publica ni altera ajustes. Revalida usuario, canales trampa, estado y plantilla, permisos del bot para mensajes/embed/fijado/historial y bloquea propuestas obsoletas; bloquea también la acción cuando hay cambios generales de Honeypot pendientes. Si el aviso estaba desactivado, confirmar también lo activa. Reutiliza `hp_sync_all_warnings` / `hp_sync_warning`: edita el mensaje existente en lugar de duplicarlo y comunica errores parciales sin anunciar éxito falso. No se publican mensajes si no hay trampas.

**Evidencias fuera de Honeypot:** la nueva solicitud de no retener evidencias cuando el incidente no provenga de Honeypot requiere especificar alcance: el motor compartido de purgas actualmente exige archivo privado antes de borrar, y otros módulos como Condenas mantienen expedientes recuperables. **No se cambió la retención ni se eliminó evidencia de otros módulos sin resolver ese conflicto**, ni se alteró la purga existente de 1 día al expulsar. Se requiere una decisión expresa sobre qué acciones ajenas a Honeypot dejarían de archivar o si el alcance solicitado se refiere únicamente a mensajes purgados por Honeypot que no sean parte del incidente. Tests nuevos `tests/test_honeypot_warning_publish.py`. **VERIFICADO AUTOMÁTICAMENTE:** código `Pruebas@475c1f8f`, GitHub Actions Python 3.11, 3.12 y 3.13 `39056219619` SUCCESS, Mensajes `39056219466` SUCCESS; Railway Test worker y cron SUCCESS. **DISCORD REAL: NO REALIZADO.** `main` intacta.

## Honeypot: purga segura al expulsar y parámetros desde /setup — 2026-10-17

**IMPLEMENTADO en Pruebas (commit de este lote; consultar HEAD tras push):** la acción **Expulsar** utiliza `heraldo_kick` y, solo si Discord confirma la expulsión, solicita mediante `hp_start_kick_purge` una purga de mensajes de ese usuario en el servidor, por defecto de las últimas **24 horas** y configurable entre 1 y 30 días desde el panel. Se usa `run_purge_job → purge_user_messages → delete_with_evidence`; sin archivo privado verificado no se borra ningún mensaje. La purga se ejecuta en segundo plano, puede ser parcial por permisos/evidencias y deja un log separado; la notificación inicial nunca afirma que terminó. Un fallo de purga no repite la expulsión; fallos de Discord no la inician. El umbral antifallos y el tercer mensaje conservado permanecen intactos.

**Interfaz:** `/setup → AutoMod → Honeypot → Configurar acción → Configurar medida` añade selectores contextuales: Expulsar (1/2/3/7/14/30 días), Banear (permanente/5 minutos/1 hora/1/7/30 días con duración exclusiva del Honeypot), Aislar (10/30/60 minutos/6 horas/1/7/28 días más purga) y rol de castigo (purga); la gestión del rol compartido continúa en Roles de `/setup`. Solo se muestran parámetros aplicables. Los selectores generan borradores, y únicamente el botón **Guardar cambios** en el panel principal persiste; Descartar no guarda. Se revisan los snapshots de acción, purga y duración para rechazar configuraciones obsoletas. Se mantienen las opciones slash existentes como alternativa. `main` no se ha modificado. **VERIFICADO AUTOMÁTICAMENTE** en `Pruebas@94fac034` (código `69d04d55` más corrección de fixture): GitHub Actions Python 3.11/3.12/3.13 `39055478658` SUCCESS, Mensajes `39055478741` SUCCESS, Railway Test worker y cron SUCCESS. **DISCORD REAL: NO REALIZADO.**

## Honeypot: acciones automáticas Expulsar y Banear — 2026-10-17

IMPLEMENTADO en `Pruebas` (commit de este lote, verificar SHA tras push): el selector de `/setup → AutoMod → Honeypot → Configurar acción` y `/honeypot setup accion` incluyen **Expulsar** y **Banear** además de rol, registro y timeout. Ambas rutas ejecutan `heraldo_kick`/`heraldo_ban` reales si la opción se guardó expresamente, comprueban permisos del administrador al guardar y permisos/jerarquía del bot al actuar, y generan expediente automático `KICK` o `BAN` mediante `moderation_case_create` (sin doble registro de heraldo_ban). Banear usa la duración general de Moderation (Test: por defecto 5 minutos; fuera de Test, permanente salvo configuración específica), sin purgar historial adicional; Expulsar tampoco purga el historial. Los valores antiguos de almacenamiento `kick`/`ban` continúan tratándose como rol: solo los nuevos `kick_enabled`/`ban_enabled` autorizan sanciones de expulsión o baneo, evitando una conversión peligrosa tras desplegar. En errores de Discord no se crea expediente; si falla SQLite después de una medida ejecutada, se registra el problema en los reportes sin reintentar la sanción. Regresiones nuevas `tests/test_honeypot_kick_ban.py`. **VERIFICADO AUTOMÁTICAMENTE:** código `Pruebas@143c855f`, GitHub Actions `39053065266` (Heraldo Lab Python 3.11/3.12/3.13 SUCCESS) y `39053065320` (Mensajes SUCCESS); Railway Test worker y cron SUCCESS tras el push. **DISCORD REAL: NO REALIZADO.** `main` no se modifica; Obsidian remoto no accesible.

## Honeypot: panel compacto y controles coherentes — 2026-10-17

IMPLEMENTADO en `Pruebas` sobre `bc27b80`: `/setup → AutoMod → Honeypot` usa un embed de cuatro bloques (Estado actual, Medida aplicada, Aviso y seguimiento, Cambios pendientes), sin mostrar parámetros ajenos a la acción ni listas vacías. La ficha representa el estado guardado, no el borrador, y los cambios pendientes aparecen por separado. Botones: Crear canal azul (abre confirmación efectiva), Retirar canal rojo (confirmación; no elimina canal Discord), Activar/Pausar/Reanudar dinámica verde/rojo, Configurar acción/aviso/Detalles azules, Guardar verde, Descartar rojo, Volver gris. Subpanel Aviso concentra editores existentes de texto y diseño; Acción permite preparar registro/rol/timeout; Detalles muestra exenciones/historial/comandos existentes. Seleccionar canal ya registrado no duplica. Guardar revalida canal, permisos, roles y snapshot de ajustes/trampas antes de persistir; cambios concurrentes se rechazan; descartar no guarda. Crear canal se confirma independientemente; no se hace pasar por un borrador del guardado general. Cobertura agregada: `tests/test_honeypot_panel.py`. **VERIFICADO AUTOMÁTICAMENTE** en `Pruebas@2d6b3aa`: CI Heraldo Lab `39050050630` SUCCESS en Python 3.11, 3.12 y 3.13, y Mensajes `39050050561` SUCCESS; compilación y regresiones del panel incluidas. Railway Test worker y cron SUCCESS del mismo commit. **VERIFICACIÓN REAL EN DISCORD: NO REALIZADA.** `main` sin modificaciones. Obsidian remoto no conectado.

## Honeypot: conservar el mensaje al activar antifallos — 2026-10-17

IMPLEMENTADO en `Pruebas`: `hp_handle_trigger` comprueba el umbral multiservidor ANTES de llamar a `delete_with_evidence`. Si se detecta el tercer veterano distinto en 5 minutos, marca `honeypot_paused=1`, conserva el mensaje original, no sanciona y avisa a los moderadores en el canal de Logs con el canal y miembro afectados. Los disparos ordinarios mantienen la misma secuencia de archivo seguro/borrado y sanción. La pausa sigue limitada por servidor y conserva contadores de otros servidores. Pruebas agregadas en `tests/test_honeypot_isolation.py` para conservación sin intento de borrado y orden en la ruta normal; **VERIFICADO AUTOMÁTICAMENTE:** GitHub Actions `39040312547`, Python 3.11, 3.12 y 3.13 SUCCESS (compilación, dependencias y regresiones); workflow de Mensajes `39040312540` SUCCESS. Railway Test: worker y heraldo-h03-lab-cron SUCCESS tras el push del código. **Discord real: NO REALIZADO.** No cambió SQLite, `main` ni lógica de condenas. El aviso depende de tener configurado un canal de Logs accesible; no se envía a canales alternativos no autorizados.

## Seguridad Honeypot: aislamiento multiservidor — 2026-10-16

IMPLEMENTADO en `Pruebas` (commit de este cambio): `_hp_busy` usa `(guild_id, user_id)`; `_hp_veteran_hits` contiene servidor y miembro, cuenta veteranos distintos solo del servidor afectado, expira registros de la ventana y al alcanzar el umbral limpia únicamente los del servidor pausado. `/honeypot history` revalida `configuration_access` antes de leer eventos; simplificados los textos de exenciones. Regresiones nuevas: `tests/test_honeypot_isolation.py` (multiservidor, duplicados intraguild, expiración, lectura sin permisos). **VERIFICADO AUTOMÁTICAMENTE** sobre `Pruebas@e379fc96`: GitHub Actions `38980795158` (regresiones Python 3.11, 3.12 y 3.13 SUCCESS) y `38980795137` (Mensajes SUCCESS); compilación, dependencias y regresiones incluidas en el flujo. Railway Test: worker y cron registran despliegues SUCCESS posteriores al push de ese commit. **VERIFICACIÓN REAL EN DISCORD: NO REALIZADA**. No se altera el motor compartido de condenas, SQLite, `main` ni acciones configuradas. El disparador sigue llamando a `delete_with_evidence` antes de la pausa por umbral; revisar comportamiento con aprobación separada si se quiere cambiar. Obsidian remoto no accesible en esta sesión.

## Fusión de canales: previsualización y seguridad implementadas — 2026-10-16

IMPLEMENTADO en `Pruebas@4cc337d0930ba2e086b00e1f9ab41560c370dca6`, en `bot.py`: la vista previa final enseña origen → destino, **cantidad actual de mensajes**, nombre final, efecto sobre origen y **cinco pasos en secuencia**. Explica que los mensajes del origen se recrean al final del destino del más antiguo al más reciente, y advierte sobre autoría, fecha, respuestas y adjuntos. Botones: **Confirmar fusión** verde, **Volver** gris (editor de borrador para origen, destino, nombre y eliminación del origen; actualizar vista previa con recuento fresco), **Cancelar** rojo. Se rechaza antes de escribir si el recuento difiere del aprobado o si faltan permisos; si el historial del origen cambia durante la migración o no puede revalidarse, se conserva y no se elimina. Se mantienen registros, log, política de adjuntos y tareas existentes.

Commits: `b37b2456` (flujo + vuelta), `0488d561` (reverificación del origen + pruebas), `79f0cc59` (pruebas de ejecución simulada), `4cc337d0` (fixture Discord). `tests/test_fusion_preview.py` cubre la representación y callbacks por AST, además de ejecutar casos de recuento cambiado, permisos revocados y origen modificado en simulaciones sin acciones reales. **VERIFICADO AUTOMÁTICAMENTE:** GitHub Actions run `38978968508` `Heraldo Lab - Python regressions`, matrices 3.11/3.12/3.13 SUCCESS, y Mensajes run `38978968411` SUCCESS. **NO VERIFICADO EN DISCORD.** Railway Test puede autodesplegar `Pruebas`; comprobación de servicio independiente. Sin cambios en `main`, BD/producción ni Obsidian externo.

## Botones «Cancelar» y «Cerrar» en rojo — 2026-10-16

IMPLEMENTADO en `Pruebas`: actualizado el color de los botones etiquetados «Cancelar», «Cancelar edición» y «Cerrar» a `discord.ButtonStyle.danger` en `bot.py`, `message_editor.py`, `message_components.py` y `message_automation.py`. Ningún callback, guardado, esquema SQLite ni permiso modificado. Actualizada la regresión `tests/test_button_palette.py`, que ahora comprueba el nuevo color y mantiene «Volver»/«Vista previa» grises. Los colores anteriores de Cancelar/Cerrar que figuren en informes históricos ya no aplican. Verificar el CI del SHA de este cambio y después en Discord Test; no confundir CI con verificación interactiva. La simplificación funcional del programador de embeds sigue como tarea separada. `main` sin modificaciones.

## Primera aplicación de paleta semántica de botones — 2026-10-16

IMPLEMENTADO en `Pruebas`: cambios de estilo en los decoradores de `bot.py` y botones construidos dinámicamente, además de `message_components.py`, `message_editor.py` y `message_automation.py`. Descartar, eliminar, advertir y otras acciones destructivas se representan en rojo; guardar, activar o publicar en verde; editar/configurar/abrir formularios en azul; volver, cancelar y cerrar paneles sin efectos en gris. El selector de activación del programador y la confirmación de canales Honeypot cambian su estilo según la acción que se va a tomar. Los botones personalizados con acción de eliminar se identifican en rojo; los botones externos `link` conservan el estilo inmodificable de Discord. No se cambian sanciones ni permisos ni registros SQLite.

Commits: `9da683bd`, `08cf0c31`, `c32141eb`. Test añadido: `tests/test_button_palette.py`. VERIFICADO AUTOMÁTICAMENTE: `Heraldo Lab - Python regressions` run `38976183423` — SUCCESS en Python 3.11, 3.12 y 3.13; `Mensajes - verificación de regresiones` run `38976183535` — SUCCESS. Estas pruebas no certifican funcionamiento interactivo en Discord. Railway Test puede desplegar automáticamente `Pruebas` al hacer push; verificar SHA exacto y servicios antes de ensayos reales. `main` no modificado.

**Pendiente separado:** la petición previa de eliminar «Revisar programación», sustituirlo por Guardar cambios directo y ofrecer Descartar cambios con restauración de borrador **aún no está implementada** por este lote de colores. Auditar gradualmente los flujos de guardado del resto de módulos conservando protección de borradores, permisos y concurrencia. Ningún cambio en Obsidian remoto.

## CI general recuperado y línea base histórica — 2026-10-16

**Pruebas@453488d9, verificado automáticamente:** se identificó el último CI verde anterior a fallos acumulados (`ce958431`, run `38691251173`). `825ef2c` ya fallaba antes de `bded3bb`. Tras corregir tests/fixtures para la interfaz vigente y una incompatibilidad Unicode 15 en Python 3.11, el run `38868053698` aprobó matrices 3.11, 3.12 y 3.13. El test de «Solo reportar» ejecuta ahora la normalización real de opciones heredadas y asegura que no se activa ninguna ventana de purga; no se realizó ninguna purga en Discord. Los tests del selector y modal verifican borradores sin guardado. Commits: `fb2477f`, `61cf275`, `453488d`. Los flujos Actions activos usan ubuntu-24.04 y checkout@v5/setup-python@v6. Railway Test dos despliegues SUCCESS al SHA final; interacciones Discord NO VERIFICADAS. main intacta. Riesgo pendiente: auditoría completa de secretos de toda la historia del repositorio público y ensayos reales de fallos parciales, permisos, vistas, SQLite, sanciones/expiración. Esta verificación no constituye aceptación para main.

## Vencimiento seguro de MUTE — 2026-10-16

DETECTADO: la tarea de caducidad de sanciones capturaba errores HTTP al retirar un aislamiento pero cerraba igualmente el expediente; tampoco distinguía un aislamiento posterior. IMPLEMENTADO en Pruebas: la caducidad MUTE consulta otro caso abierto posterior en SQLite y recupera el miembro antes de actuar; si falla SQLite/Discord, conserva caso pendiente para reintentar; si hay caso posterior o timeout externo más largo, no lo retira y clasifica el expediente vencido para revisión. Tests añadidos `test_reliability_startup_roles.py`; no probado en Discord ni main.

## Auditoría de fiabilidad: arranque, permisos y SQLite — 2026-10-16

DETECTADO por inspección en Pruebas: fallos de sincronización de paneles/consulta de invitaciones podían abortar `on_ready`, y una consulta SQLite fallida se interpretaba como ausencia de acción de sanción pendiente al perdonar. El componente público de roles no revalidaba permisos/condiciones tras `guild.fetch_member`. IMPLEMENTADO en Pruebas: recuperación aislada por servidor y función al arrancar, consulta de acciones pendientes con error cerrado (no autoriza perdón si SQLite falla), y comprobación repetida de permisos/rol/estado en componentes públicos con mensaje específico. Pruebas aisladas `tests/test_reliability_startup_roles.py`. Faltan CI SHA y validación en Discord Test. No modificar main ni afirmar auditoría integral completa.

## Programación de embeds: claridad de la interfaz — 2026-10-15

IMPLEMENTADO en Pruebas: corregido texto de confirmación que mostraba secuencias literales \\n. Ahora las condiciones de las seis frecuencias se explican en lenguaje natural, no como JSON. Estado activo/desactivado y botones Revisar/Confirmar reflejan la acción real; cada cambio reinicia la confirmación. Campos no aplicables se ocultan en el modal. Se mantiene el guardado explícito; Cancelar no guarda. Nueva regresión test_embed_schedule_wording.py; CI y Discord por verificar. Sin cambios en main.

## Duplicación de registros por expulsión de orientación — 2026-10-15

IMPLEMENTADO en Pruebas: cuando expel() publica con éxito el embed detallado «Kick — Falta de verificación», el listener on_member_remove no publica además «Miembro expulsado» por esa misma operación. Guardas transitorias por servidor, usuario y sesión de ingreso, actor bot y razón auditada, TTL 30s, espera de publicación 5s; las expulsiones manuales, baneos, demás salidas y ausencia/fallo de la tarjeta detallada siguen registrándose. No altera sanciones, DMs ni archivo de auditoría de Discord. Regression tests/test_orientation_kick_dedup.py. Verificar CI y Discord Test; producción intacta.

## Nombres legibles para /embed — 2026-10-15

IMPLEMENTADO en Pruebas: /embed crear acepta nombres de hasta 64 caracteres con letras y tildes, números, espacios, emojis habituales y signos seguros. Normalización Unicode NFKC y casefold, espacios repetidos simplificados y rechazo de menciones y controles. Crear, editar, enviar, borrar y autocompletar usan la misma clave, conservando nombres históricos ASCII, publicaciones y programaciones. Nueva suite tests/test_embed_names.py, CI y Discord reales por verificar; main intacta.

## BAN temporal y avisos de laboratorio — 2026-10-15

IMPLEMENTADO en Pruebas: motor central condena todos los orígenes con motivo estándar de Test; la resolución de una condena antigua en Test presenta también ese motivo. Rutas de kick/ban intentan DM antes de la medida con disculpa e invitación privada de 1 uso; el baneo impide entrar hasta desbaneo. Nuevo /setup → Moderation → Baneo temporal: duración configurable por servidor, 0 permanente, selección o modal personalizado con confirmación explícita; Test por defecto 5 minutos, main/producción permanente si no se configura. /ban explícito y BAN por reacción conservan prioridad; caso BAN temporal vence mediante tarea existente que reintenta unban fallido. Pendiente CI del SHA exacto y pruebas reales Discord, no tocar main.

## Mejoras de configuración y ejecución de sanciones por reportes — 2026-10-15

IMPLEMENTADO en `Pruebas`: `/setup → Moderation → Reportes → Sanciones y límite` permite máximo de WARN 1–5 (3 predeterminado), opción al alcanzar el máximo (Solo avisar por defecto; Aislar, Expulsar, Banear o Condenar) y activación/desactivación individual de las acciones por reacción: Advertir, Aislar, Expulsar, Banear y Condenar. La duración de Aislar por acumulación se elige en menú (30m/1h/1d/7d); todas las modificaciones exigen confirmación y cancelación no guarda. Ajustes globales de reacciones no desactivan comandos manuales. No se modifica la configuración heredada hasta que un administrador confirme. Escalamiento usa reclamo persistente aditivo `moderation_warn_escalations` por servidor/usuario/expediente con estado y no reintenta castigos con resultado incierto. DM del WARN precede a expulsión o baneo por alcanzar el máximo; no hay purga automática de estos escalados. Se revalidan permisos/jerarquía antes de condena directa por reacción tanto al iniciar como al confirmar motivo; condenas por umbral siguen usando `condemn_member` (expediente, rol, anuncio, hilo y evidencias). El selector de acción se reubicó junto a reacción; `Regla` pasa a `Configurar condiciones`; el modal oculta parámetros que no aplican y explica umbral, duración y purga. Pruebas: `tests/test_moderation_reaction_policy.py` y suites existentes adaptadas. **Las pruebas reales de Discord siguen pendientes**, con despliegue automático Test y regresiones a comprobar en SHA final; `main` intacta.

## Límite configurable de advertencias vigentes — 2026-10-15

**IMPLEMENTADO en `Pruebas` (validación automatizada y en Discord pendiente):** sistema WARN preexistente ampliado sin recrear historiales. `moderation_warning_limit` admite 1 a 5 por servidor (predeterminado 3) y el contador `vigentes/máximo` se muestra en `/advertencias`, DMs de expedientes y avisos administrativos. Solo cuentan casos WARN abiertos sin fecha de vencimiento pasada; los cerrados/expirados permanecen en el historial. `/warn` y la reacción ❗ comparten el mismo límite; creación de advertencia bajo transacción SQLite `BEGIN IMMEDIATE` impide excederlo por concurrencia. Al alcanzarlo, informar a moderación; bloquear nuevas WARN, sin castigos, purgas ni borrados automáticos. Menú: `/setup → Moderation → Reportes → Máx. advertencias`, selector 1-5 con confirmación y cancelación. Los máximos nuevos inferiores al conteo existente no eliminan advertencias y bloquean nuevos avisos hasta resolver las vigentes. Tests: `tests/test_moderation_warn_limit.py` y adaptación de `tests/test_moderation_warning_reaction.py`. No se modifica `main`.

## Reportes: acciones automáticas y expedientes (2026-10-15)

IMPLEMENTADO en `Pruebas`: acciones por reacción conservan las cinco opciones existentes. Para timeout/kick/ban confirmados por Discord se crea un caso administrativo y una referencia idempotente por servidor/mensaje/miembro/reacción mediante nueva tabla `moderation_report_cases` (migración aditiva); fallos en SQLite dejan advertencia en el resultado sin repetir la sanción. Se revalidan permisos del bot y jerarquía antes de sancionar, timeout sin duración se rechaza. La purga tras timeout/kick/ban conserva su archivo individual de evidencia antes de borrar, pero el log de éxito se integra en el reporte final; fallos conservan advertencia independiente. En editor, se limpian duraciones incompatibles al pasar a Solo reportar/Expulsar/Banear, se avisa sobre sanciones con umbral de una persona y se validan permisos al guardar. Regresiones añadidas en `tests/test_moderation_report_actions.py`. **Pendiente confirmar ejecución automatizada en Railway y pruebas funcionales Discord con miembros de laboratorio**. No se cambian reglas existentes ni `main`.

## Mejoras de editores de /setup — horarios y reportes (2026-10-15)

**IMPLEMENTADO EN Pruebas, validación pendiente:** Miembro de la Semana → Horario reemplaza el formulario numérico día (0–6)/hora (0–23) por dos menús de nombres de días y horas (hora RD), con borrador, revisión y cancelación. La revisión pasa por la confirmación central y rechaza horarios obsoletos. En Moderation → Reportes, la acción de cada reacción pasa a un selector entre Solo reportar, Timeout/mute, Condenar, Expulsar y Banear. Los parámetros de duración, umbral y purga conservan entradas personalizadas; elegir una acción solo cambia el borrador. Solo reportar descarta la purga pendiente, Timeout exige duración al guardar y los canales vuelven a validar permisos. Los guardados de canal MOTW y de Reportes rechazan configuraciones concurrentes obsoletas. Pruebas nuevas: tests/test_setup_editor_selectors.py y tests/test_editor_drafts_behavior.py. **CI y prueba interactiva en Discord pendientes de comprobar.** Railway Test puede autodesplegar desde Pruebas; main y producción no se modifican. Se conserva exportación/importación legítima de kits JSON y el sistema de confirmación central.

## Reaction Roles — opciones elegibles en /setup (2026-10-15)

En `Pruebas` el editor de Reaction Roles ya permite elegir por menús desplegables el acceso («Todos», «Lista blanca», «Lista negra»), reacciones invertidas (Sí/No) y el límite (0 a 20). Las selecciones actualizan exclusivamente el borrador; el botón Descartar devuelve los valores iniciales y Guardar en el editor es el único que publica los cambios. Se conserva la configuración anterior y la compatibilidad de los roles y emojis del panel. Regresiones estructurales en `tests/test_reaction_options_dropdown.py`. Prueba real en Heraldo's Lab pendiente; `main` intacta. Otros módulos con opciones aún escritas requieren revisión progresiva.

## Expedientes con hilos privados y primer selector de configuración — 2026-10-15

**IMPLEMENTADO EN `Pruebas`, pendiente de pruebas reales en Discord:** tras asignar Condenado y publicar exactamente la misma tarjeta configurable con mención al miembro, El Heraldo intenta crear un hilo privado independiente en el canal de condenas, añade únicamente al condenado y enlaza dicho hilo desde un botón adicional «Conversación privada» en la tarjeta, sin modificar el embed ni el botón Perdonar. Solo quienes sean invitados o tengan Gestionar hilos pueden acceder a la conversación; los demás condenados con permiso de Leer historial del canal principal sí pueden ver las tarjetas públicas: limitación expresa de Discord, ya explicada al propietario. Hilos privados no deben convertirse en públicos cuando falle su creación. En el hilo se publica un mensaje informativo sin nueva mención al condenado. Al liberar o perdonar se archiva y bloquea la conversación, preservando su historial. La base guild_cases incorpora thread_id y thread_requested (migración sin borrar datos), reutiliza la identidad por servidor y reintenta completar accesos y enlaces tras reinicios solo para expedientes marcados por la nueva función. Expedientes históricos permanecen sin migrar. Fallos y permisos ausentes se reportan sin cancelar la condena ni su DM. Discord puede requerir nivel 2 de mejoras para hilos privados.

**INTERFAZ:** /setup → Moderation → Condenas incorpora botón «Preparar acceso» (confirmación explícita antes de modificar permisos de rol sobre el canal) y desplegable de duración predeterminada con opciones comunes y «Duración personalizada»; solo confirmar guarda. No se tocaron configuraciones reales de ningún servidor. Esto inicia, pero no completa, la petición general de reemplazar opciones de texto por selectores en todos los módulos; pendientes una auditoría completa y migración gradual de las restantes configuraciones de opción cerrada.

Archivos: bot.py, tests/test_condemnation_private_threads.py y documentos de coordinación. Pruebas automatizadas: consultar resultados CI para el SHA del commit; prueba funcional real con El Heraldo Test en Heraldo's Lab pendiente. `main` intacta.

## Registros consolidados de condena/purga — desarrollo 2026-10-15

Cambio solicitado por el propietario al observar en producción dos embeds administrativos por una condena con purga. En `Pruebas` se conserva el evento principal «Condena aplicada» y se actualiza ese mismo mensaje con el resultado real de la purga asíncrona. `run_purge_job` sigue generando registros de éxito en todos los otros contextos; si falta el mensaje original, la edición falla o la purga falla, se conservan avisos separados para no perder trazabilidad. El archivo privado de evidencias y el evento posterior «Condena perdonada» se mantienen independientes. Cambios limitados a `bot.py` y nuevas regresiones `tests/test_condemnation_log_dedup.py`. Verificación automática GitHub Actions posterior al commit; interacción real en Discord pendiente. Producción `main` no se modifica.

## Auditoría de integración recibida de Claude — 2026-10-14

Informe guardado en [`audit/AUDITORIA_INTEGRACION_2026-10-14.md`](audit/AUDITORIA_INTEGRACION_2026-10-14.md). Claude verificó 257 pruebas offline según su informe; ChatGPT corroboró ramas, Railway y existencia del commit candidato no referenciado `203ea14a`. `main` sin actualizar; H-03 productivo desactivado. PR obligatorio con `python-checks` y autorización explícita de rama temporal. No equivale a aceptación de los 192 commits.

## Preparación sin despliegue y recuperación aplazada — 2026-10-14

El propietario aplaza hasta noviembre de 2026 la verificación independiente de Bitwarden. Existe una nota privada importada con la clave original, pero NO se ha probado su recuperación/descifrado desde una sesión o dispositivo independiente ni la recuperación de acceso a la bóveda. No tocar la clave, no repetir la importación y no ejecutar operaciones productivas que dependan de ese requisito. Esto permite seguir preparando y verificando código con datos sintéticos.

Base de trabajo: Pruebas 13af6c31fc97e8528bf03e571305b9c6b688a539. Main sigue 6f9f9ee0a7ed1c7b7e6c48a13817b9b5f3a5b667. Producción SUCCESS en bbb21914-a87c-44f3-b862-f4ba3ceecd09, sin cambios pendientes. Test SUCCESS, start python bot.py, preDeploy vacío; no se cambiaron sus secretos ni configuración para ejecutar pruebas.

Defecto corregido en backup_job._isolated_restore: SQLite creaba el destino con permisos dependientes de umask (habitualmente 0644). Ahora se reserva con O_EXCL/O_NOFOLLOW y modo 0600 antes de abrir SQLite; no se cambia umask global desde el hilo del bot, ni se sobrescribe un destino existente. Dos regresiones nuevas verifican privacidad con umask 022 y conservación del archivo existente.

Verificación Linux aislada en Railway Test: compilación, pip check, 39 regresiones históricas y 218 de tests/ aprobadas (257). Transporte simulado, sin credenciales en el proceso hijo, sin importar/iniciar el bot para operar Discord. Warnings no fatales preexistentes en mocks. No son pruebas humanas Discord ni prueba productiva.

Siguiente etapa realizada: tools/prepare_h03_candidate.py construye en directorio NUEVO un candidato basado exclusivamente en main fijo, añade cuatro módulos H-03 y cryptography, e inserta un hook protegido por bandera antes de importar dependencias. Una comparación AST comprueba que el resto de bot.py es idéntico. No crea ramas, no publica main ni despliega. La primera ejecución local encontró un error de indentación del comprobador; corregido y candidato válido generado en otro directorio, conservando el anterior.

Candidato ensayado en proceso aislado de Railway Test: 29 regresiones históricas disponibles en main, compilación y dependencias correctas; extracción AST de db_connect/db_init sin ejecutar el módulo del bot, creación de esquema sintético de main, fila sintética, inicialización candidata, backup y restauración nueva y vuelta a inicialización main. Esquema y contenido coinciden; H03_CANDIDATE_PASS. Programador sin bandera no inicia. Ninguna migración nueva se incorpora al candidato. Esto valida compatibilidad sintética del cambio mínimo; NO sustituye instantánea productiva reciente ni aceptación funcional real antes de desplegar.

Pendientes: recuperación independiente en noviembre, alerta con entrega comprobada, auditoría final de candidato/credenciales y nueva instantánea justo antes del futuro despliegue autorizado. El PR 16 no se integró. No hay respaldo diario real de producción activado ni borrado de copias. Revisar CI y autodespliegues del commit de esta etapa antes de atribuirles éxito.

## H-03 — cron interno preparado; producción condicionada (2026-10-14)

**IMPLEMENTADO SOLO EN `Pruebas`:** `production_backup_scheduler.py` y hook protegido en `bot.py:on_ready`, más `tests/test_production_backup_scheduler.py` (10 pruebas), compilación añadida al workflow. Diariamente 06:15 UTC, pero **desactivado sin bandera productiva/identidad/secreto y no iniciado en Test**. Ejecuta SQLite y Supabase desde el mismo proceso dueño de `/data` mediante hilo auxiliar, sin segundo bot; recibos persistentes e idempotentes. Commits de código: `c7577ce`, `1861e1fb`, `af90f1b`, `e28af475`, workflow `bef4daca`.

**VERIFICADO AUTOMÁTICAMENTE EN RAILWAY TEST:** 10/10 pruebas nuevas del planificador, luego 216/216 suite `tests/` con patrón `-p 'test_*.py'`, y 39/39 pruebas raíz históricas. La primera invocación del patrón sin comillas falló por expansión de shell, se corrigió y se reejecutó con `OK`. Retirados comandos de pre-deploy; no hubo datos de producción ni interacciones Discord.

**PRODUCCIÓN PENDIENTE DE PRERREQUISITOS:** propietario autorizó avanzar hasta despliegue cuando se validen condiciones. Verificado que servicio Railway producción aún carece de seis variables Supabase/clave H-03 y bandera; no hay segunda copia confirmada de la clave real custodiada en el PC. Tampoco consta alerta entregable (tareas ChatGPT: notificaciones y email desactivados). Es inseguro activar H-03 o desplegar main antes de segunda custodia, traslado seguro de secreto, respaldo reciente, prueba de compatibilidad main→candidato y plan de reversión. Instrucciones precisas en `AUTOMATIZACION_H03.md`. `main`/Railway producción no modificados; la generación externa previa sigue intacta.

## Fase H-03 — reserva de volumen verificada (2026-10-14)

**IMPLEMENTADO EN `Pruebas`:** `backup_job.py` comprueba antes de crear recibo y subir datos que queda espacio para tres SQLite (copia, descarga y restauración) y mantiene un margen mínimo adicional de 64 MiB. Admite `HERALDO_BACKUP_VOLUME_CAP_MB` para aplicar la cuota real cuando el filesystem indica más espacio que el volumen asignado; recuenta ficheros del volumen sin seguir enlaces simbólicos, no borra generaciones. Código commit `24489e0`, regresiones commit `28a4063`.

**VERIFICADO AUTOMÁTICAMENTE:** `python -m unittest discover -s tests -p test_backup_job.py -v` en Railway Test: **10/10 OK**, despliegue `431d16b9-68a4-4b88-af47-9e0bc1fdd771` SUCCESS. Se retiró pre-deploy temporal, inicio normal `python bot.py`. Variable `HERALDO_BACKUP_VOLUME_CAP_MB=500` añadida **solo al cron Lab** mediante Railway Test; sin cambios de `main`/producción. Una falta de capacidad impide intentar el respaldo; NO autoriza borrar ningún archivo.

## Refuerzo H-03, seguridad de avisos y comprobaciones — 2026-10-14

**CORREGIDO EN `Pruebas`:** el verificador `tools/backup_health.py` podía dar por válida una generación `verified_and_restored` sin marca real de finalización, usando medianoche como alternativa, y no exigía identidad del recibo. Ahora rechaza recibos sin `version=1`, `environment=lab`, día UTC coherente, hora de inicio y finalización verificables, estados desconocidos, períodos futuros, permisos no privados y archivos `lab-*.json` mal formados. No se lee SQLite real ni se altera el almacenamiento. Commits de código y pruebas: `78f31a1`, `1d3581b`.

**VERIFICADO AUTOMÁTICAMENTE:** Railway Test ejecutó `python -m unittest discover -s tests -p test_backup_health.py -v` mediante pre-deploy temporal: **14/14 OK**, despliegue `85eeacfb-63a7-4c56-ad9b-939882446fcd` SUCCESS. El comando temporal fue retirado y comprobado `preDeployCommand=[]`, `startCommand=python bot.py`. Cron Lab `cronReady/SUCCESS`, trabajador Discord Test Online 1/1, `staged=null`. Producción no modificada. Sin pruebas humanas Discord.

**RIESGOS ABIERTOS:** vigilancia ChatGPT de producción configurada y ejecutada, pero `notifications_enabled=false` y `email_enabled=false` (comprobación de tareas 2026-10-14): **no se acredita entrega de alertas al propietario**. La tarea de vigilancia local Codex Lab depende del equipo y no se ha verificado una entrega. Sigue existiendo únicamente una generación externa de producción; no se producen copias periódicas reales. Se requiere segunda copia recuperable de la clave de producción fuera del PC, definición de ejecutor siempre disponible y autorización específica para cambios en producción. No se ha decidido retención destructiva; no eliminar ninguna generación. La capacidad finita de volúmenes requiere umbrales antes de activar una política periódica.

## Automatización H-03 verificada en laboratorio — 2026-10-14

Código de ejecución publicado en Pruebas: cf9f2da77406dd79a6abf254fe445e3092a3bb4f, sobre e59bb4f. Main y producción conservan 6f9f9ee0a7ed1c7b7e6c48a13817b9b5f3a5b667. Sin ramas nuevas ni PR; PR #16 no integrado. Checkout anterior divergente preservado.

Servicio independiente heraldo-h03-lab-cron en Railway Test, volumen privado propio de 500 MB, sin DISCORD_TOKEN ni DB_PATH, seis referencias de secretos exclusivamente Lab. Worker conserva python bot.py y preDeploy vacío, SUCCESS y conectado al Gateway. No hubo cambios funcionales en bot.py ni configuración del worker.

**Ejecución programada real:** 2026-10-14 14:15:04–14:15:13 UTC (10:15 local), run 71b4b38d-f85c-4ca2-bb55-fc3a8224955e, despliegue dc2cedd1-e0d7-42f4-bc8d-3012a1dc84a4. VERIFIED_AND_RESTORED a las 14:15:07, H03_HEALTH OK, proceso EXITED. La frontera de activación bloqueó el respaldo durante el despliegue inicial: la primera transferencia completa fue del programador, no manual. SQLite sintética, API backup, AES-256-GCM, subida/descarga autenticadas, SHA-256, integridad/FK y restauración aislada con esquema/recuentos/contenido coincidentes. Supabase pasó de 1 a 2 objetos Lab: solo una generación nueva de 782 bytes cifrados. La generación productiva existente no cambió.

**Persistencia/duplicados:** segunda ejecución manual del cron a las 14:15:44 UTC en contenedor nuevo: ALREADY_ATTEMPTED no_retry=true, H03_HEALTH OK y proceso terminado. Sin nueva subida. No confundir esta segunda invocación manual con el disparo programado anterior. Recibos y generaciones permanecen privados en el volumen.

**Pruebas:** 39 + 195 = 234 regresiones offline en proceso Linux aislado de Railway Test, compilación y pip check aprobados; transporte simulado, sin iniciar Discord. CI del commit cf9f2da: workflows Mensajes y Heraldo Lab aprobados (runs 38577334609 y 38577334553). Prueba negativa real contra Supabase con API key inválida solo en proceso efímero: acceso denegado antes de subida, recibo needs_manual_review, segundo intento bloqueado. Corrupción GCM y clave incorrecta rechazadas con datos sintéticos. Períodos omitidos, fallos, fecha futura y antigüedad desde finished_at cubiertos por regresiones. Logs operativos inspeccionados: solo estados/fechas, sin secretos, filas ni manifiestos. Warnings no fatales preexistentes en mocks SQLite/discord.py; no pruebas humanas Discord.

Horario diario configurado: 06:15 UTC / 02:15 America/Santo_Domingo; se aplica con el despliegue de este commit de cierre y se verifica después. Vigilancia local Codex diaria 08:00, solo Lab, deduplicación por incidencia; depende del equipo/Codex. Vigilancia productiva previa de ChatGPT no modificada. Primer disparo futuro del monitor pendiente: no se afirma entrega de alertas probada.

Producción NO automatizada. Procedimiento, límites y autorización pendiente en AUTOMATIZACION_H03.md. Segunda custodia de clave productiva y ejecutor continuamente disponible siguen pendientes; no se movió la clave. No se borraron respaldos, registros ni datos. Obsidian sin conexión.

## Actualización de laboratorio H-03 — 2026-10-14

**VERIFICADO AUTOMÁTICAMENTE EN RAILWAY TEST:** el despliegue `7fd7ace1-2fa6-40ff-8548-5517cd199561` ejecutó `python -m unittest discover -s tests -p test_scheduled_lab_backup.py -v` como prueba temporal: **Ran 6 tests — OK**. Se probaron identidad de Railway Test, rechazo de token Discord, obligatoriedad de volumen persistente, generación de SQLite sintética, salida idempotente ante intento duplicado y fallo crítico propagado. No se usaron SQLite real ni servidor Discord ni red externa durante esas regresiones.

**RESTAURADO/COMPROBADO:** el servicio `worker` de Railway Test vuelve a `startCommand=python bot.py`, `preDeployCommand=[]`, Online/SUCCESS 1/1; `get_staged_changes` devolvió `staged=null` y cero recursos. El borrador de cron y volumen temporal que estaba pendiente quedó completamente descartado por el propietario. `main`/Railway producción intactos.

**PENDIENTE:** los seis casos son unitarios con simulación, NO un disparador cron real ni una transferencia real programada. La activación productiva exige arquitectura que lea la BD real sin duplicar el acceso al volumen, conservación independiente de clave y autorización específica para modificar `main`/producción. El monitoreo de metadatos de Supabase no genera respaldos.

## Fase 1 H-03 — preparación del cron aislado (2026-10-13, continuación)

**IMPLEMENTADO EN `Pruebas`, NO ACTIVADO:** entrada `tools/scheduled_lab_backup.py`, ejecutable sin `bot.py`, que fabrica exclusivamente SQLite sintética, exige Railway Test y volumen persistente, impide el uso de `DISCORD_TOKEN`, llama a `backup_job.run_once` y termina. Añadidos seis casos en `tests/test_scheduled_lab_backup.py` y su compilación en CI. **Ejecución de esta nueva suite y cron reales: pendientes de confirmar**.

**Railway Test:** `worker` existente preservado. Intento de configurar un servicio cron dedicado bloqueado por controles de seguridad de la herramienta; NO se desplegó ni programó. Se eliminó el servicio vacío en vivo, pero el conector dejó un **borrador STAGED NO APLICADO** en Railway Test: un servicio temporal de cron y un volumen de estado de 100 MB con referencias de variables. **No aceptar ni desplegar este borrador**; descartarlo desde Railway antes de continuar la fase. El conector no dispone de operación de descarte, y la eliminación de recursos todavía no aprovisionados devolvió error. Producción y `main` no se modificaron.

Próximo paso: descartar el borrador con controles autorizados, ejecutar CI de la nueva suite y acordar una arquitectura de programación que no dependa de la clave de producción guardada exclusivamente en PC ni exija montar el volumen del bot en dos servicios. No activar producción sin revisión/permiso específico.

## Avance fase 1 H-03 — 2026-10-13

**IMPLEMENTADO EN `Pruebas`**: `backup_job.py` (una ejecución consistente H-03 + subida, descarga, validación y restauración aislada; diario por día UTC con protección antiduplidos; guardas de identidad estrictas para producción), seis regresiones `tests/test_backup_job.py` y compilación de nuevo módulo incluida en workflow. **VERIFICADO AUTOMÁTICAMENTE EN RAILWAY TEST**: suite `6/6 OK` en pre-deploy aislado, despliegue `8e87b5b2-64c4-443e-bc38-0a4a67e44dba` `SUCCESS` y servicio `Online`. Transporte Supabase de esta suite simulado; anterior prueba sintética de subida/descarga Supabase ya consta separadamente. Se retiró el pre-deploy temporal. Monitorización diaria por automatización ChatGPT de edad del último respaldo de producción (umbral 36 h) activada.

**PENDIENTE CRÍTICO**: el ejecutor no se ha conectado a un programador, no hay nuevas copias automáticas de producción, ni segunda custodia comprobada de la clave del primer backup. Falta plan para evidencias externas y segundo destino. `main` intacta. Detalles en `RESPALDOS_SUPABASE.md`. Discord real: no probado en esta fase.

## Actualización H-03 — respaldo externo de producción (2026-10-13)

**REALIZADO SEGÚN INFORME DE CODEX LOCAL:** generada copia consistente SQLite mediante `Connection.backup` sin detener ni modificar el bot de producción. Se cifró externamente con AES-256-GCM usando clave distinta de la empleada en Test, se transfirió a Supabase con la cuenta técnica y se descargó, autenticó y restauró en SQLite aislada. El informe documenta integridad SQLite y claves foráneas correctas, coincidencia de esquema y contenido, prueba de rechazo de manipulación GCM y ausencia de cambios en producción. **Estas verificaciones de contenido/descifrado proceden del informe aportado por el propietario, no han sido repetidas por ChatGPT.**

**VERIFICADO INDEPENDIENTEMENTE POR CHATGPT (consulta 2026-10-13):** en Supabase Storage existe exactamente 1 objeto cifrado bajo la categoría de producción (100609 bytes) y 1 objeto de laboratorio; el bucket sigue privado y las políticas son solo INSERT/SELECT para usuarios authenticated restringidos por identidad. Railway producción sigue Online/SUCCESS con el despliegue anterior; Railway Test también Online/SUCCESS. No se leyó SQLite ni su clave, ni se modificó `main`.

**RIESGO PRIORITARIO:** la clave de descifrado de esta generación se conserva en un único equipo local según el informe. El propietario debe conservar una **segunda copia de la clave** en un medio seguro independiente (p. ej., gestor de contraseñas con recuperación u offline cifrado) y verificar acceso a ella. No publicar clave, rutas privadas, identificadores de generaciones, manifiestos ni datos en repositorio/Discord/chat. No repetir copia ni proceso de subida sin control de idempotencia; no hay aún protección continua.

**PENDIENTE:** periodicidad y supervisión de nuevos respaldos, política de conservación, segundo destino y disponibilidad ante pausas de Supabase Free, ensayos periódicos de restauración y cobertura independiente de adjuntos/evidencias externos de Discord. No implica autorización para desplegar `main`, restaurar producción ni ejecutar escrituras administrativas. Sin pruebas Discord en esta fase.

## Estado H-03 Supabase actualizado — 2026-10-13

**VERIFICADO AUTOMÁTICAMENTE EN RAILWAY TEST:** cuenta técnica Supabase y RLS limitadas al bucket privado, 6 variables presentes en Railway Test (sin leer valores), subida cifrada, descarga y restauración completa de una **base sintética** en contenedor de pre-deploy. Logs `H03_SMOKE status=PASS` del despliegue Test `ef2cc191-accd-4b9c-8ab3-4d07acf9fc87`, servicio Online 1/1, un objeto `lab/` en Storage. Se retiró pre-deploy y no se dejó programación activa. Código: `supabase_backup.py`, `tools/supabase_smoke_test.py`, `requirements.txt` (cryptography solo en Pruebas), tests y `RESPALDOS_SUPABASE.md`.

**NO REALIZADO:** primer respaldo de SQLite de producción, restauración de datos reales en aislamiento, verificación del tamaño de esa base, respaldo de evidencias externas Discord, programación y monitorización; `main` permanece intacta y Online. No confundir el éxito del ensayo ficticio con recuperabilidad real. Supabase Free: 50 MB/objeto, 1 GB almacenamiento, posible pausa. Referencia: `PRUEBAS_DISCORD.md`.

## Preparación Supabase H-03 — 2026-10-13

Bucket privado `heraldo-sqlite-backups` en proyecto Supabase Free (0 objetos, sin políticas de acceso en la inspección inicial). Herramienta `supabase_backup.py` y regresiones offline agregadas en Pruebas; no se modifica `bot.py`, `main` ni producción. Dependencia optativa `requirements-backup.txt`. Railway Test redeploy automático por commits de Pruebas, sin cambio de runtime funcional. **Respaldo real NO EXISTE todavía.** Falta identidad técnica de Auth con RLS restringida, instalación de secretos en Test, ensayo subida/descarga/restauración y pruebas reales. Límites Free: 50 MB/objeto, 1 GB total, posible pausa del proyecto. Pasos: `RESPALDOS_SUPABASE.md`.

# Estado compartido — El Heraldo

**Actualizado:** 2026-10-08
**Repositorio:** `ElCreador5/el-heraldo-bot`
**Producción:** rama `main` — no modificar sin revisión y autorización.
**Desarrollo/pruebas:** rama `Pruebas`, desplegada desde el servicio Railway `worker` del proyecto independiente **El Heraldo - Test**.
**Bot de prueba:** El Heraldo - Test; servidor de laboratorio: Heraldo's Lab.

## Verificaciones confirmadas
- Railway: despliegue de `Pruebas` en estado `SUCCESS`, commit `a69f59b` (observado 2026-10-08); conectado a Discord Gateway.
- Log de inicio: «Autoprueba /setup correcta en Heraldo's Lab» y conexión del bot de test; **esto no reemplaza ensayos manuales de botones**.
- Almacenamiento Railway independiente: volumen `worker-volume`, mount `/data`; servicio con variables `DISCORD_TOKEN`, `DB_PATH`, `MESSAGE_CONTENT_INTENT` (valores sensibles no documentados).
- GitHub Actions `python-checks`: compilación y pruebas de regresión completadas con éxito en los últimos cambios de código verificados; las pruebas de Discord siguen pendientes.
- Ramas de trabajo: `main` y `Pruebas`. PR histórico #2 fue cerrado sin fusionar.

## Módulo Mensajes en Pruebas (implementación parcial)
- Acceso desde `/setup`; plantillas con embeds, imagen URL, enlace y vista previa.
- Edición y publicación de plantillas; `/sendtemplate`.
- Botones y selectores de roles con comprobaciones de permisos; kits JSON básicos; editor raw.
- Confirmación de guardado, borrado e importación para operaciones del editor.
- `/edittemplate`: edición manual de un mensaje del propio bot mediante enlace y confirmación explícita.
- Pruebas de regresión para confirmación, cancelación, conflictos de kits y aislamiento de sesión.
- **No afirmar paridad completa con Sapphire:** falta completar acciones de componentes, menús avanzados, variables, edición visual avanzada, automatizaciones, programación, sticky y catálogo general de mensajes.


## Desarrollo actual — Logs de miembros (2026-10-08)
- En `/setup → Logs` la navegación hacia las plantillas visuales se eliminó: se editan en `/setup → Mensajes → Logs`.
- Categoría «Miembros»: salidas, expulsiones, baneos y advertencias, con eventos configurables y selección de canal individual. Los nuevos eventos empiezan desactivados y requieren «Guardar cambios» para activarse.
- Se añadió observación de `on_member_remove` y consulta de auditoría (si el bot dispone de acceso) para diferenciar salida, expulsión y baneo, sin emitir los tres registros por el mismo evento. Avatar, roles, fecha de incorporación y recuento actual se incluyen cuando están disponibles.
- **Limitaciones que requieren trabajo adicional:** la atribución de expulsiones/baneos depende de la auditoría de Discord y puede ser insuficiente o tardía; no se ha implementado aún un flujo específico para advertencias (warn), ni una prueba interactiva completa en Discord. La edición de plantillas existente necesita una revisión adicional para confirmar todos los guardados mediante botón explícito.
- No considerar paridad terminada con Sapphire ni desplegar este módulo a `main` sin validaciones.

## Continuidad: ampliación de Logs (2026-10-08)
- Los avisos de `/warn` ya generan un evento de miembros configurable cuando se crea correctamente un caso. El registro original de Moderation continúa independiente; vigilar posibles notificaciones redundantes.
- Se incorporó confirmación explícita para editar contenido y diseño de plantillas de logs y para restaurarlas; cancelar deja la configuración intacta.
- Pruebas offline adicionales: aislamiento por servidor, estado inicial desactivado, confirmación, cancelación y permisos del editor.
- **Pruebas reales de Discord todavía no realizadas:** confirmar salidas, expulsiones, baneos, advertencias, canales, permisos, edición visual, cambios de configuración, reinicios y manejo de auditoría tardía. No desplegar en `main` sin finalizar esta revisión.
- **Limitación:** la clasificación salida/kick/ban utiliza auditoría reciente; si la auditoría no está disponible o llega tarde, se puede clasificar como salida. La configuración de `warn` está disponible, pero no se ha verificado con una advertencia real en el laboratorio.

## Otras áreas que requieren pruebas en laboratorio
- Condena, perdón, tarjeta al canal y DM, evidencias persistentes, duración y permisos.
- Reaction Roles, Join Roles, verificaciones, reportes, logs, sugerencias y recuperación tras reinicio.
- Revisar `PRUEBAS_DISCORD.md` para casos y resultados; no confundir «implementado» con «comprobado».

## Próximo objetivo
Realizar recorrido real y reproducible de `/setup` → Mensajes (guardar, cancelar, publicar, editar, botones, roles, importación), registrar errores en `PRUEBAS_DISCORD.md` y corregirlos en `Pruebas`. Después ampliar las funciones respecto a la referencia Sapphire.

## Actualización
Cada agente debe registrar fecha, commit, resultado y riesgos reales; preservar historial. Esta página no es una garantía de que todas las funciones estén correctas.

## Publicación aislada de Logs a producción — 2026-10-09 UTC
- PR #4 fusionado a `main` por squash; commit `6f9f9ee0a7ed1c7b7e6c48a13817b9b5f3a5b667`.
- GitHub Actions: comprobaciones `python-checks` exitosas para el PR; sintaxis y cuatro regresiones offline específicas de eventos de miembros.
- Railway `©El Heraldo`, entorno `El Paraíso`: despliegue en estado `SUCCESS`; registro de conexión al Gateway Discord y autoprueba de `/setup` correctos.
- Incluye configuración de eventos/canales de miembros, logs de salidas, expulsiones, baneos, advertencias y guardado confirmado de plantillas desde Mensajes.
- **Pruebas reales de salida/kick/ban/warn en Discord: NO realizadas.** Los eventos nuevos empiezan desactivados y requieren activación administrativa. La consulta de auditoría necesita permisos; algunos eventos pueden no atribuirse con certeza.
- **Continuidad:** `Pruebas` ahora tiene un commit de `main` sin incorporar; reconciliar antes de futuras ediciones y evitar fusionar cambios experimentales completos.

## Laboratorio automatizado — propuesta en revisión (2026-10-09)
- Rama de trabajo: `feature/lab-automated-checks-20261009` (PR pendiente). Sin desplegar a `Pruebas` ni a `main`.
- Se propone CI para PR hacia `Pruebas`: compilación Python, `test_regressions.py` y descubrimiento de las regresiones `tests/test_*.py`, sin Discord ni tokens.
- Railway y la conexión a Discord deben comprobarse por separado tras un despliegue autorizado; `SUCCESS` no sustituye una prueba de botones.
- No existe automatización autorizada de cuentas personales. Una futura prueba de interacciones reales necesita diseño y credenciales de bot oficial separadas, con alcance y acciones limitadas.

## Continuidad — etapa 1 preparada, 2026-10-09 (America/Santo_Domingo)
- Bases comprobadas: `Pruebas@b8480b8`, `main@6f9f9ee`, PR #6 originalmente en `ffefb77`. Divergencia remota de partida: 48 commits exclusivos de Pruebas y 1 de main.
- Copia local preparada en la subcarpeta `el-heraldo-bot`, con entorno `.venv`. No iniciar `bot.py` para comprobar el entorno: el arranque real sincroniza comandos y activa tareas.
- Merge local `b181770`: incorpora `main` conservando íntegro `bot.py` de Pruebas. Los tres conflictos eran el comentario del observador de miembros, `LogTemplateResetConfirmView` y la entrada Mensajes del menú; se conservaron. Se incorporaron `test_member_logs.py` y su workflow.
- También se incorporó el historial del PR #6. Su actualización añade CI completo para Python 3.11/3.12/3.13, pin directo de discord.py solo para CI y exclusiones de archivos locales. La propuesta se publica en la rama existente del PR; no se hace push directo a Pruebas ni a main.
- Verificación local: Python 3.12.10, discord.py 2.7.1; compilación correcta, `pip check` correcto y 40 pruebas aprobadas (35 generales, 4 de miembros, 1 del selector). SQLite desechable, sin conexión a Discord.
- El sandbox de Windows bloqueó inicialmente temporales y red; las instalaciones y las suites SQLite se completaron con permisos concedidos. Se usó `-X utf8` para evitar errores de consola por la ruta Unicode.
- CI histórico del PR #6: ejecución 37889193532 correcta (35 + 1 pruebas). El resultado de la nueva matriz debe consultarse para el nuevo HEAD; no extrapolar el resultado anterior.
- Discord: NO probado en esta sesión. Railway: NO desplegado ni reconfigurado. Producción: sin cambios.
- Pendientes de etapas siguientes, detectados por inspección: rol 0 persistido en condenas nuevas; permisos no revalidados en algunas confirmaciones; emojis inválidos en selector de canales; modales de condenas con guardado inmediato; purga que continúa aunque falle el archivo de evidencias; expiración dependiente de caché y auditoría tardía en Logs.
- Conservar el aviso de verificación de preferencia: el PR #3 que pretendía eliminarlo se cerró sin fusionar.
- Siguiente paso: comprobar CI del PR #6, integrar mediante merge cuando se autorice el efecto de despliegue en laboratorio y abordar regresiones de condenas. Agent AVD no identificado inequívocamente; no atribuirle decisiones sin fuente.

## Punto de continuidad — 2026-10-10: correcciones en desarrollo
- PR #6 fusionado mediante merge en `Pruebas@34fa94f`; incorpora la ascendencia de main. CI posterior correcto; despliegue del laboratorio `f1b82ab5-0a4a-4071-9ee3-bb6fc596e6ab` correcto, con conexión Gateway y autoprueba de setup. No acredita pruebas interactivas. `main@6f9f9ee` permanece intacta.
- Trabajo nuevo: persistencia del rol real de condena; bloqueos por servidor/miembro para condena y perdón; expiración consulta miembros fuera de caché y conserva casos cuando no se puede consultar el servidor.
- Evidencias: sin respaldo al canal de condenados; rechazo de archivo público o autor distinto; copia de hasta diez adjuntos y cancelación de purga vinculada si la copia es incompleta. Pendiente revisar retención y archivo de todos los mensajes de una purga amplia.
- Configuración: permisos revalidados en 31 vistas, selector de canales corregido, propuestas confirmadas para diseño y duración de condenas, rechazo de borradores obsoletos en Mensajes y confirmación genérica.
- Logs: reintentos de auditoría y descripción explícita de incertidumbre. Aún necesita validación real de salidas, kick, ban y warn.
- Mensajes: texto independiente, hasta diez embeds, campos/autor/pie/miniatura mediante JSON o kit, seis variables con límites tras expansión, vistas previas sin ejecutar acciones, kit v2 e importación de archivo de hasta 128 KiB con reemplazo confirmado. Conserva kits v1 y plantillas anteriores.
- Publicación y edición comprueban permisos del usuario en el canal. Autoservicio de roles rechaza permisos administrativos, condenas activas y pulsaciones concurrentes; espera inicial y límite de frecuencia.
- Verificación local: 39 regresiones raíz y 25 en tests aprobadas en Python 3.12, discord.py 2.7.1, sin Gateway. Hubo una invocación incorrecta de unittest con discover como nombre de módulo; corregida y repetida con éxito. CI de estos cambios todavía pendiente.
- No está terminado el alcance completo: editor visual avanzado, menús independientes/multiacción, programación persistente, autorespuestas, sticky, webhooks, catálogo completo de textos y revisión integral de confirmaciones. Join Roles con demora aún utiliza tareas en memoria; pendiente recuperación tras reinicio. Reaction Roles y reportes requieren revisión adicional.
- Siguiente paso: preservar este lote en PR hacia Pruebas, ampliar pruebas de evidencia/restauración y completar módulos restantes antes de declarar preparado el recorrido integral en Discord. Agent AVD sigue sin identificarse inequívocamente.

### Continuidad adicional — 2026-10-10
- El primer lote está preservado en el PR #7 (borrador hacia Pruebas), commit remoto cb58e4e; CI 38033889706 aprobada en la matriz. Sin fusionar ni desplegar.
- Se añade cola SQLite de Join Roles: ingresos conocidos sobreviven reinicios, no repiten demora, esperan aceptación de reglas, consultan al miembro por API y descartan trabajos de ingresos anteriores o condenas activas. No recupera eventos que Discord no entregó durante una desconexión; requiere ensayo de reinicio real.
- Reaction Roles aplica también la política de roles administrativos y bloqueo por condena. Las regresiones existentes ahora declaran explícitamente permisos y tipo de los roles simulados.
- Doce modales adicionales preparan propuestas: tiempos generales, demora/sincronización de Join Roles, horario semanal, orientación, raids y textos/diseño de verificación y sugerencias. La propuesta incluye archivo comparativo y el panel se sincroniza después de confirmar. No implica que todos los comandos/configuraciones heredados hayan sido migrados.
- Pruebas locales: 39 raíz y 30 en tests aprobadas (69). Falta ejecutar la matriz remota para esta ampliación. Próximo bloque: restauración/evidencias y automatizaciones de Mensajes; aún no se declara preparación integral para Discord.

### Programación y estado más reciente — 2026-10-10
- Se incorpora `/programar_mensaje crear/listar/retirar`, accesible desde la ayuda de `/setup → Mensajes → Programación`. Publicación puntual, diaria o semanal con zona IANA y confirmación. Máximo 25 programaciones por servidor. Usa la versión guardada de la plantilla al ejecutar.
- Estado de ejecución en SQLite; vuelve a comprobar permisos del creador y del bot. Reinicios conservan pendientes; un envío interrumpido queda en revisión y no se repite automáticamente. Las ejecuciones vencidas se agrupan en un único envío al volver; no se reproduce todo el atraso. Una retirada no puede deshacer un envío ya iniciado.
- Se añade tzdata para disponibilidad de zonas en Windows. Compilación CI incluye los nuevos módulos.
- Corregida interferencia de los hooks globales: las plantillas explícitas conservan texto independiente y sus pies; no se les añaden caracteres después de validar el límite agregado de embeds.
- Estado de verificación actual: 78 pruebas offline (39 raíz + 39 tests), compilación y pip check correctos. La CI del primer commit del PR #7 pasó; consultar el HEAD más reciente para esta ampliación. Ninguna nueva prueba interactiva ni despliegue.
- Alcance restante: autorepuestas, sticky, webhooks, menús/opciones independientes y multiacción, editor visual avanzado, catálogo completo de mensajes, revisión de comandos heredados sin confirmación, pruebas de restauración parcial/evidencias y recorrido de reportes/verificación. No declarar terminado ni desplegar como versión final.

### Autorespuestas, sticky y webhooks — 2026-10-10
- CI del segundo commit remoto del PR #7, 4e696e6: ejecución 38034714893 correcta. Pruebas remotas y producción permanecen en 34fa94f y 6f9f9ee, respectivamente.
- Se añaden /autorespuesta crear/listar/retirar: coincidencia literal exacta o de palabra/frase, confirmación, máximo 25 reglas, espera persistente por regla y límite común de 30 segundos por canal. Se ignoran bots, webhooks y condenas activas; no se almacenan mensajes recibidos. Requiere Message Content.
- Se añaden /sticky crear/listar/retirar: un sticky activo por canal, confirmación, reposición tras actividad humana, espera configurable y recuperación SQLite. Comprueba que la publicación anterior pertenece al bot antes de retirarla. Actividad durante un envío queda pendiente. Retirar conserva la última publicación; los estados inciertos requieren revisión.
- Se añade /webhook_mensaje: propuesta visual, confirmación separada y permisos del autor/bot en destino. Solo crea/reutiliza webhooks del bot. No se aceptan URLs arbitrarias ni se almacenan tokens. Admite enlaces, pero no acciones de roles: estas deben publicarse mediante el bot. Un fallo incierto exige revisar el canal antes de reintentar.
- Accesos explicativos en /setup → Mensajes; listados extensos se adjuntan completos, sin perder identificadores por truncamiento.
- Verificación: 91 pruebas offline (39 raíz + 52 tests), compilación correcta. Pendiente CI del nuevo HEAD y pruebas reales. No se ha desplegado el PR #7.
- Próximo bloque: componentes por plantilla/opción y acciones múltiples, editor visual avanzado, catálogo de textos, revisión restante de condenas/restauración/evidencias y comandos heredados sin confirmación. Después validar el lote en laboratorio y registrar el recorrido interactivo. No declarar alcance total terminado.


### Estado consolidado para revisión del PR #7 — 2026-10-10
- Esta sección sustituye las listas de pendientes históricas anteriores. Nuevo editor `/editar_plantilla`: borradores visuales de texto independiente, múltiples embeds, imágenes, autor, pie y campos; guardar requiere confirmación y detecta cambios concurrentes. Un modal tardío no reabre un editor cancelado.
- `/componentes_mensaje`: botones y menús por plantilla, opciones independientes, selección múltiple y secuencias confirmadas de roles/respuestas/DM/canal/edición/eliminación. Revalida permisos, condena activa y jerarquía; limita frecuencia en SQLite y conserva auditoría de resultados sin contenido durante 30 días. El primer fallo detiene la secuencia con resultado parcial; no hay reversión automática.
- Honeypot: texto y diseño proponen cambios sin persistir; sincronización después de confirmar. La fotografía de roles de condena se guarda antes de la operación remota.
- Pruebas locales finales: 106 offline (39 raíz + 67 tests), compilación, dependencias y diff correctos. Sin Gateway ni pruebas Discord reales. Consultar GitHub para el resultado de CI del HEAD publicado.
- PR #7 queda preparado para revisión de código; no equivale a alcance total completado ni a despliegue validado. Laboratorio sigue en 34fa94f; main permanece intacta en 6f9f9ee.
- Pendientes y recorrido reproducible en REVISION_PR7.md. Prioridad: configuración heredada sin confirmación, archivo integral de purgas, restauración parcial; después catálogo uniforme y mejoras de importación/navegación. Agent AVD no identificado inequívocamente.

## Actualización comprobada — Auditoría de seguridad (2026-10-11)

- Rama de trabajo: `fix/auditoria-seguridad-pr7-20261010` (PR #10 basado en PR #7), revisada hasta `c3896d7`.
- Confirmación explícita y revalidación en comandos heredados: Honeypot (`setup`, `resume`, `add`, `create`, `remove`, exenciones), Verificación (`/verify_setup`), Join Roles (add/remove/user_add/user_remove), Raid (`setup`), Sugerencias (destinatarios y panel), Miembro de la Semana (horario y canal), canal de Logs y canal de condenas.
- Moderación: registro de IDs de roles que no se pudieron restaurar; canal de archivo de evidencia restringido por permisos reales de roles y excepciones de miembros; no archivado si no se garantiza privacidad.
- GitHub Actions: ejecución `38146125476` **SUCCESS** sobre `c3896d7`; matrices Python 3.11, 3.12 y 3.13, con 35 pruebas de raíz, 85 en tests y 4 de logs por cada runtime según registros del job consultado.
- Fallos intermedios detectados y corregidos: clases de modales/vistas retiradas accidentalmente por cambios de código, mocks incompletos y aserciones antiguas incompatibles con guardado confirmado. El último CI correcto no garantiza funcionamiento interactivo.
- Railway laboratorio antes de integración: último despliegue observado `Pruebas@34fa94f`; las correcciones del PR #10 **no estaban desplegadas** al registrar este estado.
- **Pendiente antes de producción:** revisión y merge controlado a `Pruebas`, arranque/despliegue en Railway Test, validación real por un administrador en Heraldo's Lab y cierre del flujo operativo de roles no restaurados. Mensajes/Sapphire mantiene las fases incompletas descritas en `PLAN_MENSAJES.md`. No afirmar acabado todo el alcance.

## Integración en laboratorio y siguiente mejora — 2026-10-11

- GitHub: PR #10 fusionado en `Pruebas` mediante `d190c11a95`, incorporando PR #7. Ambos figuran como fusionados. `main@6f9f9ee0a7` sin cambios.
- CI tras integración: `Heraldo Lab - Python regressions` y `Mensajes - verificación de regresiones` **SUCCESS** para `d190c11a95`.
- Railway (proyecto aislado El Heraldo Test): despliegue de `Pruebas@d190c11a95` **SUCCESS** el 2026-10-11. Logs del despliegue: Discord Gateway conectado, autoprueba `/setup` correcta en Heraldo's Lab y El Heraldo Test conectado. Esto **no prueba clics reales**.
- Rama siguiente: `fix/recuperacion-roles-pendientes-20261011` / PR #11 (borrador): guarda por servidor y miembro los roles faltantes tras liberar condena, añade `/restaurar_roles_pendientes` con confirmación administrativa, comprobaciones de jerarquía, permisos y condena activa; aún no desplegado en laboratorio.
- Pendientes: pruebas interactivas de módulos modificados; accesos y retención del archivo de evidencia; funcionalidades avanzadas de Mensajes/Reaction Roles según plan; aprobación explícita antes de cualquier actualización de producción.


## Auditoría integral retomada — 2026-10-11
- Estado verificado: Pruebas a659b28, main 6f9f9ee intacta; PR #7/#10/#11 fusionados, #12 a260fec8 en borrador con CI correcta. Railway Test a8314dd2 sobre a659b28 SUCCESS, Gateway/autoprueba correctos. No acredita interacción humana.
- Rama nueva codex/auditoria-integral-20261011 sobre #12; conserva el historial local anterior. Inventario y matriz en audit/, con responsabilidades, hallazgos, propuestas y plan de servidor real sin autorización.
- Cuatro correcciones: navegación real de setup (Button no invocable), etiqueta inicial de aislamiento aceptada por el modal, permisos revalidados al enviar ese modal, defer antes de consultas/asignación en restauración pendiente. No duplica implementación de #10/#11.
- Verificación local: 144 pruebas (39 + 105), compilación, pip check y diff correctos. Pruebas de evidencias ahora comprueban ejecución y efectos, además de las comprobaciones estáticas preexistentes.
- Auditoría global en curso: no se acredita cada callback en Discord; quedan riesgos de purgas/retención, operaciones interrumpidas y respaldo SQLite. No se integra ni despliega este corte hasta revisión. Ver audit/AUDITORIA_2026-10-11.md.


## Duplicación de expulsión por verificación — 2026-10-11
- Captura aportada por el propietario: dos registros de expulsión por falta de verificación para el mismo miembro. No se almacenan sus datos ni la captura en el repositorio.
- Causa reproducida: evaluate_verify_timeout y evaluate_sin_verificado podían ejecutar cada uno kick y log; la resolución de uno no cancelaba el pendiente del otro.
- Corrección en la rama de PR #13: bloqueo común por servidor/miembro, lectura del estado persistido y resolución conjunta de ambos pendientes en una escritura SQLite. El respaldo delega al flujo principal cuando existe, respeta ban/solo registrar y el plazo vigente. Conserva respaldo independiente para ingresos con solo Sin Verificar.
- Un fallo HTTP conserva pendientes; solo un éxito genera el registro de expulsión. Miembros ya verificados y temporizadores antiguos no sancionan.
- Verificación actual: 155 pruebas offline aprobadas (39 + 116), compilación y diff correctos. No desplegado ni probado interactivamente por Codex. La captura acredita una observación del propietario de la versión anterior, no el resultado de la corrección.

## Continuación autorizada — H-01, 2026-10-11
- Base remota verificada: Pruebas@da551f3; main@6f9f9ee intacta. Copia limpia el-heraldo-pruebas; se conserva la copia local divergente anterior. No se crearon ramas.
- H-01: tres regresiones recibidas aprobadas; añadidas dos regresiones de ejecución/normalización. Línea base completa: 158 pruebas offline aprobadas (119 + 39).
- CI de da551f3: dos workflows SUCCESS. Railway Test: despliegue 712214ac SUCCESS de ese SHA. Volumen /data de 500 MB; sin buckets observados. No demuestra respaldo externo ni pruebas interactivas.
- Sin conector Obsidian disponible: continuidad mediante Markdown de GitHub. H-02 y H-03 pendientes; continúan las etapas D–G.

## H-02: barrera de conservación — 2026-10-11
- Purga general, condenas, reportes, Honeypot (incluidos mensajes durante otra sanción) y raid pasan por archivo individual antes del borrado. Baneos usan delete_message_seconds=0; la purga configurada se ejecuta separadamente con archivo.
- evidence_archive.py conserva JSON íntegro y adjuntos en el canal privado de Logs existente; verifica tamaño y SHA-256 leyendo cada copia desde Discord. Ledger SQLite durable y exclusión por mensaje: una interrupción incierta bloquea reenvío/borrado. Condenas conservan el contrato de referencia y texto, sin migrar expedientes previos.
- Si no hay intent de contenido, canal privado, permisos o copia íntegra, no se borra. Archivos superiores al menor límite de Discord/25 MiB, stickers, encuestas y mensajes reenviados quedan conservados en origen. No se crearon almacenamiento ni credenciales.
- Se vuelve a leer el origen para detectar ediciones y comprobar privacidad antes del borrado. Discord no ofrece transacción atómica entre edición, permisos y delete: queda una ventana remota mínima y requiere validación humana. Una copia borrada/corrupta o ledger pendiente exige revisión; no se reintenta un envío incierto automáticamente.
- Pruebas base tras integración: 129 tests y 39 raíz/Logs correctos; añadidas luego tres comprobaciones de roles, excepciones individuales y formatos no soportados. El primer ensayo detectó conexiones SQLite sin cerrar; corregidas con cierre explícito.
- Discord real: no realizado. Pendiente validar CI/Railway del nuevo SHA y copia/recuperación en laboratorio. H-03 y etapas posteriores continúan pendientes.

## H-03 y revisión de continuidad — 2026-10-12
- Base remota comprobada `Pruebas@9502cea3e24099d9867484110adc3fe0872e737d`; `main@6f9f9ee` intacta. Trabajo en rama temporal exclusiva `codex/h03-recuperacion-20261012`, destinada a PR contra Pruebas; sin integración ni despliegue.
- IMPLEMENTADO y VERIFICADO AUTOMÁTICAMENTE: `sqlite_recovery.py`, CLI de respaldo online SQLite, integridad/FK/hash/esquema, publicación atómica privada, restauración offline con copia anterior y bloqueo cooperativo del bot, planificación de conservación sin borrado. Procedimiento, auditoría y límites en `RESPALDOS_RECUPERACION.md`.
- Revisión A–D: instantánea de mensaje fijada antes de esperar por archivo, guardas para restauración pendiente y confirmación de configuración caducadas; regresiones de modificación del objeto original, pérdida de copia e intent ausente. Las regresiones existentes de H-01, temporizadores, permisos, condenas y roles también pasaron.
- Revisión E: editor visual ofrece solo embeds existentes y selector de campos con valores precargados; conserva borradores, confirmación, permisos, límites de Discord y datos no editados. No completa catálogo, importación por enlace, editor de acciones ni toda la navegación pendiente.
- Validación F del lote: Python 3.12.14 / discord.py 2.7.1, 203 pruebas offline correctas (39 raíz/Logs + 164 tests), incluidas 23 H-03; compilación, pip check y diff check correctos. Bases temporales sintéticas, sin Gateway ni datos reales.
- PENDIENTE: GitHub API devuelve 403 del proxy de red; PR/CI no consultables aún. Sin herramientas/credenciales de Railway u Obsidian disponibles; estado Test actual no confirmado. Respaldo externo, programación, descarga/recuperación de archivos Discord y pruebas humanas no ejecutados. No declarar H-03 listo frente a pérdida total del volumen ni el bot listo para producción.
