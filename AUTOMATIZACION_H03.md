## Preparación sin despliegue y recuperación aplazada — 2026-10-14

El propietario aplaza hasta noviembre de 2026 la verificación independiente de Bitwarden. Existe una nota privada importada con la clave original, pero NO se ha probado su recuperación/descifrado desde una sesión o dispositivo independiente ni la recuperación de acceso a la bóveda. No tocar la clave, no repetir la importación y no ejecutar operaciones productivas que dependan de ese requisito. Esto permite seguir preparando y verificando código con datos sintéticos.

Base de trabajo: Pruebas 13af6c31fc97e8528bf03e571305b9c6b688a539. Main sigue 6f9f9ee0a7ed1c7b7e6c48a13817b9b5f3a5b667. Producción SUCCESS en bbb21914-a87c-44f3-b862-f4ba3ceecd09, sin cambios pendientes. Test SUCCESS, start python bot.py, preDeploy vacío; no se cambiaron sus secretos ni configuración para ejecutar pruebas.

Defecto corregido en backup_job._isolated_restore: SQLite creaba el destino con permisos dependientes de umask (habitualmente 0644). Ahora se reserva con O_EXCL/O_NOFOLLOW y modo 0600 antes de abrir SQLite; no se cambia umask global desde el hilo del bot, ni se sobrescribe un destino existente. Dos regresiones nuevas verifican privacidad con umask 022 y conservación del archivo existente.

Verificación Linux aislada en Railway Test: compilación, pip check, 39 regresiones históricas y 218 de tests/ aprobadas (257). Transporte simulado, sin credenciales en el proceso hijo, sin importar/iniciar el bot para operar Discord. Warnings no fatales preexistentes en mocks. No son pruebas humanas Discord ni prueba productiva.

Siguiente etapa realizada: tools/prepare_h03_candidate.py construye en directorio NUEVO un candidato basado exclusivamente en main fijo, añade cuatro módulos H-03 y cryptography, e inserta un hook protegido por bandera antes de importar dependencias. Una comparación AST comprueba que el resto de bot.py es idéntico. No crea ramas, no publica main ni despliega. La primera ejecución local encontró un error de indentación del comprobador; corregido y candidato válido generado en otro directorio, conservando el anterior.

Candidato ensayado en proceso aislado de Railway Test: 29 regresiones históricas disponibles en main, compilación y dependencias correctas; extracción AST de db_connect/db_init sin ejecutar el módulo del bot, creación de esquema sintético de main, fila sintética, inicialización candidata, backup y restauración nueva y vuelta a inicialización main. Esquema y contenido coinciden; H03_CANDIDATE_PASS. Programador sin bandera no inicia. Ninguna migración nueva se incorpora al candidato. Esto valida compatibilidad sintética del cambio mínimo; NO sustituye instantánea productiva reciente ni aceptación funcional real antes de desplegar.

Pendientes: recuperación independiente en noviembre, alerta con entrega comprobada, auditoría final de candidato/credenciales y nueva instantánea justo antes del futuro despliegue autorizado. El PR 16 no se integró. No hay respaldo diario real de producción activado ni borrado de copias. Revisar CI y autodespliegues del commit de esta etapa antes de atribuirles éxito.

## Integración productiva preparada con activación por fases — 2026-10-14

**AUTORIZACIÓN DEL PROPIETARIO:** proceder con la preparación, las pruebas y posteriormente desplegar `main`/Railway producción **una vez** verificadas claves independientes, recuperación, compatibilidad SQLite, revisión de cambios y reversión. No autoriza omitir esas precondiciones ni borrar/restaurar datos productivos.

**CÓDIGO IMPLEMENTADO SOLO EN `Pruebas`:** `production_backup_scheduler.py` (opt-in estrictamente condicionado) y llamada en `bot.py:on_ready`. El bot propietario del volumen programa H-03 diariamente a las **06:15 UTC (02:15 Santo Domingo)** con `discord.ext.tasks.loop`; offload mediante `asyncio.to_thread`, nunca se lanza otro bot ni se comparte el volumen. Antes de programar y antes de cada ejecución se verifican IDs Railway exactos, `DB_PATH` bajo `/data`, SHA de despliegue, bandera `HERALDO_PRODUCTION_BACKUP_ENABLED=enabled-after-owner-approval`, clave de 32 bytes, configuración Supabase y cuota `HERALDO_BACKUP_VOLUME_CAP_MB=500`. En ausencia de bandera no arranca ninguna tarea, no escribe SQLite ni lee credenciales. Operaciones idempotentes bajo `/data/.heraldo-h03-daily`, sin purga.

