# Migración de El Heraldo Test a Enzonic — 29/10/2026

**Estado actual: SQLite histórica restaurada y ensayo H-03 real verificado;
Discord y aceptación final PENDIENTES.** Base auditada:
`Pruebas@5850def8f2f40619348e6eaddd3be3427ebb5456`; preparación desplegada por
fast-forward a `d52686f`. El bot continúa detenido en mantenimiento.
`main`, servicio oficial, volumen, variables, datos y respaldos de producción no
se modificaron. No se eliminó ningún recurso de Railway.

## Continuación operativa comprobada

El propietario autorizó Google y accedió al panel; al no disponer esta sesión de
control del navegador, ejecutó los comandos revisados y aportó sus salidas.
Free Tier confirmado por captura (512 MiB/1 GiB). Dependencias instaladas,
`pip check` correcto, variables Enzonic configuradas, DB_PATH corregido a
`/home/container/heraldo.db`, credenciales Test y AES conservados. La comprobación
REST confirmó `TEST_IDENTITY_VERIFIED` sin abrir Gateway. El marcador sobrevivió
al reinicio (`VERIFIED_AFTER_RESTART`). El recuperador original instaló la base
histórica (`VERIFIED_AND_INSTALLED`) y `inspect` dio `PREFLIGHT_VERIFIED`.

El ensayo remoto produjo `VERIFIED_AND_RESTORED` dos veces y también tras un
reinicio posterior; el conector confirmó una sola generación nueva de validación
en Supabase Test. La copia diaria adoptada fue verificada y su repetición devolvió
`ALREADY_VERIFIED`. La bandera Enzonic se habilitó después del ensayo. Railway Test
worker/cron siguen Offline y sus volúmenes se conservan. El bucle del programador
todavía no ha arrancado porque no se ha iniciado el bot.

Al repetir los 34 tests en el proveedor aparecieron dos fallos de simulación
Railway: la ubicación real de `host.__file__` seguía siendo `/home/container`.
La corrección aísla esa ubicación en el fixture y añade una regresión para
preservar el rechazo de identidad Railway desde la ruta Enzonic. No cambia
código de ejecución. Localmente pasan 35 tests en cada ubicación simulada
local/Railway/Enzonic, 85 regresiones de respaldo y compilación. Actualizar por
fast-forward y repetir las 35 en Enzonic. **No volver a ejecutar la restauración**
ni borrar bases o recibos para esta corrección.

Tras pasar esas pruebas, verificar de nuevo Railway Test apagado y restablecer
`python3 bot.py`. Faltan Gateway, programador a 06:15 UTC, consumo real, recorridos
Discord, footer Labs, reinicio y primer respaldo programado. Migración no finalizada.

## Comprobaciones de preparación (históricas, antes de esta continuación)

- Railway Test/Lab: worker y cron observados **Offline**, sin despliegues activos
  ni operaciones pendientes. Conservar ambos volúmenes y todos los respaldos.
- Supabase: bucket Test privado; RLS activa, identidad exclusiva con SELECT e
  INSERT. Las políticas Test examinadas no conceden UPDATE ni DELETE.
- La última generación listada corresponde al 29/10/2026, 06:15 UTC, 247 918 bytes.
  Hay 13 objetos Test que suman 2 183 153 bytes; total del proyecto 2 749 906 bytes.
  **Sólo se verificaron metadatos.** Descifrado e integridad de esa generación
  concreta están pendientes de disponer de la clave original en Enzonic.
- El navegador conectado no estuvo disponible. El navegador de Work abrió
  Enzonic sin sesión. El propietario seleccionó Google en la solicitud segura;
  la revisión automática bloqueó la observación de accounts.google.com porque
  requiere autorización explícita para ese destino adicional. No se intentó
  eludir el rechazo ni recuperar credenciales mediante otros mecanismos.

## Cambios implementados exclusivamente en Pruebas

