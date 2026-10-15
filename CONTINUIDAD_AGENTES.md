## Ajustes tras prueba Discord: borradores y tiempos cortos — 2026-10-15

Tras aviso del propietario, `Pruebas@b041993`: Formato de fecha ahora distingue explícitamente «Borrador SIN GUARDAR» al elegir desplegable y sigue pasando por Revisar y confirmar → Guardar cambios del flujo central; no persiste al seleccionar. Recordatorios personalizados aceptan `30s`, `2m`, `1h`, `14d`, con mínimo 10 segundos SOLO en Railway Test identificado por `RAILWAY_PROJECT_ID`; en otros entornos mínimo 1 día y segundos no admitidos. El planificador revisa cada 10 s para ensayos, mantiene reclamo SQLite antes de enviar y no publica sin activación confirmada. Pendientes: ejecutar regresiones automatizadas, validar integración en Railway Test y comprobar con Discord. No modificar main.

## Recordatorios de reportes y formato de fecha — 2026-10-15

Implementación autorizada en `Pruebas` (commits desde `99e72a4` a `b11313d`): `/setup` incorpora **Formato de fecha**, con selección Discord/día-mes-año/mes-día-año/ISO y confirmación central; las fechas históricas no se reescriben. `Moderación → Reportes → Recordatorios` contiene el texto explicativo aprobado, frecuencia diaria/semanal/14 días/mensual/personalizada, selector de día y hora de Santo Domingo, canal, fecha inicial escrita, vista previa, activación/desactivación y confirmación. Los recordatorios están desactivados por defecto y solo se dirigen al canal autorizado; el texto excluye WARN reservado a moderadores y la reacción especial de condena. El lazo de publicación reclama primero el siguiente vencimiento en SQLite antes de llamar a Discord para evitar reenvíos de resultado incierto, y no recupera en masa publicaciones omitidas tras reinicio. Se añadieron regresiones estructurales `tests/test_report_reminders_and_date_format.py` y autoprueba del layout de ambas vistas.

**Pendiente:** confirmar Railway Test SHA final, comprobar los tests (no ejecutados localmente porque la copia GitHub no se puede clonar desde el contenedor), ensayar fechas/frecuencias y permisos en Heraldo's Lab. El formato de fecha configurable aún no sustituye todos los usos preexistentes de `discord.utils.format_dt`; aplicar por módulo de forma no destructiva. La referencia dinámica de Sapphire no permitió recuperar su apartado específico, por lo que no se declara paridad. `main` intacta.

## Corrección final del panel de Reportes por pruebas de Discord (2026-10-15)

En `Pruebas`, `a6c4270` se desplegó con SUCCESS y logs de conexión Gateway/autoprueba de /setup. La configuración histórica de 4 reportes puede estar personalizada, por lo que no debe sustituirse en segundo plano. `f01caa0` añade aviso visible de ❗ ausente en el editor compacto y ofrece por defecto el emoji y etiqueta «Incumplimiento de reglas» al pulsar Añadir; si se confirma ese formulario, la regla nace con acción WARN, umbral 1 y sin purga, pero **solo Guardar cambios persiste**. `d38c39f`/`ffd7f8c` añaden regresiones estructurales. Pendiente validar el último SHA en Railway Test y aceptación del panel recién abierto en Heraldo's Lab. Las pruebas locales completas no se han ejecutado por no disponer de clone local; `main` intacta.

## Panel Reportes compacto — corrección tras prueba del propietario (2026-10-15)

La captura del propietario confirma que el editor /setup seguía reproduciendo las instrucciones largas del resumen de Reportes pese a las mejoras previas. Commit `78337fe` reemplazó en `HeraldoUserReportsSetupView._content` el resumen extendido por canal, número efectivo de reacciones y emoji de condena directa. Las acciones y umbrales detallados quedan en selector y Condiciones, eliminando duplicidad y truncamientos. Commit `01bdb7e` agregó regresión estructural. Los cuatro reportes observados en el servidor pueden corresponder a configuración personalizada, que NO debe ser sobrescrita al agregar ❗ por defecto. Pendiente comprobar despliegue Test del SHA final y prueba real del panel recién abierto. main intacta.

