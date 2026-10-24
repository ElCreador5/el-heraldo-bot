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
