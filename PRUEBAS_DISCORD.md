## Registro único de condena con purga — 2026-10-15

**DETECTADO (captura oficial + código):** el mismo proceso de condena con purga publica «Condena aplicada» y «Purga de condena completada» como dos avisos separados. La copia privada «Evidencia archivada» y el perdón son eventos distintos y deben mantenerse.

**IMPLEMENTADO EN `Pruebas` (pendiente de CI):** se registra inmediatamente la condena y, al concluir la purga, se edita el mismo embed con alcance y resultado. Se conserva el log alternativo si no existe el inicial o falla editarlo; los errores de purga siguen generando advertencia. La orden `/purge` y otras purgas conservan registro independiente.

**VERIFICACIÓN AUTOMÁTICA:** regresiones añadidas en `tests/test_condemnation_log_dedup.py`; consultar ejecución y resultados de GitHub Actions, no presumir que están aprobadas antes de comprobarlos.

**VERIFICACIÓN REAL DISCORD:** no realizada para esta modificación. Ensayar en Heraldo's Lab, sin purgar mensajes reales, una condena de prueba con purga, una sin purga y fallo simulado de edición, comprobando que no desaparecen evidencias ni notificaciones requeridas. `main` intacta.

## Auditoría externa de integración — 2026-10-14

Claude informó 257 pruebas automáticas satisfactorias en `Pruebas`, 29 históricas de `main`, y 51/52 H-03 aplicables en candidato mínimo; **no repetidas por ChatGPT** y **sin pruebas interactivas Discord**. Ver alcance, discrepancia del commit candidato y pendientes exactos en [`audit/AUDITORIA_INTEGRACION_2026-10-14.md`](audit/AUDITORIA_INTEGRACION_2026-10-14.md). La aceptación real de cambios sensibles sigue pendiente. `main` no modificado.

## Preparación sin despliegue y recuperación aplazada — 2026-10-14

El propietario aplaza hasta noviembre de 2026 la verificación independiente de Bitwarden. Existe una nota privada importada con la clave original, pero NO se ha probado su recuperación/descifrado desde una sesión o dispositivo independiente ni la recuperación de acceso a la bóveda. No tocar la clave, no repetir la importación y no ejecutar operaciones productivas que dependan de ese requisito. Esto permite seguir preparando y verificando código con datos sintéticos.

Base de trabajo: Pruebas 13af6c31fc97e8528bf03e571305b9c6b688a539. Main sigue 6f9f9ee0a7ed1c7b7e6c48a13817b9b5f3a5b667. Producción SUCCESS en bbb21914-a87c-44f3-b862-f4ba3ceecd09, sin cambios pendientes. Test SUCCESS, start python bot.py, preDeploy vacío; no se cambiaron sus secretos ni configuración para ejecutar pruebas.

Defecto corregido en backup_job._isolated_restore: SQLite creaba el destino con permisos dependientes de umask (habitualmente 0644). Ahora se reserva con O_EXCL/O_NOFOLLOW y modo 0600 antes de abrir SQLite; no se cambia umask global desde el hilo del bot, ni se sobrescribe un destino existente. Dos regresiones nuevas verifican privacidad con umask 022 y conservación del archivo existente.

Verificación Linux aislada en Railway Test: compilación, pip check, 39 regresiones históricas y 218 de tests/ aprobadas (257). Transporte simulado, sin credenciales en el proceso hijo, sin importar/iniciar el bot para operar Discord. Warnings no fatales preexistentes en mocks. No son pruebas humanas Discord ni prueba productiva.

Siguiente etapa realizada: tools/prepare_h03_candidate.py construye en directorio NUEVO un candidato basado exclusivamente en main fijo, añade cuatro módulos H-03 y cryptography, e inserta un hook protegido por bandera antes de importar dependencias. Una comparación AST comprueba que el resto de bot.py es idéntico. No crea ramas, no publica main ni despliega. La primera ejecución local encontró un error de indentación del comprobador; corregido y candidato válido generado en otro directorio, conservando el anterior.

Candidato ensayado en proceso aislado de Railway Test: 29 regresiones históricas disponibles en main, compilación y dependencias correctas; extracción AST de db_connect/db_init sin ejecutar el módulo del bot, creación de esquema sintético de main, fila sintética, inicialización candidata, backup y restauración nueva y vuelta a inicialización main. Esquema y contenido coinciden; H03_CANDIDATE_PASS. Programador sin bandera no inicia. Ninguna migración nueva se incorpora al candidato. Esto valida compatibilidad sintética del cambio mínimo; NO sustituye instantánea productiva reciente ni aceptación funcional real antes de desplegar.

