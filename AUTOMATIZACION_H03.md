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
