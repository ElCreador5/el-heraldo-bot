# Auditoría de integración — El Heraldo — 2026-10-14

**Origen:** informe entregado por Claude al propietario el 2026-10-14. **Custodia posterior:** ChatGPT lo contrastó parcialmente contra GitHub y Railway y lo guardó en `Pruebas`. Las pruebas locales de Claude **NO fueron repetidas por ChatGPT**. No confundir inspección documental con ensayo real Discord.

## Alcance y estado comprobado

- Repositorio: `ElCreador5/el-heraldo-bot`.
- `main@6f9f9ee0a7ed1c7b7e6c48a13817b9b5f3a5b667`, sin cambios.
- `Pruebas@1eebcce77b346c8c40762b2c8bece4dfb220fb3e` al recibir el informe, **192 commits por delante, 0 por detrás, 59 archivos** (comprobado independientemente por ChatGPT antes de guardar este documento).
- Railway producción: `Online/SUCCESS`, réplica 1/1; Railway Test: worker `Online/SUCCESS`, cron Lab `cronReady/SUCCESS`. No se desplegó, restauró ni modificó producción en esta auditoría.
- PR #16 abierto en borrador, relacionado con preflight SQLite, **no fusionado**.
- Obsidian no disponible mediante los conectores de esta sesión; GitHub constituye la fuente primaria.

## Verificaciones que reportó Claude (no repetidas aquí)

**Entorno:** Python 3.12.3, discord.py 2.7.1, SQLite sintética, sin interacción con Discord.

1. `Pruebas`: compilación y `pip check` correctos; 35 tests de `test_regressions.py`, cuatro de `test_member_logs.py` y 218 de `tests/`: **257/257**.
2. Candidato mínimo generado por `tools/prepare_h03_candidate.py` desde `main`: cuatro módulos H-03, dependencia `cryptography`, hook opt-in de 7 líneas en `bot.py`; resto del AST del bot sin modificación. Compilación y dependencias correctas; 29 regresiones de `main` aprobadas; 51 de 52 pruebas H-03 aplicables pasaron, y la restante importa el `bot.py` de `Pruebas`, por lo que **no se considera fallo del candidato mínimo**.
3. Análisis estático pyflakes: cero nombres indefinidos y aviso menor sobre `import io` duplicado en `bot.py`.
4. Comparación de SQLite: `Pruebas` solo añade seis tablas (`pending_join_roles`, `evidence_archive_v1`, `message_schedule_state` con `dirty`, `message_autoresponse_rate`, `message_action_rate`, `message_action_audit`), todas mediante `CREATE TABLE IF NOT EXISTS`. No halló desaparición de tablas o columnas de `main`.
5. Inventario slash: los comandos de `main` se conservan; nuevos `/edittemplate`, `/importkit`, `/restaurar_roles_pendientes`, `/sendtemplate` y grupos de automatización. La auxiliar `delete_one` se reemplaza en el código de barrera de evidencias.
6. Archivo de evidencias: inspeccionado, falla cerrado cuando falta canal privado, copia íntegra o ledger resuelto.
7. H-03 sin bandera: hook dormante, sin importar respaldos.
8. **Defectos nuevos corregidos por Claude: ninguno.** **Críticos demostrados en esta revisión: ninguno.** La auditoría no cubrió exhaustivamente las 3.444 líneas de cambios de `bot.py` ni realizó pruebas humanas de las nuevas interacciones Discord.

Resultados Railway, CI, backups reales y recuperación mencionados en el informe de Claude proceden de trabajos previos de otros agentes, no fueron reejecutados por Claude.

## Corrección al informe: candidato GitHub no referenciado

Claude no encontró `203ea14a34ab35f8e6feb78f244558906fca1a85` mediante `git cat-file` en el clon y lo trató como no accesible. **ChatGPT confirmó por GitHub API que el objeto commit existe**, aunque **no está asociado a una rama**. Es distinto del candidato mínimo probado por Claude: además de los cuatro módulos, dependencia y hook opt-in, incluye un backport para que `Solo reportar` jamás ejecute purga con reglas heredadas y un nuevo test de regresión y ampliación del workflow `python-checks`. Esas modificaciones extra **no fueron ensayadas por Claude**. La comprobación CI obligatoria de la versión exacta sigue pendiente.

La API de GitHub rechazó una actualización directa de `main` porque la rama protegida exige PR y `python-checks`. **No se intentó omitir la protección** y `main` sigue sin modificación.

## Juicio técnico de integración

**A — H-03 dormante (sin los cambios extra del commit no referenciado): APTO TÉCNICAMENTE según Claude** para preparar PR, condicionado a `python-checks`, autorización del procedimiento, copia SQLite consistente reciente y restauración aislada inmediatamente antes de desplegar, y plan de reversión. La bandera H-03 debe quedar **SIN configurar**.

**A+ — commit candidato `203ea14a...`: PENDIENTE** de ejecutar CI en su propio diff exacto y revisar la corrección adicional de `Solo reportar`. No equiparar automáticamente su validación con la de A.

**B — respaldos diarios de producción: BLOQUEADO.** Faltan variables técnicas de Supabase/clave/flag en Railway producción y recuperación de clave independiente y entrega de alertas verificadas. No se deben activar por efecto de A.

**C — fusión de los 192 commits de `Pruebas`: NO APROBADA.** No hay defecto crítico nuevo demostrado por Claude, pero no se han aceptado interactivamente en Heraldo's Lab los flujos con sanciones, roles, borrado, verificación, logs y mensajes. Conservar el comportamiento productivo preexistente. Los fallos/ausencias de cobertura deben separarse de recomendaciones opcionales; una actualización de lotes exige aceptación de las rutas correspondientes.

## Plan ejecutable y reversión

1. Obtener aprobación específica para **una sola rama temporal de lanzamiento hacia `main` y PR**: las reglas del proyecto impiden crearla sin permiso expreso. **No usar el botón GitHub Compare & pull request sobre `Pruebas`** porque llevaría 192 commits.
2. Publicar exclusivamente el candidato mínimo elegido, comprobar `python-checks`, revisiones y diferencias exactas. No incluir otros cambios de `Pruebas`.
3. Justo antes del despliegue, verificar una copia SQLite productiva reciente consistente y su restauración aislada; conservar generaciones existentes y preparar rollback de código sin alterar datos.
4. Fusionar la PR solo tras los gates y autorización productiva correspondiente. Comprobar Railway `Online/SUCCESS`, conexión real Gateway, `/setup` no destructivo y que H-03 no se active sin bandera.
5. Revertir solo **código** si hay fallo: versión anterior/commit revert; no restaurar DB a ciegas ni rebobinar roles/sanciones.
6. Separar la futura habilitación del cron productivo de esta promoción de software. La verificación independiente de Bitwarden fue aplazada por el propietario para noviembre; no convertir esto por sí solo en bloqueo de **código dormante**.

## Continuidad

Este documento se guardó por ChatGPT porque Claude informó HTTP 403 al escribirlo. Los resultados de pruebas de Claude siguen siendo informes externos; no se atribuyen a ejecuciones propias. No se han copiado secretos, manifiestos, identidades privadas ni contenido SQLite al repositorio.