Pendientes: recuperación independiente en noviembre, alerta con entrega comprobada, auditoría final de candidato/credenciales y nueva instantánea justo antes del futuro despliegue autorizado. El PR 16 no se integró. No hay respaldo diario real de producción activado ni borrado de copias. Revisar CI y autodespliegues del commit de esta etapa antes de atribuirles éxito.

## H-03 — comprobación integral tras integración opt-in (2026-10-14)

**VERIFICADO AUTOMÁTICAMENTE EN RAILWAY TEST:** `python -m unittest discover -s tests -p test_production_backup_scheduler.py -v` → 10/10 OK; `python -m unittest discover -s tests -p 'test_*.py' -v` → 216/216 OK; `python -m unittest -v test_regressions.py test_member_logs.py` → 39/39 OK. Primer intento sin comillas del patrón descubrió erróneamente `test_regressions.py` como directorio, generó `ImportError` y **fue corregido** antes de proclamar éxito. Los registros de Railway acreditan los resultados. Comandos de prueba pre-deploy retirados; sin alteraciones de SQLite real ni Gateway desde H-03.

**PENDIENTE:** no se ha ensayado una copia diaria productiva ni entrega de alertas, no hay pruebas interactivas humanas Discord en esta fase. El monitor de la producción sigue sin canal de notificación confirmado. No se actualizó `main` ni Railway producción.

## H-03: capacidad conservadora de recuperación (2026-10-14)

**VERIFICADO AUTOMÁTICAMENTE EN RAILWAY TEST, SIN DISCORD:** `python -m unittest discover -s tests -p test_backup_job.py -v` → `Ran 10 tests`, `OK`, despliegue `431d16b9-68a4-4b88-af47-9e0bc1fdd771` SUCCESS. Incluye pruebas nuevas de disco sin margen, presupuesto de volumen inválido, volumen con generaciones retenidas y ruta de montaje incompatible; en todos los bloqueos se impide subir y no se crea recibo ni se borra dato. Las seis regresiones originales siguen pasando. Railway Test utiliza cuota explícita de 500 MB en el servicio de cron de laboratorio, no en worker.

**PENDIENTE:** observar un disparo periódico futuro con la nueva cuota. Nunca considerar la ausencia de borrado como política completa de retención. No se modificaron la base productiva ni `main`. Pruebas humanas de Discord: no realizadas.

## H-03: regresión de validación estricta de recibos — 2026-10-14

**VERIFICADO AUTOMÁTICAMENTE, NO EN DISCORD:** `python -m unittest discover -s tests -p test_backup_health.py -v` en Railway Test, `14 tests`, `OK`, despliegue `85eeacfb-63a7-4c56-ad9b-939882446fcd` SUCCESS. Se probó rechazo de recibo sin finalización, con período/entorno/versión ajenos, fechas futuras, orden temporal incorrecto, estado desconocido, nombre de archivo inválido y permisos públicos, además de salud normal, períodos omitidos y antigüedad. Regresiones sin red ni datos de usuarios.

**Cierre técnico:** pre-deploy retirado; Test `worker` Online/SUCCESS y cron Lab `cronReady/SUCCESS`, sin cambios staged. No se realizaron interacciones Discord, pruebas reales de producción, restauraciones productivas ni cambios en `main`. Entrega efectiva de notificaciones de vigilancia: **pendiente**, notificaciones de ChatGPT desactivadas según estado disponible.

## Automatización H-03 verificada en laboratorio — 2026-10-14

Código de ejecución publicado en Pruebas: cf9f2da77406dd79a6abf254fe445e3092a3bb4f, sobre e59bb4f. Main y producción conservan 6f9f9ee0a7ed1c7b7e6c48a13817b9b5f3a5b667. Sin ramas nuevas ni PR; PR #16 no integrado. Checkout anterior divergente preservado.

Servicio independiente heraldo-h03-lab-cron en Railway Test, volumen privado propio de 500 MB, sin DISCORD_TOKEN ni DB_PATH, seis referencias de secretos exclusivamente Lab. Worker conserva python bot.py y preDeploy vacío, SUCCESS y conectado al Gateway. No hubo cambios funcionales en bot.py ni configuración del worker.

**Ejecución programada real:** 2026-10-14 14:15:04–14:15:13 UTC (10:15 local), run 71b4b38d-f85c-4ca2-bb55-fc3a8224955e, despliegue dc2cedd1-e0d7-42f4-bc8d-3012a1dc84a4. VERIFIED_AND_RESTORED a las 14:15:07, H03_HEALTH OK, proceso EXITED. La frontera de activación bloqueó el respaldo durante el despliegue inicial: la primera transferencia completa fue del programador, no manual. SQLite sintética, API backup, AES-256-GCM, subida/descarga autenticadas, SHA-256, integridad/FK y restauración aislada con esquema/recuentos/contenido coincidentes. Supabase pasó de 1 a 2 objetos Lab: solo una generación nueva de 782 bytes cifrados. La generación productiva existente no cambió.

