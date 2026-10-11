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