**VERIFICADO AUTOMÁTICAMENTE EN RAILWAY TEST:** 10/10 regresiones del planificador (`tests/test_production_backup_scheduler.py`), más `216/216` pruebas del directorio `tests/` y `39/39` regresiones históricas. El primer intento de suite completa falló **por patrón de shell sin comillas**; se corrigió y volvió a ejecutar con `-p 'test_*.py'`, alcanzando `OK`. Se retiraron los comandos pre-deploy después de cada ensayo. No hubo interacciones reales Discord ni ninguna ejecución productiva de H-03.

**IMPEDIMENTOS REALES VERIFICADOS:** Railway producción todavía solo tiene los nombres de variables `DB_PATH`, `DISCORD_TOKEN` y `MESSAGE_CONTENT_INTENT`: no existe allí `HERALDO_BACKUP_ENCRYPTION_KEY` ni la identidad Supabase de respaldos, ni la bandera de activación. La clave usada para descifrar la generación productiva existente permanece fuera de Railway en el PC del propietario según Codex local; no se ha confirmado una **segunda copia accesible e independiente**. No hay acceso desde este conector al llavero local/SSH del PC para copiar y probar esa clave. La vigilancia de ChatGPT detecta antigüedad pero tiene notificaciones desactivadas. **NO desplegar ni habilitar main aún.**

### Secuencia segura pendiente para producción

1. Usar Codex local autorizado en el PC del propietario para **crear segunda copia segura e independiente** de la clave existente (gestor cifrado u offline protegido), y comprobar desde ella un descifrado aislado del objeto existente, sin exponer clave/SQLite en chats, repositorios o registros. No reemplazar la clave ni la generación existente.
2. Seleccionar ejecutor dueño del volumen y preparar un despliegue **mínimo** a `main`, sin fusionar todo `Pruebas`: comparar archivos y esquemas `main`/candidato, utilizar el preflight SQLite y ensayar `main → candidato → recuperación` contra copia sintética; revisar PR #16 sin integrarlo a ciegas.
3. Obtener una **instantánea nueva consistente de producción** y restaurarla de modo aislado antes de cualquier redeploy. Mantener copias previas y posibilidad real de revertir la revisión de software; no rebobinar SQLite ni sanciones/roles de Discord automáticamente.
4. Preparar versión desactivada con únicamente dependencias H-03 y el hook opt-in; al desplegar, verificar bot Online, Gateway, que los respaldos NO se ejecutan sin bandera y que el servicio no pierde datos. Revertir si hay pérdida de funcionalidad.
5. Configurar mediante secretos protegidos **exclusivos de producción** la clave custodiada, el acceso técnico de Supabase y `HERALDO_BACKUP_VOLUME_CAP_MB=500`; ejecutar comprobación de credenciales/objeto y descifrado sin registrar valores. No reutilizar credenciales de Lab ni transportar claves por Git o el chat.
6. Con todos los gates anteriores correctos, activar `HERALDO_PRODUCTION_BACKUP_ENABLED=enabled-after-owner-approval` mediante cambio revisado de Railway producción y comprobar en la **primera ejecución real programada** que existe una sola nueva generación, con descarga autenticada, SHA/GCM, restauración nueva, salud y registro; verificar que el bot nunca se detuvo salvo el redeploy controlado. Si se exige un primer disparo inmediato, planificarlo de forma segura y no alterar el reloj ni borrar recibos.
7. Confirmar que las notificaciones del monitor productivo se pueden recibir; someter una alerta sintética a verificación antes de considerar completa la protección. No asumir notificaciones de ChatGPT con canales desactivados. Auditar cuota/retención por crecimiento sin eliminar generaciones automáticamente.

**Rollback:** ante fallo o falta de requisitos, dejar `HERALDO_PRODUCTION_BACKUP_ENABLED` sin configurar, mantener la versión anterior de bot/despliegue y conservar respaldos, volúmenes, SQLite, tokens y recibos intactos. No realizar restauración destructiva como respuesta automática a fallos del planificador. Si el código ya se desplegó, desactivar la bandera (provocará redeploy controlado) y restaurar la versión de software previa solo con revisión de esquemas y estado actual.

## Capacidad y cuotas: protección añadida (2026-10-14)

`backup_job.py` ahora exige capacidad libre equivalente a tres copias SQLite más 64 MiB antes de marcar un intento; si falla, detiene la operación sin subir ni borrar nada. Cuando se configure `HERALDO_BACKUP_VOLUME_CAP_MB`, también considera el tamaño de todos los ficheros del volumen y el límite conservador indicado, no solo el free que devuelve `statvfs`. `RAILWAY_VOLUME_MOUNT_PATH` define el montaje o se utiliza `/data` por defecto. El presupuesto inválido o montaje incompatible producen bloqueo seguro. Verificación: 10/10 pruebas en Railway Test, commit `28a4063`.