**Persistencia/duplicados:** segunda ejecución manual del cron a las 14:15:44 UTC en contenedor nuevo: ALREADY_ATTEMPTED no_retry=true, H03_HEALTH OK y proceso terminado. Sin nueva subida. No confundir esta segunda invocación manual con el disparo programado anterior. Recibos y generaciones permanecen privados en el volumen.

**Pruebas:** 39 + 195 = 234 regresiones offline en proceso Linux aislado de Railway Test, compilación y pip check aprobados; transporte simulado, sin iniciar Discord. CI del commit cf9f2da: workflows Mensajes y Heraldo Lab aprobados (runs 38577334609 y 38577334553). Prueba negativa real contra Supabase con API key inválida solo en proceso efímero: acceso denegado antes de subida, recibo needs_manual_review, segundo intento bloqueado. Corrupción GCM y clave incorrecta rechazadas con datos sintéticos. Períodos omitidos, fallos, fecha futura y antigüedad desde finished_at cubiertos por regresiones. Logs operativos inspeccionados: solo estados/fechas, sin secretos, filas ni manifiestos. Warnings no fatales preexistentes en mocks SQLite/discord.py; no pruebas humanas Discord.

Horario diario configurado: 06:15 UTC / 02:15 America/Santo_Domingo; se aplica con el despliegue de este commit de cierre y se verifica después. Vigilancia local Codex diaria 08:00, solo Lab, deduplicación por incidencia; depende del equipo/Codex. Vigilancia productiva previa de ChatGPT no modificada. Primer disparo futuro del monitor pendiente: no se afirma entrega de alertas probada.

Producción NO automatizada. Procedimiento, límites y autorización pendiente en AUTOMATIZACION_H03.md. Segunda custodia de clave productiva y ejecutor continuamente disponible siguen pendientes; no se movió la clave. No se borraron respaldos, registros ni datos. Obsidian sin conexión.

## Verificación de entrada cron H-03 — Railway Test, 2026-10-14

**VERIFICADO AUTOMÁTICAMENTE:** `python -m unittest discover -s tests -p test_scheduled_lab_backup.py -v` en pre-deploy temporal del `worker` de Railway Test. Despliegue `7fd7ace1-2fa6-40ff-8548-5517cd199561`, registros: seis pruebas `ok`, `Ran 6 tests in 0.011s`, `OK`. Casos: identidad, token de Discord rechazado, volumen ausente rechazado, SQLite sintética, duplicado no reintentado y error crítico propagado. El archivo `tests/test_scheduled_lab_backup.py` pasó; las ejecuciones remotas de H-03 programadas con acceso Supabase NO se ensayaron en esta fase.

**ESTADO FINAL:** `worker` Test Online/SUCCESS; inicio `python bot.py`, sin pre-deploy, sin recursos/configuraciones en `staged`. Sin pruebas de interacciones reales en Discord y sin escrituras de producción.

## Entrada cron H-03 para Railway Lab — 2026-10-13

**IMPLEMENTADO, PENDIENTE DE PRUEBA AUTOMÁTICA ACTUAL:** `tools/scheduled_lab_backup.py` y `tests/test_scheduled_lab_backup.py` (identidad de servicio de Test, rechazo de credencial de Discord, comprobación de volumen, SQLite sintética, idempotencia y propagación de errores). Workflow de compilación actualizado. Los seis tests de `test_backup_job.py` fueron previamente verificados en Railway Test; los **seis nuevos** de la entrada cron NO deben confundirse con ellos. El entorno de Discord NO se probó.

**Cron no ejecutado:** Railway bloqueó la escritura de la configuración del servicio nuevo; no existe cron activo. Se dejó un borrador STAGED de Test no desplegado, pendiente de descarte manual seguro. No se tocó la producción ni se transfirieron datos reales.

## Regresiones H-03 fase 1 — 2026-10-13

**VERIFICADO AUTOMÁTICAMENTE, SIN DISCORD**: `python -m unittest discover -s tests -p test_backup_job.py -v` ejecutado en pre-deploy efímero de Railway Test: `Ran 6 tests`, `OK`. Casos: recuperación aislada y diario privado, bloqueo de duplicados del mismo día, fallo ambiguo de subida sin reintento, identificación/autorización de producción, rechazo de modo laboratorio en proyecto productivo y segundo intento permitido en día UTC distinto. Transporte remoto simulado; no se leyeron SQLite de Discord. Despliegue `8e87b5b2-64c4-443e-bc38-0a4a67e44dba` finalizó `SUCCESS`, réplica Online 1/1. Pre-deploy de pruebas retirado; `python bot.py` conservado. **CI GitHub Actions específico del HEAD aún por confirmar**, distinto del resultado real Railway. Programador de respaldos de producción: NO activado.

