# Issue #15 — Preparación verificable de actualización

Fecha: 2026-10-12 (America/Santo_Domingo). Responsable técnico: Codex.
**Producción NO está lista para actualizar.** No se modificaron main, Railway,
configuración, datos reales ni Discord. Esta propuesta va exclusivamente a Pruebas.

## Revisiones y evidencia actual

- main: `6f9f9ee0a7ed1c7b7e6c48a13817b9b5f3a5b667`.
- Pruebas/base de la tarea: `c01aa4d487b27f42610f0d182243b650cb52eddf`.
- Rama: `codex/issue15-preflight-20261012`; consultar el HEAD del PR para la
  revisión final. No se fusiona automáticamente ni se abre PR hacia main.
- main es ancestro de Pruebas (`git merge-base --is-ancestor`). H-03 ya está
  integrado mediante PR #14; no repetir ni integrar la rama histórica otra vez.
- CI de la base exacta: [Lab, 38291614080](https://github.com/ElCreador5/el-heraldo-bot/actions/runs/38291614080)
  y [Mensajes, 38291614066](https://github.com/ElCreador5/el-heraldo-bot/actions/runs/38291614066),
  ambos completed/success. El wrapper de workflows del conector filtra eventos PR;
  devolvió lista vacía para este push. Se comprobó la colección GET de Actions.
- Test: proyecto `747a1ee0-cdab-4ad5-8e45-a6ddfccc9b61`, entorno
  `71b77daf-9092-4af0-913f-32c57367fff3` (llamado production **dentro del proyecto
  independiente de Test**), worker `13a555fc-7ddd-4712-a9bc-e88509e18b2b`.
  [Despliegue ceb9b727](https://railway.com/project/747a1ee0-cdab-4ad5-8e45-a6ddfccc9b61/service/13a555fc-7ddd-4712-a9bc-e88509e18b2b?id=ceb9b727-ab69-4798-9257-78104230ba19&environmentId=71b77daf-9092-4af0-913f-32c57367fff3)
  SUCCESS, SHA completo igual a la base. Una réplica, volumen worker-volume,
  `/data`, capacidad 500 MB, sin buckets ni cambios staged.
- Producción: proyecto `1edabae7-53ff-4a6c-ad55-a1dc0b865b4f`, entorno El Paraíso
  `a2ce7142-f315-4ab9-8d6e-ad058c1dc9fc`, servicio
  `78a0bdb2-95aa-41e0-8785-32ba17ffeb70`: fuente main, despliegue
  `bbb21914-a87c-44f3-b862-f4ba3ceecd09` SUCCESS, una réplica, heraldo-data
  `/data`, capacidad 500 MB. Sin buckets ni staged. Fuente con checkSuites=false:
  una futura publicación en main podría desplegar antes de completar CI.
  No se verificó aquí el SHA de la imagen de producción ni el espacio libre.
- Railway describe-service muestra nombres DB_PATH, DISCORD_TOKEN y
  MESSAGE_CONTENT_INTENT; no se consultaron sus valores. No se presupone la ruta
  efectiva de DB_PATH a partir de la existencia de /data.

## Estado de los bloqueadores

| Área | Estado | Evidencia / límite |
|---|---|---|
| Respaldo real recuperable | PENDIENTE | El inventario confirma volumen, no acceso a sus archivos, backups del proveedor ni validez de copias externas. Sin buckets no implica ausencia de un destino externo. |
| SQLite sintético | VERIFICADO AUTOMÁTICAMENTE | Inicializadores reales main/Pruebas, DDL literal opcional, estados de dos servidores y copia/restauración H-03. |
| Preflight de lectura | IMPLEMENTADO y VERIFICADO AUTOMÁTICAMENTE | sqlite_preflight.py, cuatro regresiones; NO ejecutado contra producción. |
| Regresiones de los cambios | VERIFICADO AUTOMÁTICAMENTE | 207 tests offline: 39 raíz/Logs + 168 tests; no acredita todas las rutas reales. |
| CI/Test de la base | VERIFICADO AUTOMÁTICAMENTE | Links y SHA anteriores; CI del nuevo PR se registra separadamente. |
| Interacciones en laboratorio | PENDIENTE / no realizadas | Sin cuentas humanas controlables; no self-bot, ni ensayo en producción. |
| Lanzamiento | IMPLEMENTADO como procedimiento | Ejecución bloqueada por respaldo y aceptación del laboratorio; falta aprobación específica de main. |

## Compatibilidad y conservación

`tools/check_sqlite_upgrade.py` usa AST para ejecutar los cuerpos **reales** de
db_connect/db_init/honeypot_db_init/suggestion_db_init y CREATE TABLE literales de
cada revisión. No importa el bot ni inicia tareas/Gateway. Ejecuta además
ScheduledMessages.initialize y el ledger de evidence_archive actuales.
Los datos son sintéticos y viven en TemporaryDirectory.

Resultado: columnas existentes sin cambios, filas existentes conservadas,
inicialización repetida sin pérdidas, inicializadores main capaces de abrir el
esquema ampliado y restauración exacta de la copia anterior. Tablas nuevas:
pending_join_roles, message_schedule_state, message_autoresponse_rate,
evidence_archive_v1. No acredita esquemas históricos distintos, toda la migración
de JSON/configuración ni todos los estados posibles de producción. Ambas revisiones
usan user_version sin una migración versionada que por sí sola pruebe compatibilidad.

Comparación AST de símbolos de primer nivel: 512 idénticos, 109 modificados, 51
nuevos, ninguno eliminado. Es inventario estructural, **no prueba de equivalencia**.
Los cambios relevantes son confirmaciones de setup, aislamiento/permisos, condenas
y roles pendientes, exclusión entre temporizadores, barrera de evidencias y Mensajes.
Se reutilizaron las regresiones runtime existentes de estas rutas y Logs.
No se rediseñó ninguna función estable ni se cambió bot.py en este PR.
No se observó un nuevo defecto runtime que justifique correcciones adicionales.
El catálogo y editor de acciones pendientes de PLAN_MENSAJES no se amplían en #15.

### WAL y reversión

- El respaldo H-03 usa Connection.backup, incluye WAL confirmado y valida integridad,
  FK, hash/esquema; una copia del .db activo no es respaldo consistente.
- sqlite_preflight abre mode=ro, query_only y transacción de lectura. No escribe
  tablas ni hace checkpoint. SQLite puede acceder/crear metadatos SHM si el sistema
  de archivos permite escritura: para **cero modificación de archivos** ejecutar
  sobre el conjunto DB/WAL/SHM mediante una vista/mount de solo lectura ya disponible,
  sin crear mounts ni tocar producción en esta tarea. No usar immutable=1 en una
  base viva: puede ignorar WAL y acreditar falsamente una copia obsoleta.
- Snapshot de esquema anterior != ampliado: restore_backup requiere igualdad de
  esquema y rechaza reemplazar una base ampliada directamente con una antigua.
  Para reversión de datos, conservar el conjunto ampliado privado, usar destino
  nuevo aislado con schema-from del código anterior y detener todos los escritores.
  No borrar WAL/SHM ni forzar el reemplazo para vencer la comprobación.
- Volver solo a main conserva las tablas nuevas, pero main no procesa Join Roles
  pendientes ni programaciones/ledger nuevos. Debe decidirse cómo reconciliarlos.
- Volver a datos anteriores pierde cambios posteriores al respaldo y puede repetir
  operaciones Discord. No reconectar antes de reconciliar condenas, roles, tareas,
  envíos inciertos y recibos. SQLite no incluye los JSON/adjuntos remotos de Discord.

## Comandos reproducibles (solo datos aislados)

```bash
mkdir -p work
git show 6f9f9ee0a7ed1c7b7e6c48a13817b9b5f3a5b667:bot.py > work/main-bot.py
python tools/check_sqlite_upgrade.py --main-source work/main-bot.py
python -m unittest test_regressions.py test_member_logs.py
python -m unittest discover -s tests -p 'test_*.py'
python -m pip check
python -m py_compile bot.py sqlite_recovery.py sqlite_preflight.py tools/check_sqlite_upgrade.py evidence_archive.py message_payload.py message_automation.py message_components.py message_editor.py
git diff --check
```

Ejecutados con `/workspace/.venvs/el-heraldo-bot/bin/python`, Python 3.12,
discord.py 2.7.1. Base 203 y lote nuevo 207 correctas; compilación/dependencias/diff
correctos. CI añade ensayo contra el SHA main revisado en 3.11/3.12/3.13.
Actualizar esa referencia solo tras revisar un cambio futuro de main.
Una repetición de la suite en el sandbox de red restringida quedó detenida tras
49 casos; se terminó ese proceso propio. La repetición acotada con permisos de red
del entorno pasó los 168 tests en 1,747 s. Las pruebas siguen sin llamadas reales
a Discord; no se interpreta el bloqueo del sandbox como fallo funcional.

## Guion mínimo del laboratorio — NO REALIZADO

Registrar SHA desplegado, fecha, actor autorizado y evidencia saneada; cuentas
voluntarias, roles/canales de Test únicamente. Detener al primer fallo.

1. Setup: abrir secciones, volver/cancelar sin guardar, guardar explícitamente;
   retirar permiso antes de confirmar y comprobar rechazo; modal caducado.
2. Condena/perdón: participante de Test, snapshot de roles antes de sancionar;
   perdonar con rol no asignable, conservar pendiente, reparar jerarquía y confirmar
   restauración. Cancelar no cambia estado. Comprobar tarjeta, DM y Logs.
3. Verificación: ambos temporizadores vencen, una sanción/un registro; repetir solo
   registrar y plazo ampliado. Conservar notificación independiente de preferencias
   (decisión del PR #3 cerrado sin fusionar).
4. Evidencias: texto/adjunto sintético archivado y hash válido antes de purga;
   privacidad revocada/copia perdida/archivo no soportado bloquean borrado;
   Solo reportar no sanciona ni purga. No probar evidencias reales.
5. Mensajes: selector embed/campo, borrador/guardar/cancelar, publicar roles
   ordinarios, rechazar rol privilegiado, programación y reinicio con incertidumbre.
6. Logs/Reaction Roles: alta/baja de rol y coherencia de un aviso por evento.
7. H-03: respaldo de Test a destino privado autorizado, descarga y restauración en
   destino aislado con bot detenido; comprobar aislamiento, pendientes y archivos
   remotos. Nunca declarar recuperación integral solo por integrity_check.

## Preflight real preparado — NO EJECUTADO

Operador autorizado confirma ruta DB_PATH sin publicar valores sensibles. Ejecutar
el checkout revisado con Python compatible en vista de solo lectura autorizada:

```bash
python -m sqlite_preflight --db RUTA_DB_CONFIRMADA
```

Salida solo estado, huella del esquema, versiones, modo journal y presencia WAL/SHM;
sin filas, recuentos, SQL, rutas ni excepciones privadas. Exit 1 bloquea.
Para comprobar una generación privada **existente**:

```bash
python -m sqlite_recovery verify RUTA_PAQUETE_PRIVADO --environment ETIQUETA_CONFIRMADA
```

No publicar manifiesto ni paquete. Acceso de lectura al volumen/backup o constancia
del operador aún necesarios: las herramientas disponibles son de control de Railway,
no ofrecen shell/archivos/validación de backups de volumen. No iniciar login,
crear credenciales ni infraestructura para suplirlo sin alcance autorizado.

## Secuencia de lanzamiento propuesta — requiere aprobación futura

1. Integrar PR revisado a Pruebas solo tras CI, revisión del diff y comprobación de
   base/conflictos; esta acción podría desplegar Test automáticamente. No hacerlo
   como efecto secundario de este informe. Revalidar CI y Test del SHA integrado.
2. Completar guion anterior; documentar resultado por cambio, sin repetir desarrollo
   de funciones estables. Cerrar hallazgos demostrados antes de solicitar producción.
3. Confirmar respaldo real privado/recuperable externo al volumen, integridad y
   ensayo de descarga/restauración, espacio libre, conservación de evidencias y
   referencias. Si falta destino, propietario decide destino/coste/credenciales;
   no crear buckets ni respaldos recurrentes por esta tarea.
4. Comparar SHAs nuevamente y ejecutar preflight de lectura. Acordar ventana con
   propietario y participantes: inicio, duración máxima, responsable y criterio de
   abortar. No fijar una ventana ejecutable mientras faltan respaldo/laboratorio.
5. Obtener aprobación específica de main, parada temporal y cualquier modificación
   de datos reales. main actual no respeta service_lock: no confiar en ese archivo
   para excluir el proceso viejo. Detener todas las réplicas y escritores durante
   un futuro cambio autorizado; conservar snapshot final consistente y privado.
6. Con versión, esquema y snapshot registrados, realizar actualización aprobada y
   comprobar despliegue SUCCESS del SHA exacto. Si falla, no declarar éxito ni
   sustituir datos automáticamente. DB_PATH debe seguir en almacenamiento persistente.
7. Monitorizar arranque/Gateway, errores SQLite, permisos, roles pendientes,
   temporizadores, archivo privado y Mensajes. Registrar chequeos al arranque,
   tras la primera interacción y al finalizar la ventana. Fallos de datos,
   conservación de evidencia, sanciones duplicadas o pérdida de roles => abortar.
8. Reversión: detener escritores, guardar estado posterior privado y diagnosticar;
   escoger retorno solo de código o snapshot con reconciliación explícita. Usar
   destino nuevo para esquema anterior y procedimiento H-03; no eliminar sidecars.
   Restaurar requiere aprobación de datos. Comprobar que no se repetirán acciones
   antes del Gateway. Un rollback de imagen Railway no revierte el volumen.

## Transferencia y decisiones mínimas pendientes

Codex preserva herramientas, CI y documentos en el PR de #15. ChatGPT coordina
revisión y resultados del laboratorio. Falta acceso de lectura al conjunto SQLite
y una generación privada recuperable, aceptación humana en Test, y decisión de
destino externo si no existe uno. Estas ausencias impiden aprobar producción;
**no constituyen autorización para parar, restaurar o actualizar main**.
El issue permanece abierto hasta cerrar los bloqueadores reales.