## Evitar ediciones duplicadas al arrancar — 2026-10-15

`Pruebas@82cb5fa`: `suggestions_startup()` ya reconcilia sugerencias en el inicio; `synchronize_published_panels(..., suggestions_already_synced=True)` evita volver a editar ese mismo panel en el mismo arranque. Fuera del arranque (p. ej. incorporación a un servidor), la función conserva la comprobación del panel registrado. Regresión estructural actualizada en `tests/test_published_panel_sync.py`. No se reescriben expedientes. Validación funcional y Railway Test pendientes para SHA final. `main` intacta.

## Preparación para ensayo Discord — protección de paneles (2026-10-15)

`Pruebas@fe246717`: al recuperar Orientación, la sincronización del arranque exige tarjeta existente y que el canal registrado coincida con el actual. Evita publicar por primera vez o trasladar/borrar tarjetas de forma automática. Regresión añadida a `tests/test_published_panel_sync.py`. Railway Test reportó SUCCESS en `253642cd` y conexión Discord; registró una referencia obsoleta de verificación en un servidor, sin publicar reemplazo. Los últimos commits siguen pendientes de desplegar y probar. **No se ha realizado prueba interactiva real de estos cambios ni una suite pytest** (el contenedor local no puede resolver github.com). Necesario comprobar SHA final antes de pedir aceptación al propietario. Producción `main` intacta.

## Nuevo servidor: reconciliación de paneles existentes — 2026-10-15

`Pruebas@f93b68c`: el evento `on_guild_join` invoca `synchronize_published_panels` para referencias existentes, sin crear publicaciones al carecer de referencias. La reconciliación del arranque ya cubre Verificación, Sugerencias y Orientación; la migración virtual de ❗ se limita a reglas antiguas sin personalizaciones. Tests estructurales añadidos; aún no ejecutados en ambiente externo. La sesión local no puede clonar GitHub desde el contenedor por fallo de resolución de DNS, por lo que no atribuir resultados de compilación o pytest. Revisar CI y Railway Test al SHA final. `main` intacta.

## Sincronización continua — segunda etapa (2026-10-15)

En `Pruebas` los commits `289481a`, `4a2be42`, `1b0b830`, `c7a13cd` y `9836491` amplían la reconciliación del arranque a paneles publicados de Verificación, Sugerencias y Orientación usando sus referencias y funciones existentes; se evita repetir la reconciliación de Orientación dos veces. `tests/test_published_panel_sync.py` incorpora regresiones estructurales. El resumen de Reportes ya elimina texto obsoleto; para configuraciones heredadas exactamente iguales a los cuatro valores predeterminados anteriores, `moderation_report_reactions` incorpora virtualmente ❗ en la lista efectiva. No toca listas personalizadas ni realiza escritura en SQLite durante la lectura. **Pendiente ejecutar regresiones y comprobar en Discord**; Railway Test puede desplegar automáticamente, no equivale a aceptación. Cobertura general de otros embeds aún incompleta. `main` no modificado.

## Sincronización de verificación ampliada — 2026-10-15

Commits `3bd7cb7` y `96a83d7` en `Pruebas`: la confirmación central de configuración llama ahora a `update_verify_panel` ante cambios de `verify_enabled`, `verify_role_id`, `verify_timeout`, `verify_action` además de los textos/etiqueta existentes. El nombre correcto de la clave es `verify_timeout` (no `_seconds`). El panel publicado se edita por referencia persistida; no se vuelve a publicar y no toca expedientes. Pendientes: pruebas automáticas y reales, inventario del resto de paneles dinámicos y hooks equivalentes. Sin cambios en `main`.

## Sincronización automática de paneles — primera etapa (2026-10-15)