## Actualización H-03 — respaldo externo de producción (2026-10-13)

**REALIZADO SEGÚN INFORME DE CODEX LOCAL:** generada copia consistente SQLite mediante `Connection.backup` sin detener ni modificar el bot de producción. Se cifró externamente con AES-256-GCM usando clave distinta de la empleada en Test, se transfirió a Supabase con la cuenta técnica y se descargó, autenticó y restauró en SQLite aislada. El informe documenta integridad SQLite y claves foráneas correctas, coincidencia de esquema y contenido, prueba de rechazo de manipulación GCM y ausencia de cambios en producción. **Estas verificaciones de contenido/descifrado proceden del informe aportado por el propietario, no han sido repetidas por ChatGPT.**

**VERIFICADO INDEPENDIENTEMENTE POR CHATGPT (consulta 2026-10-13):** en Supabase Storage existe exactamente 1 objeto cifrado bajo la categoría de producción (100609 bytes) y 1 objeto de laboratorio; el bucket sigue privado y las políticas son solo INSERT/SELECT para usuarios authenticated restringidos por identidad. Railway producción sigue Online/SUCCESS con el despliegue anterior; Railway Test también Online/SUCCESS. No se leyó SQLite ni su clave, ni se modificó `main`.

**RIESGO PRIORITARIO:** la clave de descifrado de esta generación se conserva en un único equipo local según el informe. El propietario debe conservar una **segunda copia de la clave** en un medio seguro independiente (p. ej., gestor de contraseñas con recuperación u offline cifrado) y verificar acceso a ella. No publicar clave, rutas privadas, identificadores de generaciones, manifiestos ni datos en repositorio/Discord/chat. No repetir copia ni proceso de subida sin control de idempotencia; no hay aún protección continua.

**PENDIENTE:** periodicidad y supervisión de nuevos respaldos, política de conservación, segundo destino y disponibilidad ante pausas de Supabase Free, ensayos periódicos de restauración y cobertura independiente de adjuntos/evidencias externos de Discord. No implica autorización para desplegar `main`, restaurar producción ni ejecutar escrituras administrativas. Sin pruebas Discord en esta fase.

## Prueba real Supabase H-03 — 2026-10-13 (verificada automáticamente, no en Discord)

Railway **Test** ejecutó `python -m tools.supabase_smoke_test` como pre-deploy en contenedor efímero, aislado del volumen y sin importar `bot.py`. Logs del despliegue `ef2cc191-accd-4b9c-8ab3-4d07acf9fc87`: `H03_SMOKE step=local_backup status=verified`, `encrypted_upload`, `remote_download`, `isolated_restore`, `status=PASS scope=synthetic_no_discord`. Se confirmó en Supabase 1 objeto bajo `lab/`, 766 bytes cifrados. Servicio Test `SUCCESS`, 1/1 réplica Online. El comando pre-deploy se retiró después y el arranque habitual sigue `python bot.py`.

Durante implementación hubo dos builds Test fallidos por resolución de `-r requirements-backup.txt` en Railpack; se corrigió incluyendo `cryptography>=43,<47` directamente en `requirements.txt` de `Pruebas`. La prueba real completa se ejecutó **después** de la corrección. Ni datos reales ni Discord se utilizaron. **No prueba ni protege la base SQLite de producción**. Pruebas de Discord reales: no realizadas en esta fase. Fecha/objetos y logs no deben confundirse con backup real.

## Transporte Supabase (preparación, 2026-10-13)

Añadidas regresiones offline de empaquetado H-03/cifrado AES-GCM/manipulación/identidad/aislamiento por entorno y transferencia simulada. **No ejecutado contra Supabase real; no hay cuenta técnica, clave de cifrado, ni operaciones Discord reales.** Verificar CI del SHA publicado. Railway Test Online tras auto-despliegue, esto no equivale a validación de comandos. Laboratorio para descarga/restauración aún pendiente. `RESPALDOS_SUPABASE.md`.

# Registro de pruebas — El Heraldo Test

**Entorno autorizado:** servidor Heraldo's Lab, bot El Heraldo - Test, rama `Pruebas`.
**Regla:** no probar moderación destructiva sobre usuarios reales ni usar cuentas personales automatizadas.
**Convención:** PENDIENTE / OK / FALLA / BLOQUEADO. Incluir fecha, commit, actor, pasos, resultado y evidencia redactada (sin información privada).

