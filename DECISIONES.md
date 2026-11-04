## 2026-11-02 — Comandos consolidados y constructor de embeds manual

Autorización expresa del propietario: retirar las programaciones del constructor de embeds y trasladar esa corrección junto con la reorganización de comandos a `main`. Implementación selectiva sobre `main@32c9f5d`; no se incorpora toda Pruebas. Los grupos Honeypot, Raid, Embed, Roles de ingreso y Sugerencias son accesos únicos a paneles. Se retiran nueve configuraciones slash redundantes; las acciones y consultas útiles se conservan. `/mensajes` reutiliza Setup, `/list comandos` navega por tipo y módulo, y los accesos se adaptan exclusivamente a funciones existentes de producción. Registro final: 37 comandos raíz / 40 invocables; no se introducen Custodio, la internacionalización de laboratorio, el servidor Activity ni el editor de AutoFeeds.

Constructor `/embed`: creación confirmada, selección persistente, edición, eliminación confirmada y envío manual con vista previa/confirmación de canal. Sin controles ni trabajador de programaciones de embeds. La programación existente de Miembro de la Semana conserva sus claves y comportamiento. No se migran esquemas ni se borran registros o configuraciones. Los helpers de panel mantienen español y el footer productivo `{servidor}` + `{servericon}`. El defecto `view=None` se corrige al enviar respuestas/follow-ups; al editar, None conserva su función de retirar controles.

Validación aislada: **151 pruebas raíz y 9 de subdirectorio, todas correctas**, compilación y diff correctos, sin token/Gateway ni datos reales. Incluye registro real de discord.py, permisos revocados, cierre, navegación, configuración de respaldo con confirmación/concurrencia y ausencia de programación en el constructor. El editor de roles por reacción de cinco filas conserva Opciones/Editar mensaje bajo Más acciones para incorporar Cerrar sin exceder Discord.

**Railway:** el propietario informa despliegues pausados durante 14 días. Se conserva esa pausa; no se ejecuta redeploy, restart ni cambios del servicio. Antes de publicar se observó el último despliegue productivo como REMOVED desde el 29/10 y el volumen `/data` conservado. Publicar el código y pasar CI no acredita un nuevo arranque productivo. Gateway, sincronización y clics reales quedan pendientes del fin de la pausa. El propietario sí aportó evidencia de arranque y COMMAND_SYNC=42 del laboratorio; también aportó el error del botón Programaciones que motiva su retirada.

## Interfaz íntegramente en español — 2026-10-24
Se establece como norma obligatoria el español en todas las interfaces, registros y mensajes redactados por el bot en `main` y `Pruebas`. Se traducen etiquetas heredadas del módulo Roles de ingreso y se preservan nombres de comandos establecidos, claves de SQLite, variables e identificadores técnicos. El idioma de botones nativos del cliente Discord depende de la configuración del usuario. Ver NH UX-03D.

## Pie de servidor obligatorio en todos los embeds — 2026-10-24

**Decisión vigente del propietario:** los embeds enviados por El Heraldo en contexto de un servidor deberán mostrar en el footer su nombre (`{servidor}`) y su icono (`{servericon}`, si el servidor tiene icono). La regla rige para módulos, `/setup`, DMs contextualizados, registros, avisos, sanciones y plantillas personalizadas. Los footers de texto previamente guardados se conservan como texto adicional; ninguna personalización puede sustituir el icono del servidor. Cada editor de pie mostrará pistas de ambas variables. No se reescribe SQLite ni se alteran configuraciones guardadas. Cobertura técnica en NH UX-03C.

## Actualizaciones directas y log único de expulsión — 2026-10-20

**Decisión vigente del propietario (20/10/2026):** se simplifica la actualización de producción. GitHub mantiene bloqueado eliminar `main` o reescribir su historial; **ya no exige Pull Requests ni status checks bloqueantes**. Se permite publicar directamente en `main` cuando el propietario autoriza expresamente el cambio concreto, sin solicitar de nuevo la misma aprobación. Las pruebas automáticas permanecen y se ejecutan tras cada push a `main` mediante `.github/workflows/member-logs-checks.yml`; un SUCCESS técnico no equivale a una prueba de Discord. Antes de cualquier actualización, revisar SHA actual, impactos, regresiones y preservar datos: no implica habilitar activaciones H-03 ni migraciones SQLite destructivas sin garantías de recuperación. Esta decisión sustituye las prohibiciones **administrativas** antiguas de PR y checks obligatorios para cambios ordinarios de código; los controles específicos de secretos y respaldo H-03 siguen siendo independientes.

**Corrección puntual de logs en producción:** tras un KICK correcto por falta de verificación, se conserva únicamente la tarjeta configurada **«Miembro expulsado»** de `on_member_remove`. Los dos mensajes genéricos «Expulsión por falta de verificación» dejan de publicarse tras el éxito. No borrar mensajes históricos ni cambiar configuración existente, sanciones, acciones «Solo registrar», errores reales ni avisos de baneo ajenos al alcance. El diagnóstico de la imagen no acredita una prueba posterior al despliegue.

# Decisiones aplicables al candidato de Honeypot

La autorización del propietario está en
[el comentario de PR #19](https://github.com/ElCreador5/el-heraldo-bot/pull/19#issuecomment-6251227100).
Se trabaja exclusivamente en la rama existente de esa PR. No incorporar
`Pruebas` completa, no forzar referencias y no eludir revisión ni respaldos.

Honeypot conserva solamente metadatos administrativos; el contenido de canales
trampa no entra en la caché. Otros orígenes de condena conservan pruebas e
historial. No se borran evidencias históricas ni se migra SQLite destructivamente.

Un resultado ambiguo de Discord debe conciliarse antes de repetir una operación.
Los avisos se recuperan por autor y coincidencia exacta del embed enviado; si no
hay una coincidencia única, no se envía otro. La creación ambigua de canales
queda bloqueada para revisión; no se crean duplicados automáticamente.
El vencimiento del baneo se persiste antes de pedirlo y su expiración verifica
que la sanción vigente corresponde al expediente de Honeypot, sin retirar
un baneo posterior de otro origen.

La copia productiva del 18/10 se restauró usando la custodia local original.
Esto no sustituye la recuperación independiente de la clave ni autoriza una
fusión antes de satisfacer las demás condiciones. El aplazamiento histórico
de esa comprobación hasta noviembre fue revocado en `Pruebas`, pero sus puertas
de seguridad permanecen vigentes.


## 2026-11-04 — Promoción parcial y segura de etiquetas de reportes a main

Se autorizó promover las correcciones recientes de idiomas. La rama `main` usa `production_panel_text` y todavía NO contiene el selector `/language` ni los recordatorios públicos con referencias editables que existen en `Pruebas`. No se autorizó incorporar indiscriminadamente todos los cambios divergentes.

Se incorporó en `main` `production_report_labels.py` y se integró con los resúmenes, selectores y nombres de reportes existentes. Solo se traducen etiquetas institucionales predeterminadas vinculadas al mismo emoji y al idioma del servidor almacenado en `guild_settings`; cualquier etiqueta personalizada permanece literal. En ausencia de un idioma guardado, español es el predeterminado. No se ha incorporado el historial retroactivo ni el selector pendiente: esta promoción NO constituye internacionalización global completa.
