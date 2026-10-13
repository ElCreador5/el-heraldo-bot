## Transferencia preventiva — preparación cron H-03 (2026-10-13)

**Estado de GitHub:** en `Pruebas` están `tools/scheduled_lab_backup.py` (commit `273b222bdda4a06c3e9a28bfd98dd438545a1a87`), `tests/test_scheduled_lab_backup.py` (`588469486030aaa5af1fbb54ea660840f67393ff`) y workflow de compilación (`7f8af99d06d53ea0ce940184e24dc3f580fb4bac`). No hay cron activo ni pruebas reales del nuevo servicio, solo tests escritos. Los tests originales de `backup_job.py` sí habían pasado antes (6/6).

**Bloqueo operativo:** al preparar el nuevo cron separado en Railway Test, la llamada de configuración `update_service` fue rechazada por controles de seguridad. **No eludir el bloqueo.** Se eliminó el servicio vacío en vivo, pero quedó una modificación de entorno **STAGED NO APLICADA** (patch `a2e93a6f-0cd3-410a-a854-cfd02699bbc7`) con creación de servicio/volumen de laboratorio, referencias a credenciales Test; no debe aplicarse. Las llamadas para eliminar los recursos que aún no estaban provisionados devolvieron `Service not found` y `Volume ... not provisioned`. El conector no ofrece descarte de cambios en borrador. Hay que revisar/desactivar ese borrador por el panel de Railway, sin afectar `worker`; comprobar posteriormente `pendingWork=0`.

**Continuar después del descarte:** validar CI y diseño del programador antes de habilitar cron. Los secretos de producción están fuera de Railway y de `main`, por lo que el trabajo de automatización de datos reales todavía requiere decisión y autorización separada. No afirmar que existen nuevas generaciones automáticas ni hacer cambios destructivos. Obsidian no conectado; se utilizó GitHub.

## Transferencia fase 1 H-03 — 2026-10-13

`Pruebas` recibió `backup_job.py` (commit `5df0f39a2e4b0d71064d79aa811901ca52a56532`), `tests/test_backup_job.py` (`85fe90f5bcb9ada7dec496cd9979ca64ef40786b`) y workflow compilación (`3f70f1e7c63c63f8830c6d04f470a57fd5a1aa1c`). Los **6 casos H-03 pasaron en Railway Test con dependencias reales**, transporte de red simulado, pre-deploy temporal retirado, despliegue `8e87b5b2-64c4-443e-bc38-0a4a67e44dba` `SUCCESS`, sin interacciones Discord. Documento operacional: `RESPALDOS_SUPABASE.md`. ChatGPT creó vigilancia diaria del bucket para avisar si la última copia productiva supera 36 h, falta o el acceso falla; no genera nuevas copias.

**NO HECHO**: ninguna activación de respaldos automáticos en el bot/producción, ninguna clave real de producción instalada en Railway, ningún backup adicional, ni cambio de `main`. Antes de producción: custodia independiente de clave, disparador confiable con acceso al volumen, política de alertas por fallo de job, capacidad ante pausa de Free, ensayos de restauración y autorización específica. Revisar PR #16 abierto y reconciliar HEAD `Pruebas` antes de integrar; no duplicar trabajos con Codex.

## Actualización H-03 — respaldo externo de producción (2026-10-13)

**REALIZADO SEGÚN INFORME DE CODEX LOCAL:** generada copia consistente SQLite mediante `Connection.backup` sin detener ni modificar el bot de producción. Se cifró externamente con AES-256-GCM usando clave distinta de la empleada en Test, se transfirió a Supabase con la cuenta técnica y se descargó, autenticó y restauró en SQLite aislada. El informe documenta integridad SQLite y claves foráneas correctas, coincidencia de esquema y contenido, prueba de rechazo de manipulación GCM y ausencia de cambios en producción. **Estas verificaciones de contenido/descifrado proceden del informe aportado por el propietario, no han sido repetidas por ChatGPT.**

**VERIFICADO INDEPENDIENTEMENTE POR CHATGPT (consulta 2026-10-13):** en Supabase Storage existe exactamente 1 objeto cifrado bajo la categoría de producción (100609 bytes) y 1 objeto de laboratorio; el bucket sigue privado y las políticas son solo INSERT/SELECT para usuarios authenticated restringidos por identidad. Railway producción sigue Online/SUCCESS con el despliegue anterior; Railway Test también Online/SUCCESS. No se leyó SQLite ni su clave, ni se modificó `main`.