## Registro de ejecución
| Fecha (UTC) | Commit | Prueba | Estado | Observaciones |
|---|---|---|---|---|
| 2026-10-08 | a69f59b | Railway: construcción y arranque | OK | Servicio SUCCESS y Discord Gateway conectado |
| 2026-10-08 | a69f59b | Autoprueba interna `/setup` | OK | Log de inicio de Heraldo's Lab; **no implica prueba interactiva** |
| 2026-10-08 | c1f2e8e | Regresiones offline: confirmación y aislamiento | OK | GitHub Actions `python-checks`; no realizado dentro de Discord |

## Matriz de pruebas interactivas (pendientes)
| Área | Caso a verificar | Estado | Resultado / referencia |
|---|---|---|---|
| /setup | Abrir, navegar, volver y cancelar | PENDIENTE | |
| Mensajes | Crear plantilla; cancelar sin persistencia | PENDIENTE | |
| Mensajes | Guardar plantilla y comprobar persistencia tras reinicio | PENDIENTE | |
| Mensajes | Previsualizar y publicar en canal correcto | PENDIENTE | |
| Mensajes | `/edittemplate`: confirmar edición de mensaje propio | PENDIENTE | |
| Mensajes | `/edittemplate`: rechazar mensaje ajeno o servidor ajeno | PENDIENTE | |
| Mensajes | Botones, selectores, opciones y jerarquía de roles | PENDIENTE | |
| Mensajes | Exportar/importar kit; rechazar conflictos | PENDIENTE | |
| Reaction Roles | Publicar panel, asignar/quitar roles y reiniciar | PENDIENTE | |
| Join Roles | Guardado manual, selección, retrasos y permisos | PENDIENTE | |
| Moderación | Condena manual, duración, tarjeta, DM, roles retirados | PENDIENTE | |
| Moderación | Perdonar, restaurar roles, eliminar castigo | PENDIENTE | |
| Evidencias | Persistir texto/adjuntos cuando desaparece origen | PENDIENTE | |
| Logs y reportes | Coherencia, un solo aviso pertinente, enlaces válidos | PENDIENTE | |
| Seguridad | Restricción por administrador, servidor y permisos | PENDIENTE | |
| Resiliencia | Reinicio de bot y componentes persistentes | PENDIENTE | |

## Modelo de incidencia
### INC-AAAA-MM-DD-001 — [título]
- **Estado:** Abierta / En corrección / Validada.
- **Contexto:** módulo, rama, commit, entorno.
- **Pasos para reproducir:** 1)... 2)... 3)...
- **Esperado:** ...
- **Observado:** ...
- **Impacto:** ...
- **Evidencia segura:** enlace a issue/registro sin datos sensibles.
- **Corrección:** commit ...
- **Reprueba:** fecha, autor, resultado ...

Nunca inventar pruebas ejecutadas. Si una interacción no pudo comprobarse, conservar PENDIENTE.

## Ampliación automatizada del laboratorio (2026-10-09)
- **CI propuesto:** `.github/workflows/heraldo-lab-checks.yml`, ejecutable en PR contra `Pruebas` y manualmente.
- **Casos CI previstos:** `py_compile bot.py`, `py_compile test_regressions.py`, regresiones offline existentes, y `tests/test_*.py` (incluida regresión del selector de logs).
- **Resultados CI:** PENDIENTE hasta recibir resultado de GitHub Actions de este PR.
- **Prueba real en Discord:** NO REALIZADA en esta ampliación. No se simulan clics con cuentas de usuario.
- **Validación posterior al despliegue:** `Heraldo's Lab` → `/setup` → `Mensajes` → `Logs`, abrir categorías y volver; registrar hora, captura saneada y errores.

## Etapa 1 — 2026-10-09 (America/Santo_Domingo)
- CI histórico de `ffefb77`: OK, ejecución https://github.com/ElCreador5/el-heraldo-bot/actions/runs/37889193532, 35 regresiones y 1 prueba del selector. Reemplaza el PENDIENTE de la propuesta original exclusivamente para ese commit.
- Actor: Codex, Windows, Python 3.12.10 y discord.py 2.7.1. Árbol reconciliado a partir de `b8480b8`, `6f9f9ee` y `ffefb77`; registrado en el commit de preparación de esta etapa.
- `python -X utf8 -m pip check`: OK.
- `python -X utf8 -m py_compile bot.py test_regressions.py test_member_logs.py`: OK.
- `python -X utf8 -m unittest -v test_regressions.py`: 35 pruebas OK.
- `python -X utf8 -m unittest -v test_member_logs.py`: 4 pruebas OK.
- `python -X utf8 -m unittest discover -s tests -p 'test_*.py' -v`: 1 prueba OK.
- Los primeros intentos de las suites SQLite quedaron bloqueados por los temporales del sandbox, no por una regresión del bot. La repetición autorizada finalizó correctamente.
- Las suites de raíz se ejecutan en procesos separados para mantener aislados sus módulos, variables y bases SQLite. La matriz Linux 3.11/3.12/3.13 requiere comprobar el nuevo CI.
- Pruebas reales de Discord: NO REALIZADAS. La matriz interactiva anterior sigue pendiente, así como los nuevos fallos identificados en la auditoría.