| Parte | Comportamiento |
| --- | --- |
| `restore_enzonic_test.py` | Bloqueo exclusivo de servicio; rechazo de base/sidecars existentes, incluso enlaces colgantes; ausencia total de la bandera antigua; identidad Test; AES-GCM y SHA; recuperación aislada; instalación sin sobrescribir; integridad, FK, esquema y recuentos finales; recibo privado. |
| `enzonic_test_host.py` | Proveedor y entorno explícitos; montaje real; prueba de persistencia entre contenedores; identidad Supabase Test; revisión Git real de Pruebas; comprobación REST de la cuenta original del bot sin Gateway; arranque bloqueado sin migración verificada. |
| `enzonic_test_backup.py` | SQLite real; mismo cifrado H-03; ensayo remoto separado de la copia diaria; recibos durables; reconciliación de subidas inciertas mediante descarga; adopción de copia diaria anterior sin duplicarla; restauración aislada; cuotas y conservación. |
| `backup_job.py` | Ruta adicional exclusiva de Enzonic Test, sin cambiar las comprobaciones de producción; presupuesto del directorio completo de 1 GB; propósito de validación exclusivo de Test. |
| `test_backup_scheduler.py` | Bandera propia, prueba real previa obligatoria, ejecución auxiliar sin token Discord y sin bloquear el bucle del bot; 06:15 UTC, sin copia anticipada al reiniciar antes del horario. |
| `bot.py` | Identidad de laboratorio independiente de Railway; mismo footer Labs; bloqueo exclusivo local en Enzonic. El arranque de este código en el antiguo Railway Test sale con código 0 antes del Gateway para que un push no reactive una segunda instancia. |
| Dependencias | `requirements-enzonic.txt`: discord.py 2.7.1, cryptography 46.0.7 y Pillow 12.3.0, más las dependencias comunes. |

Los recibos y las generaciones locales se guardan en
`/home/container/.heraldo-h03-enzonic`, excluido de Git. No incluyen valores de
secretos. Nunca se borran generaciones remotas para obtener espacio.
Se reserva espacio para copia, descarga, restauración y 64 MiB adicionales.
El límite conservador remoto de Test es 100 MB, reservando hasta 45 MB por
operación. El worker limita su espacio de direcciones a 256 MiB y baja su
prioridad; rechaza fuentes lógicas mayores de 20 MB, incluyendo páginas en WAL.
Estos límites deben comprobarse contra el consumo real de Discord en Enzonic.

## Configuración que debe aplicarse tras acceder al panel

| Variables | Acción pendiente en Enzonic |
| --- | --- |
| `DB_PATH` | Conservar `/home/container/heraldo.db`. |
| `HERALDO_HOSTING_PROVIDER` | Añadir `enzonic`. |
| `HERALDO_ENVIRONMENT` | Añadir `heraldo-test`. |
| `HERALDO_TEST_BACKUP_ENABLED` | Eliminar la variable completa, incluso si está vacía o dice disabled. |
| Todas las `RAILWAY_*` | Retirar las identidades, dominios y rutas antiguas. La lógica del bot ya utiliza identidad neutral; los adaptadores de publicación Railway quedan archivados, no se ejecutan en Enzonic. |
| `HERALDO_BACKUP_VOLUME_CAP_MB` | Retirar el presupuesto Railway antiguo de 500 MB; Enzonic contabiliza el directorio completo frente a 1 GB. |
| `SUPABASE_BACKUP_*`, `HERALDO_BACKUP_ENCRYPTION_KEY` | Conservar valores originales de Test. Comprobar identidad y GCM sin imprimirlos. |
| `DISCORD_TOKEN` | Conservar sólo el token Test; `verify-token` comprueba por HTTPS la cuenta original corroborada en los logs anteriores, sin conectarse al Gateway. |
| `HERALDO_ENZONIC_BACKUP_ENABLED` | No crear hasta que el ensayo real termine; después usar `enabled-after-validation`. |
| `HERALDO_TEST_RECOVERY_OBJECT` | Seleccionar privadamente la última generación Test válida; no copiar la ruta a Git ni a logs. |

