# H-03 — Respaldo SQLite y recuperación offline

## Continuación de verificación — 2026-10-12

Estado Railway reconsultado: producción heraldo-data y Test worker-volume en
`/data`, 500 MB. Las variables devuelven `valuesRedacted=true`: no se conoce el
DB_PATH efectivo. No hay shell, archivos ni listado de backups accesibles por el
conector; CLI/credenciales locales tampoco disponibles. No afirmar ausencia de
copias: existencia, fecha, privacidad, integridad y recuperación siguen sin verificar.
Railway documenta [backups de volumen](https://docs.railway.com/volumes/backups),
incluido SQLite; ver detalles y permisos mínimos en INFORME_ISSUE15.md. No se
crearon/restauraron backups ni se contrataron recursos. El snapshotId asociado al
despliegue no prueba respaldo del volumen. Restaurar Railway implica cambio de
volumen y despliegue; no es una comprobación de lectura.

El ensayo reforzado comprueba integridad/FK, tablas/índices/triggers/vistas,
versiones, inicialización repetida de módulos y restauración sintética exacta.
215 tests totales correctos. No sustituye una generación privada real descargable,
recuperación aislada sin Gateway ni reconciliación de evidencias en Discord.

## Verificación vigente issue #15 — 2026-10-12

H-03 ya está en Pruebas c01aa4d. Lectura Railway confirma volumen producción
heraldo-data /data 500 MB y Test worker-volume /data 500 MB; no acredita espacio
libre, ruta DB_PATH, paquetes existentes ni respaldo externo recuperable. El
preflight de lectura está en sqlite_preflight.py y su procedimiento/límites en
INFORME_ISSUE15.md. Cero escrituras en archivos requiere vista read-only del
conjunto DB/WAL/SHM; mode=ro impide escribir tablas pero puede usar metadatos SHM.
Ensayo sintético main→Pruebas conserva esquema/datos previos, añade cuatro tablas
y permite restaurar copia main en destino nuevo aislado. La igualdad estricta de
schema-from impide reemplazar directamente una base ampliada con snapshot antiguo;
no eludirla ni borrar sidecars. Restaurar snapshot requiere reconciliar Discord y
conservar estado posterior. Una reversión de imagen no revierte el volumen.

Implementación local para revisión; no configura Railway, almacenamiento externo
ni tareas programadas. Las pruebas usan bases sintéticas. No restaurar producción.

## Persistencia comprobada en el código

- `DB_PATH` apunta a `heraldo.db` por defecto. La documentación de Test declara
  `/data/heraldo.db` y un volumen de 500 MB; no se pudo consultar Railway en esta
  sesión, por lo que no se acredita su estado ni capacidad libre actuales.
- `db_init` activa WAL y `synchronous=NORMAL`. `db_connect` usa autocommit,
  `busy_timeout=2000` y conexiones cortas; algunas operaciones agrupan escrituras
  con `BEGIN IMMEDIATE`. No hay checkpoint global automático implementado por el
  bot: SQLite conserva su comportamiento de checkpoint al cerrar y por tamaño.
- `guild_cases`, `guild_settings` (incluidos roles pendientes), miembros,
  programaciones, reportes y `evidence_archive_v1` viven en la misma base. Una copia
  completa conserva los servidores sin seleccionar ni mezclar filas.
- El ledger H-02 conserva estados `pending`/`complete` y recibos con hashes y
  referencias. Los JSON y adjuntos están en Discord, **fuera de SQLite**.
- Discord y SQLite no comparten transacción: una operación remota puede terminar
  antes de persistir su resultado. Restaurar una copia antigua puede reintroducir
  tareas o casos pendientes. No conectar automáticamente la copia restaurada al
  Gateway ni repetir acciones inciertas antes de reconciliar esos registros.

## Respaldo consistente

Desde el checkout, con el Python preparado en `.venv`, indicar explícitamente
base, entorno y versión. Los nombres siguientes son ejemplos; confirmar las
rutas efectivas antes de ejecutarlos sobre un laboratorio autorizado.

```bash
.venv/bin/python -m sqlite_recovery backup \
  --db /data/heraldo.db --destination /data/backups \
  --environment heraldo-test --revision SHA_DEL_CODIGO
.venv/bin/python -m sqlite_recovery verify /data/backups/PAQUETE \
  --environment heraldo-test
```

`Connection.backup` copia una instantánea consistente, incluido WAL confirmado;
no hace una copia directa del archivo activo ni fuerza un checkpoint. Copia por
lotes y abandona por timeout o error. Comprueba espacio disponible antes de
copiar; el crecimiento concurrente o una cuota no visible todavía pueden causar
un error de escritura que no publica una copia parcial.

Cada generación nueva contiene `database.sqlite` y `manifest.json`: fecha UTC,
revisión indicada, versión SQLite, tamaño, SHA-256, huella del esquema,
`user_version`, `application_id`, recuentos por tabla y resultado. Se comprueba
`integrity_check` y `foreign_key_check` antes de publicar. Los recuentos y nombres
de tabla permanecen dentro del paquete privado, no se imprimen los registros.
La suma detecta corrupción; **no es una firma ni protege frente a un operador
capaz de alterar también el manifiesto**.

Carpetas 0700 y archivos 0600; se rechazan destinos compartidos o symlinks. La
publicación es una renombración atómica después de fsync. No se sobrescriben
generaciones anteriores. `.partial-*` tras una muerte abrupta no es una copia
válida y no se elimina automáticamente al reiniciar. Verificar las generaciones
publicadas; si fsync falla después de renombrar, revisar la copia aunque el comando
haya devuelto error. El soporte validado de respaldos/restauración es Linux/POSIX;
no se acredita protección por ACL ni durabilidad del paquete en Windows.

## Conservación prudente, sin borrado automático

```bash
.venv/bin/python -m sqlite_recovery retention-plan \
  --destination /data/backups --environment heraldo-test \
  --keep-min 7 --max-age-days 30
```

La política es configurable y solo produce candidatos: preserva al menos una
copia validada (siete por defecto), no propone las recientes y conserva entradas
no verificables para revisión. **No borra ningún paquete ni evidencia.** Antes de
eliminar una generación se necesita una decisión específica y comprobar una copia
externa recuperable. Revisar el espacio antes de programar frecuencia/conservación:
en un volumen pequeño, siete copias podrían no caber. La programación del comando
en Railway sigue pendiente de revisar el servicio y confirmar su alcance.

## Restauración segura y recuperación del servicio

1. Detener todos los procesos del servicio de Test y confirmar que no existe otra
   réplica, proceso antiguo ni tarea que use SQLite. `--service-stopped` expresa
   esa confirmación; no detiene servicios por sí mismo.
2. Mantener una versión del código y una base de referencia del esquema esperado.
   Puede ser una base vacía de laboratorio inicializada con la misma versión y
   tablas opcionales. El esquema debe coincidir exactamente: tablas, índices,
   triggers, versiones e ID de aplicación. Si cambió, parar y revisar una migración
   por separado; la herramienta no inventa migraciones ni descarta tablas.
3. Validar el paquete y su etiqueta de entorno. Para un ensayo, usar una base nueva
   en carpeta temporal; nunca reutilizar rutas de producción.

```bash
.venv/bin/python -m sqlite_recovery restore /RUTA_PRIVADA/PAQUETE \
  --db /RUTA_LAB/restaurado.db --schema-from /RUTA_LAB/esquema.db \
  --environment heraldo-test --service-stopped
```

4. El proceso mantiene un bloqueo exclusivo sobre `DB_PATH.service.lock`. El
   arranque normal de `bot.py` mantiene el bloqueo compartido durante `bot.run`;
   mientras haya un proceso actualizado conectado, la restauración se rechaza.
   El bloqueo es cooperativo: otros programas o versiones antiguas pueden no
   respetarlo. No sustituye detener y revisar todos los procesos. No borrar el
   archivo de bloqueo para sortearlo.
5. Se rechaza una base con WAL/SHM/journal presentes. No borrar estos archivos:
   pueden contener transacciones necesarias. Con el servicio detenido, conservar
   el conjunto y diagnosticar la recuperación SQLite en una copia de laboratorio.
6. Se valida una copia privada del respaldo antes de instalarla. Si existe una
   base anterior compatible, se crea primero una generación validada en
   `.recovery-history/`; si falla, la base anterior no se reemplaza. La sustitución
   final es atómica y el resultado informa la copia anterior para rollback.
   Un fallo después de sustituir/fsync requiere verificar qué generación está
   instalada; no iniciar automáticamente el servicio ante un resultado incierto.
7. Comprobar casos, roles, servidores, estados pendientes y referencias de evidencia
   en el laboratorio, sin copiar contenidos a logs. La prueba automatizada incluye
   relaciones, aislamiento y lectura de roles por el código real del bot.
8. Reconciliar manualmente operaciones Discord posteriores al punto de respaldo:
   recibos completos deben verificarse contra archivos remotos; recibos pendientes
   y envíos inciertos requieren revisión. Una copia SQLite no recupera adjuntos
   que hayan desaparecido de Discord, ni garantiza exactamente una ejecución.
9. Solo después de revisión y autorización de laboratorio, iniciar la versión
   compatible con `DB_PATH` y credenciales exclusivas de Test. Verificar Gateway y
   luego interacciones reales. Para rollback offline, restaurar la generación
   `previous_backup` con el mismo procedimiento; también conserva la base sustituida.

## Protección ante pérdida completa del volumen

Una copia en `/data/backups` **no protege frente a la pérdida de `/data`**. Opciones
a evaluar con el propietario: un destino privado externo ya autorizado (servidor
de respaldos o almacenamiento de objetos privado con versionado), copia cifrada
en un equipo del administrador, o un servicio de respaldo gestionado que confirme
restauración de volúmenes. Se requiere comprobar disponibilidad, costes, ubicación,
control de acceso, gestión de claves y ensayo de descarga/restauración. Ninguna
opción quedó conectada ni se crearon buckets, servicios o credenciales.

SQLite más el ledger permite localizar evidencias en Discord; para recuperación
independiente también haría falta exportar y verificar los JSON/adjuntos en el
destino externo aprobado. No almacenar datos privados en GitHub, artifacts públicos
de CI ni snapshots de desarrollo compartidos. No hay retención destructiva.

## Validación y límites

Las regresiones prueban integridad, WAL con transacciones confirmadas/no confirmadas,
escrituras concurrentes, espacio insuficiente, fallos de escritura, timeout,
interrupción real de subprocess, reinicio, restauración/rollback, bloqueo entre
procesos, esquema, checksums, claves externas, permisos y conservación de estados
de evidencia y roles. Se prueban SQLite y temporales sintéticos; no se inició el bot
ni se copiaron o restauraron bases reales. Pruebas humanas, respaldo externo,
programación Railway y recuperación de archivos de Discord: pendientes.
