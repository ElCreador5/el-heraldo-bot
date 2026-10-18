## SQLite real de Test — implementación 2026-10-18

El encargo actual autoriza trabajar directamente en `Pruebas`, configurar Test y
respaldar su SQLite real. `test_backup_scheduler.py` ejecuta un proceso corto
`python -m test_backup_runtime due` desde el worker propietario del volumen. La
primera activación respalda inmediatamente; luego comprueba el vencimiento diario
06:15 UTC (02:15 Santo Domingo), con recuperación del disparo tras reinicio.
El subproceso no recibe DISCORD_TOKEN. Una réplica, volumen worker-volume de
500 MB, identidad Railway exacta, DB_PATH canónico y estado fijo privado son
requisitos; no se permite el cron sintético ni producción. Activación explícita:
HERALDO_TEST_BACKUP_ENABLED=enabled y HERALDO_BACKUP_VOLUME_CAP_MB=500.

Test utiliza `heraldo-test-sqlite-backups`, privado, límite 45 MB y MIME binario,
cuenta técnica nueva y clave AES independiente. RLS permite solo INSERT/SELECT,
exige identidad exacta y prefijo heraldo-test. Las políticas del bucket histórico
no se modificaron. Las seis variables estándar del worker fueron reemplazadas
por las exclusivas de Test, después de conservar valores independientes en el
cron; así el cron no pierde acceso a sus generaciones antiguas ni el worker
conserva las credenciales históricas. La custodia local de Test está cifrada con
Windows DPAPI; depende de la cuenta Windows, no acredita recuperación de la
clave ORIGINAL de producción desde otro dispositivo.

El motor usa Connection.backup con origen mode=ro, valida integridad/FK y
manifiesto, cifra AES-256-GCM antes de red, sube sin upsert, descarga/autentica y
restaura a archivo nuevo. Compara esquema, recuentos y hashes de todas las filas.
Guarda la ruta del objeto en el recibo privado ANTES de la subida: una respuesta
perdida se reconcilia mediante descarga, sin repetir la transferencia. Un fallo
pendiente bloquea nuevas generaciones hasta resolverlo. Un lock y un recibo por
día impiden duplicados entre scheduler, CLI, reinicios y procesos concurrentes.
No se eliminan generaciones; el presupuesto de disco conserva 64 MiB de margen.

Para comprobar/recuperar una generación ya registrada, ejecutar DENTRO del
worker Test: `python -m test_backup_runtime recover --day AAAAMMDD`. El comando
no acepta destino: siempre usa un directorio temporal privado del volumen,
valida el respaldo remoto, compara contenido, elimina únicamente su temporal y
registra last_recovery_at. También permite reconciliar upload_unconfirmed cuando
el objeto remoto realmente existe. Si falta o está corrupto, conserva el bloqueo;
no borrar recibos para forzar intentos. Los paquetes y la primera restauración
verificada permanecen en el estado privado; la SQLite activa nunca es destino.
La pérdida de recibos requiere recuperar su copia administrativa o localizar
la generación en Storage; esta CLI no inventa recibos ni enumera datos privados.

Validación previa: 18 casos nuevos, 72 casos H-03 (incluyen los 18) y 39 base
aprobados en Linux, compilación y pip check correctos. La suite global en SSH
se interrumpió y no se acredita; se verifica en CI GitHub. Transferencia REAL comprobada el 18/10/2026 09:02:59 UTC (05:02:59 local):
SQLite del worker en WAL, 479232 bytes; objeto cifrado 89228 bytes; AES-GCM,
SHA-256, integridad/FK, esquema/recuentos/contenido recuperados correctos.
Fuente desplegada 926f6d552f42aca1b63b0e8cbff6d8dd7b335d27. Se ejecutaron los
módulos candidatos ya probados en un proceso temporal del worker; el bot conservó
su proceso y los respaldos locales anteriores conservaron sus hashes. Supabase
confirma una generación Test y mantiene 5 Lab + 1 producción en el bucket antiguo.
El programador aún requiere despliegue/activación y comprobación posterior.
No incluye archivos de evidencias de Discord ni activación de producción.

