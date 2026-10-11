# Continuidad entre agentes — El Heraldo

[[INICIO_OBSIDIAN]] · [[AGENTS]] · [[ESTADO_PROYECTO]] · [[DECISIONES]] · [[PRUEBAS_DISCORD]]

## Procedimiento de inicio
1. Leer [[AGENTS]], [[ESTADO_PROYECTO]], [[DECISIONES]], [[PRUEBAS_DISCORD]] y, si procede, [[PLAN_MENSAJES]].
2. Consultar ramas, PR y commits recientes en GitHub; no tomar por actual una nota anterior.
3. Consultar Graphify para orientar la exploración; confirmar el commit indexado (última referencia observada: `main@6f9f9ee`) antes de atribuir resultados a `Pruebas`.
4. Trabajar únicamente en rama de desarrollo autorizada. Mantener `main` sin cambios salvo autorización específica.
5. Al finalizar, actualizar los documentos pertinentes, registrar pruebas realizadas y guardar commits/PR; no afirmar que hubo guardado si faltan permisos.

## Protocolo compartido actual
- **Rama única de desarrollo habitual:** `Pruebas`. Producción: `main`, protegida por autorización explícita.
- Las ramas de tarea y PR abiertos son temporales, usados para revisión, pruebas y prevención de conflictos. Integrar a `Pruebas` únicamente cambios comprobados; conservar o cerrar PR obsoletos con explicación.
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
