# Continuidad entre agentes — El Heraldo

[[INICIO_OBSIDIAN]] · [[AGENTS]] · [[ESTADO_PROYECTO]] · [[DECISIONES]] · [[PRUEBAS_DISCORD]]

## Procedimiento de inicio
1. Leer [[AGENTS]], [[ESTADO_PROYECTO]], [[DECISIONES]], [[PRUEBAS_DISCORD]] y, si procede, [[PLAN_MENSAJES]].
2. Consultar ramas, PR y commits recientes en GitHub; no tomar por actual una nota anterior.
3. Consultar Graphify para orientar la exploración; confirmar el commit indexado (última referencia observada: `main@6f9f9ee`) antes de atribuir resultados a `Pruebas`.
4. Trabajar únicamente en rama de desarrollo autorizada. Mantener `main` sin cambios salvo autorización específica.
5. Al finalizar, actualizar los documentos pertinentes, registrar pruebas realizadas y guardar commits/PR; no afirmar que hubo guardado si faltan permisos.

## Traspaso Codex → Claude → ChatGPT (informe recibido 2026-10-10)
**Origen:** informe de auditoría aportado por Claude a la conversación; sus resultados de ejecución se atribuyen a Claude, no han sido reproducidos al crear esta nota.

- PR #7: rama `codex/seguridad-mensajes-20261010`, HEAD `661da952a0`, destino `Pruebas@34fa94f0d2`.
- Claude indicó 106 pruebas offline aprobadas con Python 3.12.3 y CI remota satisfactoria en 3.11–3.13. **Pruebas Discord del PR #7: no realizadas**.
- A: comandos administrativos heredados con guardado sin confirmación o comprobación insuficiente de permisos.
- B: condenas finalizadas aunque algunos roles no puedan restaurarse, sin detallar cuáles en la notificación.
- C: canal de evidencias comprueba visibilidad de `@everyone` pero no otras vías de acceso; purgas amplias no archivan todos los mensajes.
- Claude no tenía escritura en GitHub. Su informe `INFORME_CIERRE_PR7.md` se entregó en la conversación y **no estaba persistido en el repositorio** al redactar esta nota.
- Documento del propio PR #7: `REVISION_PR7.md`, disponible **en la rama del PR**, no en `Pruebas` hasta integrarlo.
- Próximos hitos: resolver A/B/C según alcance y riesgo, integrar PR #7 en `Pruebas` tras revisión, pasar CI y pruebas interactivas autorizadas en Heraldo's Lab, y solo entonces preparar aprobación independiente de `main`.

## Plantilla para nuevas transferencias
- Fecha, agente y entorno:
- Rama, commit y PR:
- Objetivo:
- Cambios reales y rutas:
- Verificación automática (comandos y resultados):
- Verificación **real** en Discord:
- Riesgos/bloqueantes:
- Documentos actualizados:
- Trabajo local no guardado:
- Próximo paso concreto:

## Abrir en Obsidian
El repositorio contiene Markdown compatible con Obsidian. En el equipo local, clonar o actualizar la **rama deseada** en una carpeta y usar «Abrir carpeta como bóveda» sobre esa carpeta. No editar documentos de ramas distintas como si fueran una sola versión. No publicar `.obsidian/workspace.json`, configuraciones locales, secretos ni información sensible.

**Sincronización:** Obsidian no sincroniza automáticamente con GitHub, Graphify ni los chats. Guardar cambios mediante Git y PR revisado; resolver conflictos antes de actualizar la rama compartida.