## Automatización H-03 verificada en laboratorio — 2026-10-14

Código de ejecución publicado en Pruebas: cf9f2da77406dd79a6abf254fe445e3092a3bb4f, sobre e59bb4f. Main y producción conservan 6f9f9ee0a7ed1c7b7e6c48a13817b9b5f3a5b667. Sin ramas nuevas ni PR; PR #16 no integrado. Checkout anterior divergente preservado.

Servicio independiente heraldo-h03-lab-cron en Railway Test, volumen privado propio de 500 MB, sin DISCORD_TOKEN ni DB_PATH, seis referencias de secretos exclusivamente Lab. Worker conserva python bot.py y preDeploy vacío, SUCCESS y conectado al Gateway. No hubo cambios funcionales en bot.py ni configuración del worker.

**Ejecución programada real:** 2026-10-14 14:15:04–14:15:13 UTC (10:15 local), run 71b4b38d-f85c-4ca2-bb55-fc3a8224955e, despliegue dc2cedd1-e0d7-42f4-bc8d-3012a1dc84a4. VERIFIED_AND_RESTORED a las 14:15:07, H03_HEALTH OK, proceso EXITED. La frontera de activación bloqueó el respaldo durante el despliegue inicial: la primera transferencia completa fue del programador, no manual. SQLite sintética, API backup, AES-256-GCM, subida/descarga autenticadas, SHA-256, integridad/FK y restauración aislada con esquema/recuentos/contenido coincidentes. Supabase pasó de 1 a 2 objetos Lab: solo una generación nueva de 782 bytes cifrados. La generación productiva existente no cambió.

**Persistencia/duplicados:** segunda ejecución manual del cron a las 14:15:44 UTC en contenedor nuevo: ALREADY_ATTEMPTED no_retry=true, H03_HEALTH OK y proceso terminado. Sin nueva subida. No confundir esta segunda invocación manual con el disparo programado anterior. Recibos y generaciones permanecen privados en el volumen.

**Pruebas:** 39 + 195 = 234 regresiones offline en proceso Linux aislado de Railway Test, compilación y pip check aprobados; transporte simulado, sin iniciar Discord. CI del commit cf9f2da: workflows Mensajes y Heraldo Lab aprobados (runs 38577334609 y 38577334553). Prueba negativa real contra Supabase con API key inválida solo en proceso efímero: acceso denegado antes de subida, recibo needs_manual_review, segundo intento bloqueado. Corrupción GCM y clave incorrecta rechazadas con datos sintéticos. Períodos omitidos, fallos, fecha futura y antigüedad desde finished_at cubiertos por regresiones. Logs operativos inspeccionados: solo estados/fechas, sin secretos, filas ni manifiestos. Warnings no fatales preexistentes en mocks SQLite/discord.py; no pruebas humanas Discord.

Horario diario configurado: 06:15 UTC / 02:15 America/Santo_Domingo; se aplica con el despliegue de este commit de cierre y se verifica después. Vigilancia local Codex diaria 08:00, solo Lab, deduplicación por incidencia; depende del equipo/Codex. Vigilancia productiva previa de ChatGPT no modificada. Primer disparo futuro del monitor pendiente: no se afirma entrega de alertas probada.

Producción NO automatizada. Procedimiento, límites y autorización pendiente en AUTOMATIZACION_H03.md. Segunda custodia de clave productiva y ejecutor continuamente disponible siguen pendientes; no se movió la clave. No se borraron respaldos, registros ni datos. Obsidian sin conexión.

## Fase 1: ejecutor de respaldo periódico preparado (2026-10-13)

