# Continuidad entre agentes — El Heraldo

## Continuación del PR #16 — 2026-10-12

Codex conserva `codex/issue15-preflight-20261012`, HEAD recibido `c80066d`.
Main `6f9f9ee` y Pruebas `c01aa4d` intactas. Leer primero la nueva sección de
`INFORME_ISSUE15.md`: revisión de los 11 archivos originales, defectos reproducidos
en verificadores y límites de acceso. No repetir H-03/#14 ni desarrollar Mensajes.
215 pruebas offline correctas, ocho nuevas, ensayo real de inicializadores con
datos sintéticos y compilación/dependencias correctos. CI recibida 38331744777
success; CI del commit de continuación debe constar en la descripción del PR.
Railway Test online c01aa4d; producción SUCCESS main exacto. Ninguna mutación
Railway/Discord/main. OAuth valuesRedacted=true, sin shell ni backups API; CLI y
credenciales Railway ausentes. Obsidian no conectado. Respaldo/preflight real e
interacciones humanas siguen pendientes, con pasos mínimos en el informe y
PRUEBAS_DISCORD. Siguiente responsable técnico: revisar CI del HEAD remoto, cerrar
acceso/ejecución privada de operador y laboratorio; solo después pedir aprobación
de producción. No asumir que un snapshot de despliegue protege SQLite.

## Transferencia issue #15 — 2026-10-12

Codex, rama temporal `codex/issue15-preflight-20261012`, base Pruebas
`c01aa4d487b27f42610f0d182243b650cb52eddf`, main `6f9f9ee` intacta.
H-03 ya integrado; no repetir PR #14. Acceso GitHub por conector y Git nativo;
gh API sigue Forbidden. Railway leído por conector, sin mutaciones.
CI/Test de base exacta correctos. Nuevos preflight y ensayo de compatibilidad aislado,
CI y documentación: `INFORME_ISSUE15.md`. 207 pruebas offline; Discord real y
respaldo/preflight real no realizados. No modificar main ni datos reales.
Siguiente: ChatGPT revisa PR y CI del nuevo HEAD; coordinar laboratorio y verificación
privada de generación real. Si falta destino externo, decisión del propietario;
no crear infraestructura automáticamente. Commit/PR consultables en historial remoto.

[[INICIO_OBSIDIAN]] · [[AGENTS]] · [[ESTADO_PROYECTO]] · [[DECISIONES]] · [[PRUEBAS_DISCORD]]

## Procedimiento de inicio
1. Leer [[AGENTS]], [[ESTADO_PROYECTO]], [[DECISIONES]], [[PRUEBAS_DISCORD]] y, si procede, [[PLAN_MENSAJES]].
2. Consultar ramas, PR y commits recientes en GitHub; no tomar por actual una nota anterior.
3. Consultar Graphify para orientar la exploración; confirmar el commit indexado (última referencia observada: `main@6f9f9ee`) antes de atribuir resultados a `Pruebas`.
4. Trabajar únicamente en rama de desarrollo autorizada. Mantener `main` sin cambios salvo autorización específica.
5. Al finalizar, actualizar los documentos pertinentes, registrar pruebas realizadas y guardar commits/PR; no afirmar que hubo guardado si faltan permisos.

## Protocolo compartido actual
- **Rama permanente de desarrollo:** `Pruebas`. Producción: `main`, protegida por autorización explícita. Desde 2026-10-12 Codex tiene permiso específico para ramas temporales de tarea con PR hacia `Pruebas`.
- Solo Codex puede crear ramas temporales de tarea y PR abiertos con destino `Pruebas`; no se autoriza modificar `main`. Revisar cambios y CI antes de integrar, tener presente Railway Test automático, y eliminar la rama temporal cuando se descarte o integre sin trabajo pendiente.
- **ChatGPT** recoge decisiones de producto y coordina; **Codex** se ocupa principalmente del código y auditoría; **Work** y **Claude** solo cuando exista una necesidad específica. El repositorio es el contexto compartido.
- Cada transferencia debe nombrar responsable siguiente, rama/commit, cambios reales, CI, pruebas reales Discord, riesgos y acción concreta.
- La sección siguiente conserva el informe recibido el **2026-10-10 como historial**: no es el estado actual de los PR ni de la rama `Pruebas`.

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

## Punto de control Codex — 2026-10-11, H-01
- Pruebas remota da551f3, copia activa el-heraldo-pruebas. Copia el-heraldo-bot preservada: Pruebas local divergente, fetch genérico apunta a una rama eliminada; no mezclar historiales antiguos.
- H-01 validado con tres pruebas recibidas y dos nuevas pruebas runtime. Base: 158 pruebas, compilación y dependencias correctas. Railway Test 712214ac SUCCESS y CI correcto. Discord no realizado.
- Siguiente: archivo verificable de cada mensaje en purgas/Honeypot/raid; impedir borrado API en ban; después respaldo SQLite y evidencias. No hay acceso directo Obsidian; usar Markdown.

