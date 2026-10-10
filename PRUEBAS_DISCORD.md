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