**RIESGO PRIORITARIO:** la clave de descifrado de esta generación se conserva en un único equipo local según el informe. El propietario debe conservar una **segunda copia de la clave** en un medio seguro independiente (p. ej., gestor de contraseñas con recuperación u offline cifrado) y verificar acceso a ella. No publicar clave, rutas privadas, identificadores de generaciones, manifiestos ni datos en repositorio/Discord/chat. No repetir copia ni proceso de subida sin control de idempotencia; no hay aún protección continua.

**PENDIENTE:** periodicidad y supervisión de nuevos respaldos, política de conservación, segundo destino y disponibilidad ante pausas de Supabase Free, ensayos periódicos de restauración y cobertura independiente de adjuntos/evidencias externos de Discord. No implica autorización para desplegar `main`, restaurar producción ni ejecutar escrituras administrativas. Sin pruebas Discord en esta fase.

## Punto de control: H-03 Supabase real en Test — 2026-10-13

**HECHO:** ChatGPT agregó en `Pruebas` `tools/supabase_smoke_test.py` y corrigió `requirements.txt` tras dos builds fallidos por dependencia anidada de Railpack. Pre-deploy temporal de Railway Test creó base sintética, ejecutó H-03 backup, subió objeto cifrado, descargó y restauró, y contrastó el contenido. Resultado en logs `H03_SMOKE status=PASS scope=synthetic_no_discord`; despliegue `ef2cc191-accd-4b9c-8ab3-4d07acf9fc87` SUCCESS, 1/1 Online, un objeto en `lab/`. Pre-deploy temporal retirado (comando `python bot.py` intacto). Producción Online, sin modificación. No mostrar credenciales.

**PENDIENTE:** respaldo real de producción externo al volumen con verificación de descarga y recuperación aislada, espacio/cuota, monitoreo, retención no destructiva y Discord real; autorización específica antes de tocar main. PR #16 de Codex puede requerir reconciliación de nueva base de Pruebas; no sobrescribir cambios recientes. Plan Free puede pausar proyecto. Ver `ESTADO_PROYECTO.md`, `PRUEBAS_DISCORD.md` y `RESPALDOS_SUPABASE.md`.

## Transferencia Supabase H-03 — 2026-10-13

ChatGPT creó bucket privado en Supabase, escribió en Pruebas `supabase_backup.py`, `tests/test_supabase_backup.py`, `requirements-backup.txt` y `RESPALDOS_SUPABASE.md`, y amplió CI. Código aislado sin autoejecución ni acceso a producción. Codex continúa PR #16 sobre su rama temporal en paralelo: reconciliar cambios antes de integración; no sobrescribir Pruebas ni duplicar H-03. Faltan RLS de identidad técnica, credenciales privadas, subida/descarga real en Lab, respaldo recuperable de producción y autorización de main. **No declarar trabajo terminado ni verificado en Discord.**

# Continuidad entre agentes — El Heraldo

[[INICIO_OBSIDIAN]] · [[AGENTS]] · [[ESTADO_PROYECTO]] · [[DECISIONES]] · [[PRUEBAS_DISCORD]]

## Procedimiento de inicio
1. Leer [[AGENTS]], [[ESTADO_PROYECTO]], [[DECISIONES]], [[PRUEBAS_DISCORD]] y, si procede, [[PLAN_MENSAJES]].
2. Consultar ramas, PR y commits recientes en GitHub; no tomar por actual una nota anterior.
3. Consultar Graphify para orientar la exploración; confirmar el commit indexado (última referencia observada: `main@6f9f9ee`) antes de atribuir resultados a `Pruebas`.
4. Trabajar únicamente en rama de desarrollo autorizada. Mantener `main` sin cambios salvo autorización específica.
5. Al finalizar, actualizar los documentos pertinentes, registrar pruebas realizadas y guardar commits/PR; no afirmar que hubo guardado si faltan permisos.

## Protocolo compartido actual
- **Rama permanente de desarrollo:** `Pruebas`. Producción: `main`, protegida por autorización explícita. Desde 2026-10-12 Codex tiene permiso específico para ramas temporales de tarea con PR hacia `Pruebas`.
- Solo Codex puede crear ramas temporales de tarea y PR abiertos con destino `Pruebas`; no se autoriza modificar `main`. Revisar cambios y CI antes de integrar, tener presente Railway Test automático, y eliminar la rama temporal cuando se descarte o integre sin trabajo pendiente.
- **ChatGPT** recoge decisiones de producto y coordina; **Codex** se ocupa principalmente del código y auditoría; **Work** y **Claude** solo cuando exista una necesidad específica. El repositorio es el contexto compartido.
- Cada transferencia debe nombrar responsable siguiente, rama/commit, cambios reales, CI, pruebas reales Discord, riesgos y acción concreta.
- La sección siguiente conserva el informe recibido el **2026-10-10 como historial**: no es el estado actual de los PR ni de la rama `Pruebas`.