Autorización del propietario: actualizar paneles dinámicos al cambiar configuración, al desplegar cambios de texto y tras reinicio, conservando personalizaciones; NO reescribir expedientes/evidencias/registros históricos ni duplicar mensajes. `Pruebas@b064757`: se incorporó en el arranque la reconciliación del panel persistente de verificación por referencia guardada; el panel de sugerencias ya se restaura y edita mediante `suggestions_startup` / `suggestion_ensure_panel`. Los paneles efímeros de /setup se reconstruyen al abrir. **Cobertura global incompleta**: inventariar módulos y sus IDs persistidos, añadir hooks de guardado y regresiones. Sin pruebas automáticas o de Discord de esta etapa todavía; comprobar Railway Test. `main` no modificada.

## Confirmación legible y aviso de laboratorio por DM — 2026-10-15

Commits `c644354` y `4bce296` en `Pruebas`: se sustituyeron secuencias literales `\\n` por saltos de línea reales en la confirmación de `/setup` (problema visible en captura). Los DM de expedientes de moderación, tarjetas de condena y perdón reciben un campo formal de aviso de pruebas solo cuando `RAILWAY_PROJECT_ID` corresponde al proyecto Railway Test; el embed se copia para no contaminar el expediente publicado en canales. No se modificó `main`, ni las notificaciones en otros entornos. Pendientes: verificar presencia real de `RAILWAY_PROJECT_ID`, pruebas automatizadas y prueba interactiva de los tres flujos en Heraldo's Lab; ampliar revisión de otros DM según alcance.

## Ajustes visuales de Reportes — 2026-10-15

`Pruebas@4492a536`: botones «Emoji de condena directa», «Condiciones» y «Advertencias y sanciones» aclaran la diferencia entre condena especial por reacción y reglas de reportes. El texto del editor separa los pasos de las opciones independientes y muestra estado de cambios sin guardar cerca del comienzo. Guardar/Descartar se deshabilitan si los valores del borrador equivalen a los originales; el guardado conserva sus validaciones existentes. Commits `9fa08ab` y `4492a536`, archivo `bot.py`. **Verificación automatizada y real en Discord pendiente**; Railway Test se autodespliega de Pruebas y requiere comprobar su estado. No se modificó `main`.

## Continuidad — política de sanciones por reacción y escalamiento WARN (2026-10-15)

Última petición: mejorar claridad de los editores y poder desactivar/activar las acciones (Advertir, Aislar, Expulsar, Banear, Condenar) y seleccionar acción cuando un usuario alcanza máximo de advertencias (3/3 por defecto, límite 5). En `Pruebas`, se implementó `HeraldoWarningLimitSelectView` con 4 selects + revisión y cancelación; flags `moderation_reaction_*_enabled`, `moderation_warn_limit_action` y `moderation_warn_limit_mute_minutes`. Default de escalamiento Solo avisar; acciones no habilitadas no se ejecutan. Se añadió tabla SQLite aditiva `moderation_warn_escalations`, reclamo único y estado fail-closed de acciones para no repetir una sanción incierta. `/warn` y ❗ comparten el máximo; DM de WARN antes de escalamiento. `ModerationReactionRuleModal` usa etiquetas claras y oculta campos irrelevantes, selector de acción ahora está junto a reacción y botón se llama Configurar condiciones; `moderation_can_condemn` revalida privilegios/jerarquía para condena por reacción. `tests/test_moderation_reaction_policy.py` prueba despachos simulados y se actualizaron regresiones anteriores. Al terminar: consultar logs de ejecución de pruebas, limpiar `preDeployCommand` temporal del worker de Railway Test y comprobar estado, documentar resultados reales. **Discord interactivo no probado**; no modificar `main`. Próximo paso: pruebas de aceptación en Heraldo's Lab y auditoría de editores restantes usando el mismo lenguaje claro sin reescrituras globales ni sobrescribir cambios concurrentes.

## Continuidad — máximo de advertencias vigente (2026-10-15)