## H-02: barrera de conservación — 2026-10-11
- Purga general, condenas, reportes, Honeypot (incluidos mensajes durante otra sanción) y raid pasan por archivo individual antes del borrado. Baneos usan delete_message_seconds=0; la purga configurada se ejecuta separadamente con archivo.
- evidence_archive.py conserva JSON íntegro y adjuntos en el canal privado de Logs existente; verifica tamaño y SHA-256 leyendo cada copia desde Discord. Ledger SQLite durable y exclusión por mensaje: una interrupción incierta bloquea reenvío/borrado. Condenas conservan el contrato de referencia y texto, sin migrar expedientes previos.
- Si no hay intent de contenido, canal privado, permisos o copia íntegra, no se borra. Archivos superiores al menor límite de Discord/25 MiB, stickers, encuestas y mensajes reenviados quedan conservados en origen. No se crearon almacenamiento ni credenciales.
- Se vuelve a leer el origen para detectar ediciones y comprobar privacidad antes del borrado. Discord no ofrece transacción atómica entre edición, permisos y delete: queda una ventana remota mínima y requiere validación humana. Una copia borrada/corrupta o ledger pendiente exige revisión; no se reintenta un envío incierto automáticamente.
- Pruebas base tras integración: 129 tests y 39 raíz/Logs correctos; añadidas luego tres comprobaciones de roles, excepciones individuales y formatos no soportados. El primer ensayo detectó conexiones SQLite sin cerrar; corregidas con cierre explícito.
- Discord real: no realizado. Pendiente validar CI/Railway del nuevo SHA y copia/recuperación en laboratorio. H-03 y etapas posteriores continúan pendientes.

## Actualización de flujo Codex — 2026-10-12
- Autorización expresa del propietario: excepcionar la política anterior de dos ramas únicamente para ramas temporales de tareas Codex y PR a `Pruebas`; queda registrada en `DECISIONES.md` y `AGENTS.md`.
- `.codex/setup.sh` corregido: admite `work` interno, reporta SHA y divergencias respecto a `Pruebas` sin alterar ramas, y prepara dependencias con compilación; no inicia el bot.
- Los commits documentales en `Pruebas` pueden activar Railway Test. Prueba del script dentro de Codex y pruebas reales Discord: pendientes, no declaradas realizadas.
- Próxima tarea Codex: confirmar base del PR, ejecutar preparación y regresiones relevantes; someter PR a `Pruebas`. ChatGPT revisa resultado antes de integrar.

## Punto de continuidad H-03 — 2026-10-12
- Responsable: Codex. Rama `codex/h03-recuperacion-20261012`, base exacta `Pruebas@9502cea3e24099d9867484110adc3fe0872e737d`. El commit que contiene esta sección conserva implementación, regresiones y documentación; consultar `git log` para su SHA, sin atribuirle integración en Pruebas.
- H-03 local implementado y probado: respaldos online, WAL, integridad, manifiesto privado, restauración offline/rollback con bloqueo de servicio y plan de conservación sin borrado. Auditoría y procedimiento en `RESPALDOS_RECUPERACION.md`; 23 pruebas específicas.
- Continuación A–E: protección ante mensaje mutado mientras se archiva, solicitudes/confirmaciones caducadas y selección visual de campos/embeds. No se declaró terminada la auditoría funcional global ni las funciones restantes de `PLAN_MENSAJES.md`.
- Validación F: 203 pruebas offline (39 + 164), compilación y dependencias correctas en Python 3.12.14 / discord.py 2.7.1; sin Discord real, bases reales o despliegues. El primer fixture de permisos de H-03 se corrigió por umask, luego pasó.
- Git nativo funciona; GitHub API devuelve 403 del proxy. No hay conector Railway/Obsidian ni variables Railway/Discord inyectadas. No solicitar nuevos tokens GitHub por este bloqueo. El borrador cloud guardó instalación, instrucciones de inicio offline y `api.github.com`; requiere revisión/guardado y publicación del entorno para activar lo pendiente, no confirma acceso actual.
- Siguiente: habilitar API GitHub, comprobar PR/CI y Railway Test, preparar/revisar PR exclusivamente a Pruebas. Antes de integrar revisar cabeza remota y despliegue automático; no modificar main. Definir destino externo privado y recuperación de archivos de evidencia con el propietario; ensayar laboratorio antes de activar respaldos programados. Continuar editor de acciones, comparación/importación de kits, catálogo y auditoría de interrupciones, conservando prioridades A–F y sin presumir cierre global.

### Guardado remoto comprobado del lote
- Implementación y pruebas preservadas en `99c9853ca97aa48ad5293169ba8874b6d6312204`, publicado y verificado en `origin/codex/h03-recuperacion-20261012`. Árbol limpio tras commit; Pruebas sigue en `9502cea`, main en `6f9f9ee`.
- Se intentó `gh pr create` en borrador, base `Pruebas`, head `codex/h03-recuperacion-20261012`: falló con `Post https://api.github.com/graphql: Forbidden`. **No se creó ningún PR**. La propuesta explica H-03, las correcciones adicionales, 203 tests y las limitaciones; el cuerpo preparado está en `/tmp/heraldo-h03-pr.md` en esta instancia y puede reconstruirse desde este informe si no sobrevive.
- Próximo paso concreto tras habilitar el dominio: consultar primero si existe ya un PR de esta rama para evitar duplicados; crear o actualizar su borrador hacia Pruebas, consultar CI y Railway Test antes de proponer integración. No hay autorización implícita para modificar main o activar infraestructura externa.