Inspeccionar también cualquier bandera productiva/H-03 copiada por error. El
preflight de Enzonic las rechaza. No cambiar claves ni tokens por esta migración.

## Secuencia operativa pendiente

1. Autenticar Enzonic; localizar el servidor correcto y comprobar plan gratuito,
   estado apagado, recursos y comando real. Verificar de nuevo Railway Test
   apagado antes de abrir el Gateway. No tocar producción.
2. Actualizar sólo el checkout Pruebas por fast-forward, sin reset, clean,
   reinstalación destructiva ni sustitución del directorio persistente. Verificar
   rama/SHA/archivos y aplicar las variables indicadas.
3. Instalar `python3 -m pip install --no-cache-dir -r requirements-enzonic.txt` y
   ejecutar `python3 -m pip check`, sin ejecutar bot.py.
4. Ejecutar `python3 -m enzonic_test_backup prepare-persistence`; reiniciar el
   contenedor con una operación de mantenimiento, **sin bot.py**; ejecutar
   `python3 -m enzonic_test_backup verify-persistence`. No sobrescribir el marcador
   si ya existe. Revisar después de la actualización que sigue presente.
5. Confirmar la última generación Test en Supabase y seleccionarla mediante
   `HERALDO_TEST_RECOVERY_OBJECT`. Con Discord detenido y sin base de destino,
   ejecutar `python3 restore_enzonic_test.py`. Sólo aceptar
   `HERALDO_TEST_RECOVERY status=VERIFIED_AND_INSTALLED`.
6. Ejecutar `python3 -m enzonic_test_backup verify-token` y
   `python3 -m enzonic_test_backup inspect`. Ante error, detener y diagnosticar;
   nunca crear una base vacía ni suplantar la identidad de Railway.
7. Ejecutar `python3 -m enzonic_test_backup validate`: debe subir, descargar,
   autenticar, comparar y restaurar una copia aislada real. Si la subida fue
   incierta, `python3 -m enzonic_test_backup recover --validation` sólo descarga y
   reconcilia; no vuelve a subir. No habilitar el planificador tras un fallo.
8. Sólo después, crear la bandera nueva y devolver el comando normal a
   `python3 bot.py`. Comprobar login, Gateway, presencia en Heraldo's Lab, datos
   históricos y cuota real de memoria. El recibo de migración mantiene el enlace
   con la base recuperada; cambios normales de filas no invalidan la comprobación.
9. Ejecutar recorridos auténticos sin sanciones innecesarias: /setup, Plantillas
   y programación, Honeypot, Verificación, Custodio, los tres idiomas, registros
   y expedientes, footer Labs y reinicio. Revisar el primer respaldo programado.

La consola del proveedor **no se ha inspeccionado**. No se asume que su entrada
acepte comandos de shell. Si hace falta cambiar temporalmente el arranque,
comprobar primero su política de reinicios y ejecutar cada operación una sola
vez; restaurar siempre `python3 bot.py` antes de la puesta en servicio.

## Verificación y límites de la entrega de código

Pruebas de cifrado, SQLite, instalación sin sobrescritura, bloqueo, identidad,
presupuestos, WAL, deduplicación, horario y recuperación incierta utilizan datos
sintéticos y transporte simulado. No prueban el objeto real de Supabase ni los
botones reales de Discord. Los resultados finales se registran también en los
tres documentos de coordinación.

Incidencia heredada: `test_no_unreviewed_literal_exemptions` falla también en un
checkout aislado del commit base 5850def. La auditoría i18n de esta entrega enumera 597 literales pendientes; no se añadieron exenciones para ocultarlos ni
se retiró el test. No convertir este fallo en una afirmación de traducción
completa. La migración y la aceptación real permanecen PENDIENTES.

Resultados locales finales: 1 160 componentes ejecutados (1 157 aprobados, un fallo heredado, dos omisiones), 39 pruebas raíz aprobadas, 34 regresiones Enzonic aprobadas, compilación y pip check correctos. CI remoto y verificaciones reales siguen pendientes.