**Implementado en `Pruebas`, pero NO ACTIVADO para producción.** El archivo `backup_job.py` ejecuta UNA operación H-03 por invocación desde un entorno autorizado. Toma una instantánea SQLite online con `sqlite_recovery.create_backup`, cifra y sube usando `supabase_backup.upload`, la descarga con `download_verify` y realiza una restauración SQLite en archivo nuevo y aislado para comparar integridad, esquema y recuentos. No importa Discord ni conecta al Gateway; no restaura sobre la base activa ni elimina generaciones remotas.

**Barreras de seguridad:** verificación de `RAILWAY_PROJECT_ID`, `RAILWAY_ENVIRONMENT_ID`, `RAILWAY_SERVICE_ID` y `HERALDO_PRODUCTION_BACKUP_ENABLED=enabled-after-owner-approval` para el entorno `heraldo-production`; exige que base y diario de estado estén en `/data`. El modo `lab` está prohibido en el proyecto Railway de producción. Usa directorio privado POSIX, archivo `flock`, diario durable con un intento por fecha UTC y una marca `needs_manual_review` tras errores. Los errores ambiguos de subida NO provocan reintentos automáticos, evitando duplicados ciegos. Nunca imprimir identidades de objetos, SHA privados, rutas de SQLite o contenido; el recibo permanece en directorio privado. **No borrar el diario para forzar reintentos sin reconciliar Storage.**

Parámetros de ejecución (solo cuando exista disparador autorizado y claves almacenadas correctamente):

- `DB_PATH`: ubicación de SQLite del servicio.
- `HERALDO_BACKUP_STATE_DIRECTORY`: carpeta persistente privada, distinta de la SQLite fuente.
- `HERALDO_BACKUP_ENVIRONMENT`: `lab` o `heraldo-production`.
- `HERALDO_BACKUP_REVISION`: SHA/revisión comprobada del binario.
- Credenciales y clave ya definidas en `supabase_backup.py`; usar una clave de producción custodiada de forma independiente, nunca la de Test.
- **Solo producción**, después de autorización específica, `HERALDO_PRODUCTION_BACKUP_ENABLED=enabled-after-owner-approval`.

Ejecutar un intento con `python -m backup_job` únicamente en contenedor autorizado con configuración completa. El comando **no es un daemon ni un programador**: aún falta integrar un disparador diario compatible con el volumen montado, configurar los secretos de producción, respaldar la clave fuera de Railway y verificar un ciclo completo real con restauración aislada. No se programa nada en `main` ni se cambia su proceso de arranque.

**Prueba automática ejecutada en Railway Test:** pre-deploy temporal en contenedor sin volumen `python -m unittest discover -s tests -p test_backup_job.py -v`, despliegue `8e87b5b2-64c4-443e-bc38-0a4a67e44dba`, **6/6 casos OK, servicio Online/SUCCESS**. Transporte Supabase simulado dentro de esa suite. Se retiró el pre-deploy y se restauró el inicio normal `python bot.py`. El archivo `tests/test_supabase_backup.py` y el anterior ensayo H-03 en Storage aportan comprobaciones distintas. No hubo ensayos Discord en este bloque.

**Vigilancia ya programada por ChatGPT:** comprobación diaria de metadatos Supabase; notifica si último objeto de producción supera las 36 horas, desaparece, se pierde la privacidad o falla la consulta. **Alerta no equivale a realización de nuevos respaldos**. Por ahora existe solamente una generación verificada de producción; es normal que la vigilancia avise si no se activa la creación periódica.

**Prioridades antes de habilitar producción:** copia adicional y probada de la clave de descifrado en destino independiente del PC; autorización explícita de configuración/despliegue de producción; estrategia de segundo destino ante pausa de Supabase Free y pruebas periódicas de recuperación. Evidencias externas de Discord no quedan incluidas en SQLite.

**Estado (2026-10-13):** respaldo externo de producción CONFIRMADO EN STORAGE, con recuperación aislada APROBADA SEGÚN INFORME DE CODEX LOCAL. El bot de Discord no ejecuta el módulo automáticamente y aún no hay programación de nuevas copias. Mantener cifrado, clave externa y recuperación independientes.

## Infraestructura verificada (2026-10-13)