## Regresiones de seguridad y mensajes — 2026-10-10
- Python 3.12.10 y discord.py 2.7.1. `python -X utf8 -m unittest test_regressions.py test_member_logs.py`: 39 pruebas aprobadas.
- `python -X utf8 -m unittest discover -s tests -p 'test_*.py'`: 25 pruebas aprobadas.
- Cobertura nueva: rol persistido de condena, aislamiento entre servidores, bloqueo condena/perdón, permisos revocados, propuestas y cancelación, conflictos concurrentes, expiración fuera de caché, auditoría tardía o inaccesible, autor de evidencia, política de autoservicio, formatos avanzados, kits y límites tras variables.
- Una invocación inicial añadió erróneamente discover como módulo; ese error de comando se corrigió. No confundirlo con una regresión del bot.
- Discord interactivo: NO realizado. Pendiente comprobar restauración parcial de roles, archivo privado y fallos de adjuntos, pérdida de permisos durante formularios, publicación/edición, reconexión y conservación de estado.
- Railway verificado para la versión anterior del PR #6; las correcciones nuevas aún no están desplegadas en este punto de continuidad.

### Ampliación de comprobaciones — 2026-10-10
- Cola persistente de Join Roles: conservación entre conexiones SQLite, recuperación sin volver a esperar y conservación ante servidor inaccesible.
- Formularios: tiempos no guardados antes de confirmar; permiso revocado impide proponer/guardar demora.
- Suites actuales: 39 raíz + 30 tests = 69 aprobadas. CI del primer lote del PR #7 aprobada (38033889706); ampliación pendiente de publicar. No hay pruebas Discord nuevas.

### Lote ampliado: 78 pruebas offline — 2026-10-10
- 39 regresiones raíz y 39 descubiertas en tests: correctas. Compilación de bot.py, message_payload.py y message_automation.py correcta; pip check correcto.
- Programación: conversión de zona, horas ambiguas/inexistentes, cambio de horario estacional, envío único, permisos revocados, timeout incierto, reinicio y aislamiento por servidor.
- Compatibilidad: las plantillas de texto no se convierten por el hook global; una plantilla de 6000 caracteres no recibe pies que la invaliden.
- Las primeras regresiones de Reaction Roles tras endurecer permisos fallaron por mocks sin permisos/tipo de rol definidos. Los fixtures ahora representan roles ordinarios explícitos; ambas rutas añadir/quitar e inversión volvieron a pasar.
- Recorrido manual pendiente en laboratorio: crear programación futura, cancelar propuesta, confirmar, listar, comprobar destino y variables, retirar una recurrente, reiniciar con un trabajo pendiente y revocar permisos antes del envío. No realizar estos ensayos en producción.
- No se han probado aún Discord Gateway, formularios reales ni reinicios Railway para este lote.

### Automatizaciones: 91 pruebas offline — 2026-10-10
- 39 raíz + 52 tests aprobadas; compilación correcta. Pendiente verificar la nueva CI y despliegue del PR #7.
- Nuevas regresiones: palabras completas y coincidencia literal, variables del usuario que activa la regla, espera entre reinicios, límite común entre reglas, rechazo de bots/webhooks/condenados; sticky con actividad concurrente y rechazo de mensajes ajenos; cancelar webhook sin llamadas, permisos revocados, plantilla modificada, reutilización del propio webhook y exclusión de uno ajeno.
- Ensayos Discord pendientes: mensajes exactos y parciales, adjuntos que provocan sticky, ráfagas de conversación, mensajes del propio bot, reinicio durante espera, pérdida de permisos y publicación confirmada por webhook en canal del laboratorio.
- Ninguna llamada real a Discord ejecutada por estas pruebas. No automatizar cuentas personales para realizar los ensayos.