El cron de laboratorio tiene valor de cuota `500` MB, coherente con su volumen. Esto NO realiza rotación ni libera espacio; requiere una política futura de conservación revisada, comparaciones contra disponibilidad remota y consentimiento específico para cualquier eliminación. En producción, presupuesto/secretos/horario deben definirse y verificarse antes de activar un ejecutor. Los respaldos anteriores se conservan.

## Refuerzo de salud y bloqueos operativos (2026-10-14)

La regresión del verificador de laboratorio exigía información demasiado débil: un recibo `verified_and_restored` sin fecha de finalización podía figurar `OK`. Se cerró con 14 pruebas ejecutadas en Railway Test (`Ran 14 tests`, `OK`) y validación de identidad, período, tiempos y permisos. El servicio cron real de Lab ya había demostrado una ejecución programada y una segunda no-op sin repetición. No hay cron real de producción.

**Alertas:** consulta de tareas ChatGPT muestra vigilancia productiva habilitada, pero notificaciones de la app y correo desactivadas; no se debe afirmar entrega fiable. La monitorización local Codex Lab depende de la disponibilidad del PC y aún no acredita entrega. Habilitar y probar un canal real antes de considerar la cadena de alertas completa, manteniendo una sola fuente por incidente.

**Capacidad:** el servicio cron conserva generaciones, descargas y restauraciones en el volumen sin retención destructiva; validar capacidad y establecer límites de uso antes de introducir datos de producción. Los objetos cifrados en Supabase Free no sustituyen una estrategia de disponibilidad/clave. La clave real requiere segunda copia independiente y verificación de recuperación. Ninguna operación de producción ni borrado de copias queda autorizada por esta documentación.

# Operación H-03 de laboratorio y propuesta de producción

## Alcance autorizado el 2026-10-14

Servicio independiente `heraldo-h03-lab-cron`, exclusivamente `Pruebas`, en el
proyecto Railway Test. Inicio `python -m tools.scheduled_lab_backup`, restart
`NEVER`, sin pre-deploy ni credenciales Discord/DB_PATH. Volumen propio de 500 MB
en `/data`, sin compartir el volumen de worker. Las seis referencias de secretos
apuntan a la identidad/clave de laboratorio existentes; no a la clave productiva.
No hay cambios funcionales en bot.py, main ni configuración del worker.

La validación inicial usa cron cada cinco minutos y una frontera UTC de activación
para que el primer respaldo completo lo ejecute el programador, no el despliegue.
Tras verificar un disparo programado completo y una segunda invocación manual se fija la frecuencia diaria a las 06:15 UTC
(02:15 America/Santo_Domingo). El período de idempotencia siempre es el día UTC.

## Estados, conservación y fallos

El bloqueo fcntl y el recibo privado durable se crean antes de la subida.
`verified_and_restored` permite que otra ejecución del mismo período termine
como `ALREADY_ATTEMPTED` sin tocar Supabase. Cualquier recibo incompleto, corrupto
o incierto impide reintentos y sale con error. Se conserva `failed_stage`.
No se promete exactamente una operación remota frente a una respuesta perdida:
se bloquea el reintento y se requiere reconciliar el objeto, nunca borrar recibos.

Las generaciones, descargas y restauraciones se conservan por período en el
volumen privado, sin rotación destructiva. La restauración abre únicamente un
archivo nuevo; compara esquema, versiones, recuentos y huellas de todas las filas.
El proceso tiene un límite de 180 segundos y cierra conexiones al terminar.
Un SIGKILL puede dejar `started`/`upload_unconfirmed`: el siguiente proceso lo
trata como fallo, no como éxito ni autorización para volver a subir.

`python -m tools.backup_health` inspecciona recibos sin contenidos privados:
no_attempt, invalid_receipt, attempt_needs_review, missing_period y stale (>36 h).
Identifica días UTC cerrados sin recibo desde el primer intento; el primer día
sin historial necesita vigilancia externa. Los logs del cron incluyen únicamente
estados saneados y fecha de período. Nunca imprimir URLs firmadas, hashes de
bases, manifiestos, objetos privados, secretos o filas.

## Contrato con la vigilancia existente