- Proyecto existente de Supabase El Heraldo, organización Free.
- Bucket `heraldo-sqlite-backups` privado (`public=false`). Existen una generación cifrada de **laboratorio** y una de **producción**; la verificación de restauración de esta última se fundamenta en el informe de Codex local.
- Cuenta técnica de Auth creada y confirmada por el propietario; RLS de `storage.objects` permite exclusivamente `INSERT` y `SELECT` del bucket a esa identidad. No se otorgaron permisos de modificación ni eliminación. No se revelaron credenciales.
- En Railway Test se aplicaron seis variables y se verificó **su presencia, no sus valores**. El acceso cifrado funcionó en prueba real. Una identidad de servicio no debe reutilizarse indiscriminadamente con credenciales de producción.
- Restricciones documentadas del plan Free: 50 MB máximos por objeto y 1 GB de Storage; proyectos gratuitos pueden pausarse por inactividad. Subidas periódicas a Storage **no garantizan** actividad de base de datos suficiente para evitar la pausa. No prometer durabilidad ni periodicidad hasta verificarlas.

## Actualización H-03 — respaldo externo de producción (2026-10-13)

**REALIZADO SEGÚN INFORME DE CODEX LOCAL:** generada copia consistente SQLite mediante `Connection.backup` sin detener ni modificar el bot de producción. Se cifró externamente con AES-256-GCM usando clave distinta de la empleada en Test, se transfirió a Supabase con la cuenta técnica y se descargó, autenticó y restauró en SQLite aislada. El informe documenta integridad SQLite y claves foráneas correctas, coincidencia de esquema y contenido, prueba de rechazo de manipulación GCM y ausencia de cambios en producción. **Estas verificaciones de contenido/descifrado proceden del informe aportado por el propietario, no han sido repetidas por ChatGPT.**

**VERIFICADO INDEPENDIENTEMENTE POR CHATGPT (consulta 2026-10-13):** en Supabase Storage existe exactamente 1 objeto cifrado bajo la categoría de producción (100609 bytes) y 1 objeto de laboratorio; el bucket sigue privado y las políticas son solo INSERT/SELECT para usuarios authenticated restringidos por identidad. Railway producción sigue Online/SUCCESS con el despliegue anterior; Railway Test también Online/SUCCESS. No se leyó SQLite ni su clave, ni se modificó `main`.

**RIESGO PRIORITARIO:** la clave de descifrado de esta generación se conserva en un único equipo local según el informe. El propietario debe conservar una **segunda copia de la clave** en un medio seguro independiente (p. ej., gestor de contraseñas con recuperación u offline cifrado) y verificar acceso a ella. No publicar clave, rutas privadas, identificadores de generaciones, manifiestos ni datos en repositorio/Discord/chat. No repetir copia ni proceso de subida sin control de idempotencia; no hay aún protección continua.

**PENDIENTE:** periodicidad y supervisión de nuevos respaldos, política de conservación, segundo destino y disponibilidad ante pausas de Supabase Free, ensayos periódicos de restauración y cobertura independiente de adjuntos/evidencias externos de Discord. No implica autorización para desplegar `main`, restaurar producción ni ejecutar escrituras administrativas. Sin pruebas Discord en esta fase.

## Qué hace y qué NO hace

`supabase_backup.py` reutiliza `sqlite_recovery.validate_backup`. Comprime los dos archivos privados de H-03 (`database.sqlite`, `manifest.json`) en ZIP, cifra el ZIP completo con AES-256-GCM, nonce aleatorio y AAD versionada, y sube un único objeto nuevo al bucket. No admite sobrescritura, borrado ni claves S3 globales. La subida no incluye datos privados ni manifiestos en el mensaje de resultado. La descarga descifra, verifica GCM y pasa la comprobación H-03 (SHA-256, integridad/FK, esquema y entorno) antes de marcarla como correcta.