Petición del propietario: sistema de máximo configurable para WARN, default 3/3 y tope configurable 5/5. Comprobado que `/warn`, expedientes y `/advertencias` existían, pero no un límite configurable. Implementación en `Pruebas`: `moderation_warning_create` y guardia de `moderation_report_case_record` en SQLite transaccional, consulta de vigentes y máximo por servidor, selector `HeraldoWarningLimitSelectView` en Moderation → Reportes, mensajes de conteo en DM/log y consulta. Sin sanción automática al llegar al tope, se bloquean nuevos WARN y se preservan anteriores. Actualizada suite aislada de reacción y nueva `tests/test_moderation_warn_limit.py`. Revisar pruebas y despliegue Railway Test HEAD y limpiar `preDeployCommand` temporal al finalizar. Casos WARN sin estado expirado no se borran; expirados dejan de contar, aunque su fila esté pendiente de cierre programado. Queda validar acciones reales en Heraldo's Lab. `main` intacta.

## Transferencia — mejoras de acciones por reportes (2026-10-15)

En `Pruebas` se detectó que timeout/kick/ban por reportes actuaban sin expediente, podían anunciar otra purga exitosa independiente y timeout sin duración usaba valor implícito. Se agregó tabla `moderation_report_cases` y registro de caso idempotente después de sanción, verificaciones de permisos y duración, reducción del doble log y avisos de editor para umbral 1. Nuevas pruebas: `tests/test_moderation_report_actions.py`. No se reconfiguraron reglas persistidas ni se tocó main. Comprobar estado del despliegue Test y pruebas; retirar **preDeployCommand temporal** de Railway Test si aún consta. Seguimiento: revisar reintentos tras fallos intermedios Discord/SQLite, seguridad de reportes maliciosos y evidencia verificable vinculada a casos sin transformar enlaces de mensajes en pruebas duraderas; Discord Lab pendiente.

## Continuidad — selectores de los editores /setup (2026-10-15)

Encargo del propietario: modernizar editores, conservar lo existente y eliminar escritura manual de opciones cerradas. En Pruebas se incorporaron HeraldoMotwScheduleSelectView y selector de acciones de reportes dentro de HeraldoUserReportsSetupView; ModerationReactionRuleModal conserva únicamente parámetros libres. Borradores no persisten al seleccionar; Guardar exige reglas válidas y permisos vigentes, con comprobación optimista de cambios concurrentes (MOTW y Reportes). Dos tests nuevos: tests/test_setup_editor_selectors.py y tests/test_editor_drafts_behavior.py. Comprobar CI/compilación en HEAD, Railway Test y test real en Heraldo's Lab; nunca afirmar lo último sin interacción autorizada. La tarjeta de condena, main y producción quedan fuera del alcance. Próxima etapa: probar los selectores y continuar con otros editores, especialmente la navegación visual de Mensajes, sin duplicar implementaciones ni reescribir módulos estables.

## Confirmaciones legibles de /setup — 2026-10-15

Petición del propietario: eliminar el adjunto técnico `propuesta.json` de `/condenar_setup` y casos similares. Detectada función central `confirm_configuration` utilizada por aproximadamente 30 rutas. En `Pruebas`, se sustituyó el archivo JSON por embed efímero con etiquetas, valor actual y propuesto; valores de ID de canal/rol/miembro se resuelven cuando sea posible, y se excluyen cambios idénticos (sin ofrecer guardar). Se conserva `ConfigurationConfirmView`: permisos y revalidaciones, control transaccional SQLite, Guardar y Cancelar. Regresión estructural: `tests/test_configuration_preview.py`. Se preservan exportaciones de kits JSON cuando son una funcionalidad explícita de importación/exportación (no una confirmación). Se requiere comprobar CI del commit, ejecución real en Heraldo's Lab y posibles campos adicionales que precisen etiquetas específicas. `main` intacta.

## Segunda etapa de desplegables — Reaction Roles (2026-10-15)