La vigilancia previa de ChatGPT controla exclusivamente antigüedad/metadatos de
producción. No debe tomar objetos `lab/` como evidencia de producción. La señal
de laboratorio se identifica como `lab:<motivo>`; emitir un aviso al abrir o
cambiar incidencia y otro al recuperarse, no repetir avisos idénticos.
Consultar ejecuciones cron de Railway y sus logs, además de metadatos agregados
de `lab/`. Un objeto presente por sí solo no acredita descarga/restauración:
exigir `VERIFIED_AND_RESTORED` y salida correcta. Si no corre el programador,
un proceso dentro del mismo cron no puede detectarlo: la vigilancia debe ser
externa, diaria, independiente del arranque del servicio. No notificar éxitos
ordinarios. El bot Discord no enviará estas alertas.

Se creó la automatización local de Codex `Vigilar H-03 de laboratorio`, diaria
a las 08:00 America/Santo_Domingo, en este mismo chat. Consulta solo Test y
metadatos Lab, conserva estado mínimo por incidencia y no duplica alertas
productivas. Depende de que el equipo esté encendido y Codex disponible; no
equivale a un monitor alojado continuamente. La vigilancia previa de ChatGPT
no es editable desde esta conexión y no fue modificada. Su integración queda
definida por la separación de ámbitos y el contrato anterior. No se ha probado
todavía un disparo programado de esta nueva vigilancia ni su entrega de avisos.

## Producción: procedimiento propuesto, NO activado

1. Aprobar arquitectura antes de tocar main: Railway no permite compartir el
   volumen entre dos servicios. La opción que conserva el esquema actual es un
   disparador externo autorizado por SSH que ejecuta el backup en el contenedor
   propietario del volumen, con Connection.backup y origen mode=ro. Descargar
   exclusivamente la generación terminada para cifrar/transferir fuera del bot.
   Requiere un ejecutor disponible continuamente: una computadora apagada no es
   un programador fiable. Alternativa: proceso auxiliar supervisado dentro del
   servicio dueño del volumen, mediante cambio revisado de inicio/deploy; nunca
   iniciar un segundo bot ni compartir DB por red. Ambas requieren aprobación.
2. Confirmar DB_PATH en privado, identidad y SHA real, tamaño y espacio/cuota.
   WAL activo se respalda con API SQLite, nunca copiando solo el archivo activo.
   Guardar recibo durable y reservar espacio antes del intento. Mantener una
   generación verificable local; no eliminar las anteriores automáticamente.
3. La clave productiva existente permanece fuera de Railway. Antes de usarla en
   un ejecutor, aprobar su destino, acceso mínimo y recuperación tras reinicio.
   Custodiar una segunda copia independiente y comprobar un descifrado desde ella.
   No sustituirla por la clave Lab ni ponerla junto al ciphertext en Supabase.
4. Revisar identidad técnica y RLS específicas de producción, INSERT/SELECT sin
   UPDATE/DELETE. Comprobar acceso, cuotas y disponibilidad; Free puede pausarse,
   no garantiza servicio continuo. Límites del formato: objeto 45 MB y SQLite
   150 MB; si se exceden, bloquear y revisar solución, nunca truncar/dividir a ciegas.
5. Exigir download autenticado, GCM, SHA-256, integridad/FK y restauración a nuevo
   destino aislado, sin Gateway. Solo entonces marcar verificado. Los errores o
   respuestas perdidas se conservan para revisión, sin reintento automático.
6. Integrar producción en la vigilancia ya existente (36 h), un único propietario
   de alertas y estado por incidencia; no crear un segundo aviso productivo.
7. Retención: solo inventario/plan, con revisión de espacio y disponibilidad.
   Cualquier borrado requiere aprobación distinta y evidencia recuperable externa.
8. SQLite no incluye adjuntos/JSON de Discord. Su copia independiente requiere
   inventario, permisos, hashes, cifrado y almacenamiento propio autorizados.
   Restaurar datos antiguos exige reconciliar acciones posteriores de Discord.

Autorización pendiente de producción: arquitectura/disparador y horario, destino
de secretos y segunda custodia comprobada, cambios exactos de main/despliegue si
se elige el proceso auxiliar, identidad externa y alcance operativo. La validación
de laboratorio no concede esa autorización. Ninguna restauración productiva se
incluye en esta etapa.

## Evidencia

Los resultados efectivos de ejecución, SHA, CI y cambios de horario se registran
en PRUEBAS_DISCORD.md y CONTINUIDAD_AGENTES.md. Las pruebas offline no se presentan
como llamadas reales a Supabase ni como pruebas humanas Discord.

Referencias: https://docs.railway.com/cron-jobs,
https://docs.railway.com/volumes,
https://supabase.com/docs/guides/storage/security/access-control.