El operador debe descargar y verificar antes de considerar recuperable una generación. Una clave AES perdida vuelve irrecuperables las copias; guardarla únicamente en Railway también impide recuperar tras pérdida de credenciales. Mantener recuperación cifrada y clave en destinos separados y privados. **No subir la clave a Git, chat, logs ni al mismo bucket.**

No programa respaldos, no crea identidad de Supabase, no modifica `bot.py`, no lee `DB_PATH` automáticamente ni inicia/restaura producción. No prueba la coherencia de archivos Discord externos.

**Tamaño:** este formato admite un objeto cifrado de hasta 45 millones de bytes (margen bajo 50 MB), y base sin comprimir de máximo 150 millones de bytes. Superar límites BLOQUEA la subida; no divide un backup en múltiples partes. Si el tamaño de producción no cabe, revisar solución antes de cualquier publicación.

## Preparación segura de identidad (ya aplicada en Test; referencia para nuevas instalaciones)

1. Crear mediante Supabase Auth **una cuenta técnica exclusiva**, con correo controlado por el propietario, contraseña larga y correo confirmado. No reutilizar usuarios humanos ni claves `service_role`, `secret` o S3 globales.
2. Obtener el UUID real de esa cuenta desde Auth → Users (no colocarlo en Git). En SQL Editor de Supabase, sustituir **solo localmente** `UUID_DE_CUENTA_TECNICA` por ese UUID y ejecutar las dos políticas siguientes; no modificar otras políticas:

```sql
create policy "heraldo_h03_insert_only"
on storage.objects for insert to authenticated
with check (
  bucket_id = 'heraldo-sqlite-backups'
  and auth.uid() = 'UUID_DE_CUENTA_TECNICA'::uuid
);

create policy "heraldo_h03_read_only"
on storage.objects for select to authenticated
using (
  bucket_id = 'heraldo-sqlite-backups'
  and auth.uid() = 'UUID_DE_CUENTA_TECNICA'::uuid
);
```

No crear UPDATE ni DELETE. Comprobar que nadie más tiene políticas que otorguen acceso a este bucket. El bucket privado **no es suficiente** si otras reglas permiten leer sus objetos.
3. En entorno *Test* únicamente, inyectar estas variables mediante el gestor de secretos autorizado (nunca valores en texto en el repositorio):

```text
SUPABASE_BACKUP_URL=https://bzomavqthjhnukmaqocc.supabase.co
SUPABASE_BACKUP_PUBLISHABLE_KEY=<clave_publicable_o_anon_del_proyecto>
SUPABASE_BACKUP_EMAIL=<correo_cuenta_tecnica>
SUPABASE_BACKUP_PASSWORD=<contrasena_cuenta_tecnica>
SUPABASE_BACKUP_USER_ID=<UUID_de_cuenta_tecnica>
HERALDO_BACKUP_ENCRYPTION_KEY=<base64url_de_32_bytes_aleatorios>
```

Generar la última clave en un dispositivo seguro, conservar su copia fuera de Railway y no compartirla en esta conversación. Si Railway reinicia al guardar secretos, planificarlo y no aplicarlos en producción sin autorización separada. El módulo comprueba que el JWT de Supabase Auth corresponde al UUID configurado, además de las políticas RLS de servidor.

No confundir la clave **publishable** con la clave **secret**; esta última NO debe colocarse en el bot. La cuenta técnica se autentica con contraseña contra Auth, obtiene un JWT efímero y solo podrá usar las operaciones permitidas por RLS.

## Ensayo con datos sintéticos en laboratorio

Ejecutar los comandos en un checkout autorizado con Python y dependencias instaladas, nunca en un runner con secretos de producción:

```bash
python -m pip install -r requirements-backup.txt
# Crear /lab/synthetic.db desde un script de prueba sin datos reales.
python -m sqlite_recovery backup --db /lab/synthetic.db --destination /lab/h03 \
  --environment lab --revision COMMIT_VERIFICADO
python -m supabase_backup upload --package /lab/h03/PAQUETE --environment lab
python -m supabase_backup verify-remote --object lab/FECHA/OBJETO.h03e --environment lab
python -m supabase_backup fetch --object lab/FECHA/OBJETO.h03e \
  --environment lab --destination /lab/recuperacion
python -m sqlite_recovery verify /lab/recuperacion/PAQUETE_DESCARGADO --environment lab
```