## Traspaso Codex → Claude → ChatGPT (informe recibido 2026-10-10)
**Origen:** informe de auditoría aportado por Claude a la conversación; sus resultados de ejecución se atribuyen a Claude, no han sido reproducidos al crear esta nota.

- PR #7: rama `codex/seguridad-mensajes-20261010`, HEAD `661da952a0`, destino `Pruebas@34fa94f0d2`.
- Claude indicó 106 pruebas offline aprobadas con Python 3.12.3 y CI remota satisfactoria en 3.11–3.13. **Pruebas Discord del PR #7: no realizadas**.
- A: comandos administrativos heredados con guardado sin confirmación o comprobación insuficiente de permisos.
- B: condenas finalizadas aunque algunos roles no puedan restaurarse, sin detallar cuáles en la notificación.
- C: canal de evidencias comprueba visibilidad de `@everyone` pero no otras vías de acceso; purgas amplias no archivan todos los mensajes.
- Claude no tenía escritura en GitHub. Su informe `INFORME_CIERRE_PR7.md` se entregó en la conversación y **no estaba persistido en el repositorio** al redactar esta nota.
- Documento del propio PR #7: `REVISION_PR7.md`, disponible **en la rama del PR**, no en `Pruebas` hasta integrarlo.
- Próximos hitos: resolver A/B/C según alcance y riesgo, integrar PR #7 en `Pruebas` tras revisión, pasar CI y pruebas interactivas autorizadas en Heraldo's Lab, y solo entonces preparar aprobación independiente de `main`.

## Plantilla para nuevas transferencias
- Fecha, agente y entorno:
- Rama, commit y PR:
- Objetivo:
- Cambios reales y rutas:
- Verificación automática (comandos y resultados):
- Verificación **real** en Discord:
- Riesgos/bloqueantes:
- Documentos actualizados:
- Trabajo local no guardado:
- Próximo paso concreto:

## Abrir en Obsidian
El repositorio contiene Markdown compatible con Obsidian. En el equipo local, clonar o actualizar la **rama deseada** en una carpeta y usar «Abrir carpeta como bóveda» sobre esa carpeta. No editar documentos de ramas distintas como si fueran una sola versión. No publicar `.obsidian/workspace.json`, configuraciones locales, secretos ni información sensible.

**Sincronización:** Obsidian no sincroniza automáticamente con GitHub, Graphify ni los chats. Guardar cambios mediante Git y PR revisado; resolver conflictos antes de actualizar la rama compartida.

## Punto de control Codex — 2026-10-11, H-01
- Pruebas remota da551f3, copia activa el-heraldo-pruebas. Copia el-heraldo-bot preservada: Pruebas local divergente, fetch genérico apunta a una rama eliminada; no mezclar historiales antiguos.
- H-01 validado con tres pruebas recibidas y dos nuevas pruebas runtime. Base: 158 pruebas, compilación y dependencias correctas. Railway Test 712214ac SUCCESS y CI correcto. Discord no realizado.
- Siguiente: archivo verificable de cada mensaje en purgas/Honeypot/raid; impedir borrado API en ban; después respaldo SQLite y evidencias. No hay acceso directo Obsidian; usar Markdown.

## H-02: barrera de conservación — 2026-10-11
- Purga general, condenas, reportes, Honeypot (incluidos mensajes durante otra sanción) y raid pasan por archivo individual antes del borrado. Baneos usan delete_message_seconds=0; la purga configurada se ejecuta separadamente con archivo.
- evidence_archive.py conserva JSON íntegro y adjuntos en el canal privado de Logs existente; verifica tamaño y SHA-256 leyendo cada copia desde Discord. Ledger SQLite durable y exclusión por mensaje: una interrupción incierta bloquea reenvío/borrado. Condenas conservan el contrato de referencia y texto, sin migrar expedientes previos.
- Si no hay intent de contenido, canal privado, permisos o copia íntegra, no se borra. Archivos superiores al menor límite de Discord/25 MiB, stickers, encuestas y mensajes reenviados quedan conservados en origen. No se crearon almacenamiento ni credenciales.
- Se vuelve a leer el origen para detectar ediciones y comprobar privacidad antes del borrado. Discord no ofrece transacción atómica entre edición, permisos y delete: queda una ventana remota mínima y requiere validación humana. Una copia borrada/corrupta o ledger pendiente exige revisión; no se reintenta un envío incierto automáticamente.
- Pruebas base tras integración: 129 tests y 39 raíz/Logs correctos; añadidas luego tres comprobaciones de roles, excepciones individuales y formatos no soportados. El primer ensayo detectó conexiones SQLite sin cerrar; corregidas con cierre explícito.
- Discord real: no realizado. Pendiente validar CI/Railway del nuevo SHA y copia/recuperación en laboratorio. H-03 y etapas posteriores continúan pendientes.