### Verificación final del lote de editores — 2026-10-10
- Python 3.12.10 / discord.py 2.7.1: 39 pruebas raíz y 67 descubiertas en tests, total 106. Compilación de bot y los cuatro módulos de Mensajes, pip check y git diff --check correctos.
- Cobertura adicional: cambios solo en borrador, conflictos concurrentes, modal obsoleto/cerrado, embed vacío, descripción larga sin truncar, menú independiente y selección múltiple, esquema de acciones, cancelación y propietario, permisos revocados, condena activa, fallo parcial con auditoría persistente y espera entre ejecuciones.
- Honeypot: cancelar conserva valores y no sincroniza; permisos revocados impiden proponer cambios. Condenas: copia de roles disponible antes de una interrupción de la llamada remota.
- Discord real: NO realizado para PR #7. Laboratorio continúa en la versión anterior 34fa94f. Seguir REVISION_PR7.md después de verificar integración y commit del despliegue. Los resultados offline no acreditan funcionamiento de formularios, Gateway o reinicio real.

## Auditoría PR #10 — 2026-10-11

- **Automatización:** GitHub Actions `Heraldo Lab - Python regressions` ejecución `38146125476`, commit `c3896d7`: SUCCESS en Python 3.11, 3.12 y 3.13. Regresiones de configuración/cancelación, logs, moderación y control de evidencias offline. No equivale a prueba real de Discord.
- **Discord:** NO REALIZADAS para PR #10. **Railway de laboratorio:** última versión observada `Pruebas@34fa94f`, anterior a PR #10.
- **PENDIENTE (laboratorio):** para cada comando heredado corregido, confirmar que «Cancelar» no cambia SQLite, que «Guardar cambios» sí lo hace, que otro administrador no puede reutilizar el borrador y que retirar permisos antes de confirmar bloquea la escritura.
- **PENDIENTE (laboratorio):** `/honeypot add/create/remove/exempt_*` ante canal inexistente, bot sin permisos, exenciones concurrentes y avisos fijados.
- **PENDIENTE (laboratorio):** Raid Protection y condena manual; restauración de roles y casos incompletos; evidencia/adjuntos privados y purgas canceladas cuando no hay archivo; DMs, logs y eliminación de duplicados.
- **PENDIENTE (laboratorio):** panel de sugerencias, canales de anuncios, Join Roles, Reaction Roles, reinicio y persistencia de componentes, y regresiones de Mensajes.

## Resultado de integración y caso pendiente de roles — 2026-10-11

