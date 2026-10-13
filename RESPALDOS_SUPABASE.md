# H-03 → Supabase Storage: respaldo externo cifrado

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
