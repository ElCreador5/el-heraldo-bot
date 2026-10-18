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