- `Pruebas@d190c11a95`: GitHub Actions Python/Mensajes OK; Railway Test despliegue SUCCESS, bot en Discord Gateway y autoprueba /setup OK. Actor: verificación remota de GitHub y Railway; **no se ejecutaron interacciones como un usuario humano**.
- PR #11 `fix/recuperacion-roles-pendientes-20261011`: pruebas SQLite offline para aislamiento por servidor, cancelar, permisos revocados y restauración parcial; ejecutar CI para último SHA del PR.
- Casos interactivos **PENDIENTES** (PR #11, tras integrar al laboratorio): liberar condenado con un rol no asignable, comprobar que se registra como pendiente; reparar jerarquía; ejecutar `/restaurar_roles_pendientes`, cancelar sin modificación y confirmar; comprobar roles restaurados, logs y persistencia tras reinicio; rechazar condena aún activa y permisos perdidos.


## Auditoría de PR #12 — 2026-10-11
- Línea base de a260fec8: 132 pruebas offline aprobadas (39 + 93); CI 38157090799 correcta. Nueva prueba sin sustituir el callback reprodujo TypeError al elegir sección de setup.
- Rama de auditoría: 144 pruebas offline aprobadas (39 + 105), compilación y pip check correctos. Selector real de las siete secciones, etiquetas de cinco acciones, permisos de modal, ledger persistente/aislado, archivo de evidencia privado/incompleto y restauración con defer/error API/permisos revocados cubiertos.
- Railway Test observado en a659b28, despliegue a8314dd2 SUCCESS; solo arranque/Gateway/autoprueba verificados. No se ejecutaron clics, comandos o reacciones humanas ni moderación real durante la auditoría.
- Pruebas manuales mínimas y vacíos por módulo en audit/MATRIZ_COBERTURA.md. El nuevo lote aún no está desplegado.


## Caso observado: dos expulsiones registradas por verificación — 2026-10-11
- Evidencia aportada por el propietario: dos mensajes de expulsión para un miembro, uno del timeout principal y otro del respaldo Sin Verificar. No se copia su identidad al informe. No consta el commit exacto de la captura.
- Reproducción offline antes de corregir: dos llamadas a kick y dos registros; además el respaldo podía saltarse el plazo ampliado o la acción solo registrar/ban.
- tests/test_verification_expiry.py incorpora 11 regresiones: una sanción/registro, concurrencia, aislamiento por servidor, ban, solo registrar, ampliación del plazo, marca reciente, respaldo independiente, miembro verificado y fallos API con pendientes conservados.
- Suite final: 39 raíz/Logs + 116 tests = 155 aprobadas. Compilación e inventario regenerado correctos. Una primera prueba de concurrencia quedó esperando por el defecto reproducido; se detuvo ese proceso de pruebas y se acotó la espera. La repetición tras corrección y la suite completa terminaron correctamente.
- Pendiente laboratorio, después de integrar PR #13: participante voluntario con ambos temporizadores; esperar plazo y comprobar una sola expulsión y un solo registro. Repetir con solo registrar sin expulsión y plazo ampliado. No ejecutar sobre miembros reales sin consentimiento.

## H-01 verificado offline — 2026-10-11
- Base da551f3: 158 pruebas offline aprobadas (119 tests + 39 raíz/Logs), pip check y compilación correctos. Tres guardas AST de Solo reportar pasan.
- Dos regresiones nuevas comprueban la ejecución real sin sanción/purga y normalización heredada. El primer fixture omitía label obligatorio; corregido sin cambiar producción.
- Discord real: no realizado. CI y Railway Test de da551f3 correctos; pendientes recorrido humano y nuevo SHA.

## H-02: barrera de conservación — 2026-10-11
- Purga general, condenas, reportes, Honeypot (incluidos mensajes durante otra sanción) y raid pasan por archivo individual antes del borrado. Baneos usan delete_message_seconds=0; la purga configurada se ejecuta separadamente con archivo.
- evidence_archive.py conserva JSON íntegro y adjuntos en el canal privado de Logs existente; verifica tamaño y SHA-256 leyendo cada copia desde Discord. Ledger SQLite durable y exclusión por mensaje: una interrupción incierta bloquea reenvío/borrado. Condenas conservan el contrato de referencia y texto, sin migrar expedientes previos.
- Si no hay intent de contenido, canal privado, permisos o copia íntegra, no se borra. Archivos superiores al menor límite de Discord/25 MiB, stickers, encuestas y mensajes reenviados quedan conservados en origen. No se crearon almacenamiento ni credenciales.
- Se vuelve a leer el origen para detectar ediciones y comprobar privacidad antes del borrado. Discord no ofrece transacción atómica entre edición, permisos y delete: queda una ventana remota mínima y requiere validación humana. Una copia borrada/corrupta o ledger pendiente exige revisión; no se reintenta un envío incierto automáticamente.
- Pruebas base tras integración: 129 tests y 39 raíz/Logs correctos; añadidas luego tres comprobaciones de roles, excepciones individuales y formatos no soportados. El primer ensayo detectó conexiones SQLite sin cerrar; corregidas con cierre explícito.
- Discord real: no realizado. Pendiente validar CI/Railway del nuevo SHA y copia/recuperación en laboratorio. H-03 y etapas posteriores continúan pendientes.

## H-03 y revisión A–F del lote — 2026-10-12
- Base `Pruebas@9502cea`, rama `codex/h03-recuperacion-20261012`, Codex Cloud Linux, Python 3.12.14 / discord.py 2.7.1.
- `.venv/bin/python -m unittest test_regressions.py test_member_logs.py`: 39 correctas.
- `.venv/bin/python -m unittest discover -s tests -p 'test_*.py'`: 164 correctas; total 203. H-03 aporta 23 tests: WAL confirmado/no confirmado, escritura concurrente atómica, integridad/FK, almacenamiento insuficiente, fallo de fsync/reemplazo, timeout, interrupción de subprocess, reinicio, conservación/rollback, bloqueo entre procesos, esquema, checksums/manifiesto/sidecars, permisos, estados de evidencias/roles y CLI completa. Datos sintéticos temporales.
- Compilación de bot, sqlite_recovery, evidence_archive y módulos de Mensajes: correcta. `pip check` y `git diff --check`: correctos.
- Primer ensayo H-03: un fixture pretendía crear directorio 0755, pero umask lo hizo privado. Se corrigió el fixture con chmod explícito y la repetición pasó; no se relajó la protección.
- Nuevas regresiones: archivado con mutación del objeto original, intent ausente/copia perdida, restauración/confirmación caducadas y selector/edición visual de campos con permisos revocados y límites. Las suites previas de verificación, Solo reportar, Reaction Roles y moderación siguen pasando.
- CI remoto: NO CONSULTADO, API GitHub bloqueada por proxy. Railway: NO CONSULTADO/NO DESPLEGADO. Discord real: NO REALIZADO. No extrapolar el resultado local a estas tres comprobaciones.
- Recorrido humano pendiente: selección de embed/campo, guardar/cancelar, permisos retirados y modal tardío; respaldo/descarga/restauración aislados de Test, reconciliación de operaciones inciertas y comprobación de evidencias remotas. No activar purgas, sanciones ni restauraciones en datos reales por este informe.