Se amplió la petición general de opciones elegibles: en `Pruebas`, Reaction Roles → Opciones usa selectores para acceso, invertidas y máximo; aplica al borrador y requiere Guardar posterior, con Descartar explícito. Regresiones en `tests/test_reaction_options_dropdown.py`. No tocar `main`. Pendientes otras configuraciones textuales con elecciones cerradas; priorizar opciones reales sin convertir títulos, URLs o motivos libres en desplegables.

## Continuidad — expedientes con conversación privada + selectores (2026-10-15)

Petición expresa del propietario: mantener sin cambios diseño de los embeds de condena, mencionar al condenado en el canal; una vez publicada la tarjeta, crear hilo privado por expediente para el miembro y administración, con enlace desde la tarjeta; cerrar al perdonar. Hilo privado no puede nacer directamente del mensaje en la API; se crea separado. Discord no oculta tarjetas distintas a quienes pueden leer historial en canal común. Desarrollo solo en `Pruebas`, con cambios en bot.py y tests/test_condemnation_private_threads.py; base de datos migra aditivamente, los errores no deben cancelar una condena válida. /setup Condenas suma «Preparar acceso» con confirmación y selector de duraciones frecuentes con opción personalizada, primer paso de la petición más amplia de desplegables. Verificar CI para SHA del commit, estado Railway Test y prueba real con bot de laboratorio; no desplegar `main` sin permiso expreso. Otros módulos de selección siguen pendientes; evitar crear ramas o duplicar investigaciones.

## Punto de continuidad — doble aviso de condena/purga (2026-10-15)

Petición del propietario basada en captura del bot oficial. Se localizó que `_condemn_member_inner` publicaba «Condena aplicada» mientras `run_purge_job` publicaba, posteriormente, «Purga de condena completada». Implementación acotada en `Pruebas`: conservar un único embed principal, editarlo con cantidades reales tras la purga; cuando no haya log principal o falle editarlo, emitir aviso alternativo, sin silenciar auditoría ni errores. No se eliminan eventos distintos de evidencia privada ni perdón. Regresiones específicas añadidas. `main` y producción permanecen intactos. Siguiente paso: comprobar GitHub Actions de SHA exacto, Railway Test y aceptación real autorizada en Heraldo's Lab; solo con autorización específica preparar integración a `main`.

## Transferencia auditada — Claude/ChatGPT 2026-10-14

Se conservó auditoría independiente en [`audit/AUDITORIA_INTEGRACION_2026-10-14.md`](audit/AUDITORIA_INTEGRACION_2026-10-14.md). Estado previo de `Pruebas`: `1eebcce77b346c8c40762b2c8bece4dfb220fb3e`; `main`: `6f9f9ee0a7ed1c7b7e6c48a13817b9b5f3a5b667`; 192 commits de diferencia. Commit `203ea14a` **existe** como objeto sin rama, pero es más amplio que candidato H-03 mínimo validado por Claude y necesita CI propio. **Sin PR nueva, sin merge y sin cambios en producción**. Siguiente decisión: autorización expresa para crear una única rama temporal y PR a `main` con commit de lanzamiento, sin arrastrar `Pruebas`.

## Preparación sin despliegue y recuperación aplazada — 2026-10-14

El propietario aplaza hasta noviembre de 2026 la verificación independiente de Bitwarden. Existe una nota privada importada con la clave original, pero NO se ha probado su recuperación/descifrado desde una sesión o dispositivo independiente ni la recuperación de acceso a la bóveda. No tocar la clave, no repetir la importación y no ejecutar operaciones productivas que dependan de ese requisito. Esto permite seguir preparando y verificando código con datos sintéticos.

Base de trabajo: Pruebas 13af6c31fc97e8528bf03e571305b9c6b688a539. Main sigue 6f9f9ee0a7ed1c7b7e6c48a13817b9b5f3a5b667. Producción SUCCESS en bbb21914-a87c-44f3-b862-f4ba3ceecd09, sin cambios pendientes. Test SUCCESS, start python bot.py, preDeploy vacío; no se cambiaron sus secretos ni configuración para ejecutar pruebas.