Verificar *realmente* las siguientes propiedades: subida con cuenta dedicada, rechazo de otra cuenta no permitida, rechazo de lectura anónima, integridad de descarga, prueba de restauración en SQLite **aislado** con bot detenido y mismo esquema, bloqueo si clave/GCM incorrecta, y objeto sin posibilidad de UPDATE/DELETE. Documentar SHA, fecha, resultado saneado y conservación de la clave sin copiar datos.

## Activación futura en producción (no autorizada todavía)

- Confirmar ruta de DB, tamaño, espacio libre del volumen y disponibilidad de la identidad Supabase, además de cuota efectiva y pausas del plan Free.
- Preparar respaldo consistente H-03 de producción desde un proceso/ventana autorizados. Crear y verificar el paquete local; subirlo al bucket privado y descargarlo/verificarlo **fuera del volumen original**.
- Probar restauración del paquete descargado en destino aislado compatible, no en el volumen activo. Guardar referencia de objeto y SHA, no contenidos.
- Registrar monitoreo de fallos, calendario/retención con decisión explícita y un segundo destino ante pausas o pérdida de cuenta/proyecto. El programa actual NO elimina generaciones anteriores.
- No ejecutar actualización de `main` antes de estas comprobaciones y validación humana en Heraldo's Lab.
- Recordar que recuperar SQLite no recupera automáticamente los archivos/evidencias almacenados en Discord ni revierte acciones ya ejecutadas.

## Ensayo real de laboratorio — APROBADO (2026-10-13)

Railway Test ejecutó una única vez `python -m tools.supabase_smoke_test` mediante **pre-deploy** con tiempo máximo 180 s. La base se creó en un contenedor temporal sin volumen `/data`, no se leyó `DB_PATH`, no se inició `bot.py` dentro de la prueba y no se tocó Discord. Se creó respaldo H-03, se cifró/subió a `lab/`, se descargó y validó contra SHA e integridad, y se restauró a nueva SQLite aislada verificando filas sintéticas exactas. Log: `H03_SMOKE status=PASS scope=synthetic_no_discord`; deploy `ef2cc191-accd-4b9c-8ab3-4d07acf9fc87` SUCCESS, worker Online. Supabase confirmó 1 objeto de 766 bytes en `lab/`.

La configuración de pre-deploy se **retiró** tras la prueba; no se generarán nuevos objetos en futuros despliegues por este mecanismo. Test recuperó `python bot.py` como comando normal. Railway Railpack rechazó inicialmente un `-r requirements-backup.txt` anidado, porque faltaba ese archivo durante la instalación; se corrigió declarando `cryptography>=43,<47` directamente en `requirements.txt` de `Pruebas`. Los builds fallidos previos no completaron la prueba ni desplegaron producción.

**Este éxito no confirma que la base real de producción quepa, esté íntegra o sea recuperable.** Ese paso exige confirmar `DB_PATH`, acceso privado autorizado al volumen, tamaño, cuotas y restauración aislada, además de políticas de recuperación tras una pérdida de la cuenta de Supabase.

## Verificación automatizada

`tests/test_supabase_backup.py`: empaquetado real H-03 sintético, cifrado, manipulación, identidad, aislamiento por entorno, transporte remoto simulado y límite de tamaño. La suite de GitHub Actions instala `requirements-backup.txt` en entorno de CI aislado. **No equivale a una subida real**.

Documentación del proveedor:
- https://supabase.com/docs/guides/storage/uploads/file-limits
- https://supabase.com/docs/guides/platform/manage-your-usage/storage-size
- https://supabase.com/docs/guides/platform/free-project-pausing
- https://supabase.com/docs/guides/storage/security/access-control