## Actualización de flujo Codex — 2026-10-12
- Autorización expresa del propietario: excepcionar la política anterior de dos ramas únicamente para ramas temporales de tareas Codex y PR a `Pruebas`; queda registrada en `DECISIONES.md` y `AGENTS.md`.
- `.codex/setup.sh` corregido: admite `work` interno, reporta SHA y divergencias respecto a `Pruebas` sin alterar ramas, y prepara dependencias con compilación; no inicia el bot.
- Los commits documentales en `Pruebas` pueden activar Railway Test. Prueba del script dentro de Codex y pruebas reales Discord: pendientes, no declaradas realizadas.
- Próxima tarea Codex: confirmar base del PR, ejecutar preparación y regresiones relevantes; someter PR a `Pruebas`. ChatGPT revisa resultado antes de integrar.

## Punto de continuidad H-03 — 2026-10-12
- Responsable: Codex. Rama `codex/h03-recuperacion-20261012`, base exacta `Pruebas@9502cea3e24099d9867484110adc3fe0872e737d`. El commit que contiene esta sección conserva implementación, regresiones y documentación; consultar `git log` para su SHA, sin atribuirle integración en Pruebas.
- H-03 local implementado y probado: respaldos online, WAL, integridad, manifiesto privado, restauración offline/rollback con bloqueo de servicio y plan de conservación sin borrado. Auditoría y procedimiento en `RESPALDOS_RECUPERACION.md`; 23 pruebas específicas.
- Continuación A–E: protección ante mensaje mutado mientras se archiva, solicitudes/confirmaciones caducadas y selección visual de campos/embeds. No se declaró terminada la auditoría funcional global ni las funciones restantes de `PLAN_MENSAJES.md`.
- Validación F: 203 pruebas offline (39 + 164), compilación y dependencias correctas en Python 3.12.14 / discord.py 2.7.1; sin Discord real, bases reales o despliegues. El primer fixture de permisos de H-03 se corrigió por umask, luego pasó.
- Git nativo funciona; GitHub API devuelve 403 del proxy. No hay conector Railway/Obsidian ni variables Railway/Discord inyectadas. No solicitar nuevos tokens GitHub por este bloqueo. El borrador cloud guardó instalación, instrucciones de inicio offline y `api.github.com`; requiere revisión/guardado y publicación del entorno para activar lo pendiente, no confirma acceso actual.
- Siguiente: habilitar API GitHub, comprobar PR/CI y Railway Test, preparar/revisar PR exclusivamente a Pruebas. Antes de integrar revisar cabeza remota y despliegue automático; no modificar main. Definir destino externo privado y recuperación de archivos de evidencia con el propietario; ensayar laboratorio antes de activar respaldos programados. Continuar editor de acciones, comparación/importación de kits, catálogo y auditoría de interrupciones, conservando prioridades A–F y sin presumir cierre global.

### Guardado remoto comprobado del lote
- Implementación y pruebas preservadas en `99c9853ca97aa48ad5293169ba8874b6d6312204`, publicado y verificado en `origin/codex/h03-recuperacion-20261012`. Árbol limpio tras commit; Pruebas sigue en `9502cea`, main en `6f9f9ee`.
- Se intentó `gh pr create` en borrador, base `Pruebas`, head `codex/h03-recuperacion-20261012`: falló con `Post https://api.github.com/graphql: Forbidden`. **No se creó ningún PR**. La propuesta explica H-03, las correcciones adicionales, 203 tests y las limitaciones; el cuerpo preparado está en `/tmp/heraldo-h03-pr.md` en esta instancia y puede reconstruirse desde este informe si no sobrevive.
- Próximo paso concreto tras habilitar el dominio: consultar primero si existe ya un PR de esta rama para evitar duplicados; crear o actualizar su borrador hacia Pruebas, consultar CI y Railway Test antes de proponer integración. No hay autorización implícita para modificar main o activar infraestructura externa.