Defecto corregido en backup_job._isolated_restore: SQLite creaba el destino con permisos dependientes de umask (habitualmente 0644). Ahora se reserva con O_EXCL/O_NOFOLLOW y modo 0600 antes de abrir SQLite; no se cambia umask global desde el hilo del bot, ni se sobrescribe un destino existente. Dos regresiones nuevas verifican privacidad con umask 022 y conservación del archivo existente.

Verificación Linux aislada en Railway Test: compilación, pip check, 39 regresiones históricas y 218 de tests/ aprobadas (257). Transporte simulado, sin credenciales en el proceso hijo, sin importar/iniciar el bot para operar Discord. Warnings no fatales preexistentes en mocks. No son pruebas humanas Discord ni prueba productiva.

Siguiente etapa realizada: tools/prepare_h03_candidate.py construye en directorio NUEVO un candidato basado exclusivamente en main fijo, añade cuatro módulos H-03 y cryptography, e inserta un hook protegido por bandera antes de importar dependencias. Una comparación AST comprueba que el resto de bot.py es idéntico. No crea ramas, no publica main ni despliega. La primera ejecución local encontró un error de indentación del comprobador; corregido y candidato válido generado en otro directorio, conservando el anterior.

Candidato ensayado en proceso aislado de Railway Test: 29 regresiones históricas disponibles en main, compilación y dependencias correctas; extracción AST de db_connect/db_init sin ejecutar el módulo del bot, creación de esquema sintético de main, fila sintética, inicialización candidata, backup y restauración nueva y vuelta a inicialización main. Esquema y contenido coinciden; H03_CANDIDATE_PASS. Programador sin bandera no inicia. Ninguna migración nueva se incorpora al candidato. Esto valida compatibilidad sintética del cambio mínimo; NO sustituye instantánea productiva reciente ni aceptación funcional real antes de desplegar.

Pendientes: recuperación independiente en noviembre, alerta con entrega comprobada, auditoría final de candidato/credenciales y nueva instantánea justo antes del futuro despliegue autorizado. El PR 16 no se integró. No hay respaldo diario real de producción activado ni borrado de copias. Revisar CI y autodespliegues del commit de esta etapa antes de atribuirles éxito.

## Transferencia H-03 — 2026-10-14, autorización condicionada de producción

**Rama `Pruebas`:** se incorporó `production_backup_scheduler.py` (cron interno opt-in al primer `on_ready`; horario 06:15 UTC, I/O en hilo, revalidación diaria), parche mínimo de `bot.py`, 10 tests y compilación en CI. En Railway Test: pruebas 10/10 del scheduler, 216/216 suite `tests/` y 39/39 regresiones históricas `OK` tras corregir un patrón shell de la prueba (fallo inicial documentado). Worker Test/cron Lab siguen como sistemas separados, sin habilitar respaldos reales. Comandos temporales retirados. Commits hasta `bef4daca1101edbbd7211cde16532b45abb712d7` más documentación.

**Bloqueo verificable de producción:** `main` continúa en SHA `6f9f9ee0a7ed1c7b7e6c48a13817b9b5f3a5b667`; servicio productivo solo publica nombres de variables DB_PATH, DISCORD_TOKEN y MESSAGE_CONTENT_INTENT. No se han configurado Supabase técnicos, key AES, cuota, ni bandera; la única clave del objeto productivo anterior está custodiada localmente según informe de Codex, sin segunda copia externa verificable. **No se desplegó main** porque el permiso del propietario exige antes pruebas/reversión/custodia. Se necesitan Codex local o intervención autorizada en el equipo propietario para respaldar la clave y verificar recuperación, luego preparar revisión mínima main/candidato y nueva snapshot.

**Próximo paso concreto:** seguir `AUTOMATIZACION_H03.md` sección de activación escalonada. No fusionar todo Pruebas a main ni subir secretos. Comprobar disponibilidad y alertas: monitor ChatGPT ejecutado con notifications_enabled=false y email_enabled=false, no garantiza recepción. No se consultó Obsidian por falta de conexión. Sin pruebas reales Discord en esta fase.

