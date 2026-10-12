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
