# Continuidad — Auditoría de seguridad sobre PR #7

**Registro:** 2026-10-11 UTC. Este documento pertenece a la rama `fix/auditoria-seguridad-pr7-20261010` basada en `codex/seguridad-mensajes-20261010@661da952a0`; no equivale a integración en `Pruebas`.

## Objetivo
Cerrar los hallazgos A (confirmaciones heredadas), B (roles parcialmente restaurados) y C (visibilidad de evidencias) antes de aprobar el avance hacia producción.

## Cambios confirmados
- `bot.py`: registrar los IDs de roles que no se pudieron restaurar en el log de perdón. No incluir los IDs extra en el DM ni tarjeta pública.
- `bot.py`: rechazar el archivado de evidencia en canales legibles para roles no administrativos y miembros con permisos individuales explícitos.
- `tests/test_evidence_access_regressions.py`: tres pruebas estáticas para detectar la eliminación accidental de las protecciones anteriores.

## Limitaciones y riesgos
- **A pendiente:** rutas administrativas heredadas todavía realizan escrituras directas sin confirmación. Ejemplos confirmados por lectura: `honeypot_config`, `honeypot_resume` y `heraldo_log_channel`; revisar todas las restantes.
- **B parcial:** los IDs aparecen en el registro, pero no existe flujo operativo completo de reintento/reconciliación.
- **C conservador:** el chequeo puede impedir archivar si un rol ordinario tiene acceso a logs, incluso si se trata de personal de moderación. Habilitar canal de evidencias separado sería preferible; faltan pruebas interactivas y de permisos.
- Las comprobaciones añadidas son estáticas; no se ha confirmado ejecución de CI después de estos commits ni realizado prueba real en Discord.
- No se ha integrado el PR #7 ni la rama de corrección a `Pruebas`, y `main` está sin modificaciones.

## Siguiente paso
1. Ejecutar CI (compilación y regresiones) sobre esta rama; corregir fallos.
2. Implementar guardado confirmado y permisos revalidados en los comandos heredados por etapas con pruebas.
3. Diseñar control de acceso y retención para evidencia independiente de logs generales.
4. Integrar los PR en orden revisado, desplegar solo El Heraldo Test en Heraldo's Lab y registrar pruebas manuales en `PRUEBAS_DISCORD.md`.
5. Exigir revisión, respaldo SQLite y autorización concreta antes de `main`.

## Avance adicional — 2026-10-11 UTC
- Commits en la rama de auditoría: confirmación en `/honeypot setup`, `/honeypot resume`, `/heraldo_log_channel`, `/verify_setup`, Join Roles add/remove/user_add/user_remove y `/motw_set_schedule` / `/motw_set_channel`. Se reutilizó `ConfigurationConfirmView` con comprobaciones de permisos al guardar y control de propuestas obsoletas.
- Regresiones agregadas en `tests/test_safety_regressions.py`; GitHub Actions **SUCCESS** en el commit `55f62790eb` (matriz offline). Hubo fallos intermedios de dobles de prueba corregidos posteriormente; no se deben confundir con el resultado final.
- Última rama revisada: `fix/auditoria-seguridad-pr7-20261010@55f62790eb`, PR #10 sigue en borrador contra `Pruebas`.
- Railway laboratorio: último despliegue observable **SUCCESS** en `Pruebas@34fa94f`; estos cambios **NO** están desplegados en Discord.
- **Pendientes:** otros comandos administrativos heredados aún pueden guardar sin confirmación (raid, sugerencias, honeypot add/create/remove/exenciones, etc.); tratar por módulos con pruebas. Restauración parcial requiere flujo operativo y política de acceso a evidencias exige comprobación del modelo de moderadores. Verificaciones interactivas de Discord NO REALIZADAS.
- No se modificó ni fusionó `main` ni `Pruebas`. Para integrar, revisar orden entre PR #7 y PR #10, CI sobre la rama fusionada y autorizar despliegue al laboratorio primero.