## Continuidad H-03 — capacidad finita protegida (2026-10-14)

- `Pruebas`: `backup_job.py` commit `24489e02204a7004e59f074f9750e0ab69443680`; `tests/test_backup_job.py` commit `28a4063fa0f00ed0f6e32e0b1902cfa0c1db155f`. Preflight de espacio >= tres instantáneas +64 MiB, cuota opcional `HERALDO_BACKUP_VOLUME_CAP_MB`; sin borrado automático.
- Test: 10/10 regresiones OK en Railway, despliegue `431d16b9-68a4-4b88-af47-9e0bc1fdd771` SUCCESS; el comando temporal pre-deploy retirado. Configurada cuota `HERALDO_BACKUP_VOLUME_CAP_MB=500` **solo en cron de Railway Test**; comprobar próxima ejecución programada tras el cambio, sin repetir hoy la copia. Worker Test conserva arranque `python bot.py`; producción/main intactos.
- Próxima tarea: umbrales con alerta fiable, segunda custodia de clave productiva y arquitectura de ejecución sin compartir volumen ni depender de PC apagado. La activación real de producción sigue requiriendo autorización focalizada. Ni copias ni claves privadas se subieron a GitHub, y no hay pruebas Discord en esta fase.

## Punto de control H-03 — validación de recibos y limitaciones de alertas (2026-10-14)

- **Rama:** `Pruebas`. Se corrigió verificador `tools/backup_health.py` y actualizó `tests/test_backup_health.py`; commits `78f31a1dab1c1c9f8da49e746f4b6421de4915b3` y `1d3581bfcea47a81139d6d2c9e8a30b32fec865e`.
- **Automático verificado:** `python -m unittest discover -s tests -p test_backup_health.py -v` (14/14 OK) en pre-deploy efímero de Railway Test; despliegue `85eeacfb-63a7-4c56-ad9b-939882446fcd` SUCCESS. Eliminado pre-deploy; `worker` Online y cron Lab `cronReady`, staged vacío. `main` y producción intactos. Discord real no ensayado.
- **Detectado:** ChatGPT monitor diario de producción tiene `notifications_enabled=false` y `email_enabled=false`: configuración programada/ejecutada NO garantiza entrega de avisos. Codex Lab monitor local tampoco prueba entrega. No activar backups reales sin respaldo independiente de clave, capacidad, ejecutor fiable y autorización específica. Respaldo productivo externo existente no duplicado ni modificado.
- **Próximo paso de implementación:** revisar arquitectura de ejecución en el servicio propietario de `/data` o lanzador externo siempre disponible sin duplicar bot; asegurar gestión de clave y recuperación independiente, controles de cuota y límite, alertas comprobadas; preparar plan de reversión y solicitar permiso focalizado antes de tocar `main` o Railway producción. Revisar PR #16 antes de integrar cambios. GitHub es fuente principal; Obsidian no conectado.

## Automatización H-03 verificada en laboratorio — 2026-10-14

Código de ejecución publicado en Pruebas: cf9f2da77406dd79a6abf254fe445e3092a3bb4f, sobre e59bb4f. Main y producción conservan 6f9f9ee0a7ed1c7b7e6c48a13817b9b5f3a5b667. Sin ramas nuevas ni PR; PR #16 no integrado. Checkout anterior divergente preservado.

Servicio independiente heraldo-h03-lab-cron en Railway Test, volumen privado propio de 500 MB, sin DISCORD_TOKEN ni DB_PATH, seis referencias de secretos exclusivamente Lab. Worker conserva python bot.py y preDeploy vacío, SUCCESS y conectado al Gateway. No hubo cambios funcionales en bot.py ni configuración del worker.

