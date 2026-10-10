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