**Ejecución programada real:** 2026-10-14 14:15:04–14:15:13 UTC (10:15 local), run 71b4b38d-f85c-4ca2-bb55-fc3a8224955e, despliegue dc2cedd1-e0d7-42f4-bc8d-3012a1dc84a4. VERIFIED_AND_RESTORED a las 14:15:07, H03_HEALTH OK, proceso EXITED. La frontera de activación bloqueó el respaldo durante el despliegue inicial: la primera transferencia completa fue del programador, no manual. SQLite sintética, API backup, AES-256-GCM, subida/descarga autenticadas, SHA-256, integridad/FK y restauración aislada con esquema/recuentos/contenido coincidentes. Supabase pasó de 1 a 2 objetos Lab: solo una generación nueva de 782 bytes cifrados. La generación productiva existente no cambió.

**Persistencia/duplicados:** segunda ejecución manual del cron a las 14:15:44 UTC en contenedor nuevo: ALREADY_ATTEMPTED no_retry=true, H03_HEALTH OK y proceso terminado. Sin nueva subida. No confundir esta segunda invocación manual con el disparo programado anterior. Recibos y generaciones permanecen privados en el volumen.

**Pruebas:** 39 + 195 = 234 regresiones offline en proceso Linux aislado de Railway Test, compilación y pip check aprobados; transporte simulado, sin iniciar Discord. CI del commit cf9f2da: workflows Mensajes y Heraldo Lab aprobados (runs 38577334609 y 38577334553). Prueba negativa real contra Supabase con API key inválida solo en proceso efímero: acceso denegado antes de subida, recibo needs_manual_review, segundo intento bloqueado. Corrupción GCM y clave incorrecta rechazadas con datos sintéticos. Períodos omitidos, fallos, fecha futura y antigüedad desde finished_at cubiertos por regresiones. Logs operativos inspeccionados: solo estados/fechas, sin secretos, filas ni manifiestos. Warnings no fatales preexistentes en mocks SQLite/discord.py; no pruebas humanas Discord.

Horario diario configurado: 06:15 UTC / 02:15 America/Santo_Domingo; se aplica con el despliegue de este commit de cierre y se verifica después. Vigilancia local Codex diaria 08:00, solo Lab, deduplicación por incidencia; depende del equipo/Codex. Vigilancia productiva previa de ChatGPT no modificada. Primer disparo futuro del monitor pendiente: no se afirma entrega de alertas probada.

Producción NO automatizada. Procedimiento, límites y autorización pendiente en AUTOMATIZACION_H03.md. Segunda custodia de clave productiva y ejecutor continuamente disponible siguen pendientes; no se movió la clave. No se borraron respaldos, registros ni datos. Obsidian sin conexión.

## Punto de control H-03 — Railway Test limpio y pruebas del cron, 2026-10-14

**Rama:** `Pruebas`. **Resultado:** el propietario descartó íntegramente el patch de Railway Test que había quedado en borrador (confirmado `staged=null`). ChatGPT ejecutó temporalmente la nueva suite `tests/test_scheduled_lab_backup.py` en el `worker` mediante pre-deploy no destructivo: `Ran 6 tests`, `OK`; despliegue Test `7fd7ace1-2fa6-40ff-8548-5517cd199561` SUCCESS/Online. Configuración restaurada a `startCommand=python bot.py`, `preDeployCommand=[]`; no quedan cambios pendientes de Railway.

**No realizado:** cron activo real, acceso automático a datos de producción, protección de clave duplicada, pruebas Discord, edición de `main` o cambios de despliegue productivo. Módulos existentes: `backup_job.py`, `tools/scheduled_lab_backup.py`, y suites `tests/test_backup_job.py`/`tests/test_scheduled_lab_backup.py`.

**Siguiente paso:** diseñar/programar activación en laboratorio sin incorporar `DISCORD_TOKEN` al servicio cron. Nunca presuponer que Railway deja montar un mismo volumen SQLite simultáneamente en dos servicios. Si se elige integración en el proceso actual del bot, requiere revisión de errores/reinicio/secretos y nueva autorización antes de modificar `main`. Preservar copia/clave existentes. Obsidian no conectado.

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
