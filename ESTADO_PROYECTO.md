## 2026-11-02 — Comandos consolidados y constructor de embeds manual

Autorización expresa del propietario: retirar las programaciones del constructor de embeds y trasladar esa corrección junto con la reorganización de comandos a `main`. Implementación selectiva sobre `main@32c9f5d`; no se incorpora toda Pruebas. Los grupos Honeypot, Raid, Embed, Roles de ingreso y Sugerencias son accesos únicos a paneles. Se retiran nueve configuraciones slash redundantes; las acciones y consultas útiles se conservan. `/mensajes` reutiliza Setup, `/list comandos` navega por tipo y módulo, y los accesos se adaptan exclusivamente a funciones existentes de producción. Registro final: 37 comandos raíz / 40 invocables; no se introducen Custodio, la internacionalización de laboratorio, el servidor Activity ni el editor de AutoFeeds.

Constructor `/embed`: creación confirmada, selección persistente, edición, eliminación confirmada y envío manual con vista previa/confirmación de canal. Sin controles ni trabajador de programaciones de embeds. La programación existente de Miembro de la Semana conserva sus claves y comportamiento. No se migran esquemas ni se borran registros o configuraciones. Los helpers de panel mantienen español y el footer productivo `{servidor}` + `{servericon}`. El defecto `view=None` se corrige al enviar respuestas/follow-ups; al editar, None conserva su función de retirar controles.

Validación aislada: **151 pruebas raíz y 9 de subdirectorio, todas correctas**, compilación y diff correctos, sin token/Gateway ni datos reales. Incluye registro real de discord.py, permisos revocados, cierre, navegación, configuración de respaldo con confirmación/concurrencia y ausencia de programación en el constructor. El editor de roles por reacción de cinco filas conserva Opciones/Editar mensaje bajo Más acciones para incorporar Cerrar sin exceder Discord.

**Railway:** el propietario informa despliegues pausados durante 14 días. Se conserva esa pausa; no se ejecuta redeploy, restart ni cambios del servicio. Antes de publicar se observó el último despliegue productivo como REMOVED desde el 29/10 y el volumen `/data` conservado. Publicar el código y pasar CI no acredita un nuevo arranque productivo. Gateway, sincronización y clics reales quedan pendientes del fin de la pausa. El propietario sí aportó evidencia de arranque y COMMAND_SYNC=42 del laboratorio; también aportó el error del botón Programaciones que motiva su retirada.

## Identidad obligatoria del footer en toda salida — 2026-10-24

**Preparado para publicación en `main`**: `stamp_embed` aplica el nombre/icono reales del servidor también sobre pies personalizados, conserva el texto configurable y utiliza copias para evitar que una plantilla reutilizada contamine otros servidores. Se incorporan pistas en los editores y regresiones globales. No hay migración ni modificación de SQLite. Las pruebas automatizadas y el despliegue deben comprobarse en el commit publicado; la comprobación visual en Discord Lab continúa pendiente.

## Actualizaciones directas y log único de expulsión — 2026-10-20

**IMPLEMENTADO EN CANDIDATO PARA `main`**: se suprimen los dos registros de éxito por KICK de verificación para dejar la tarjeta genérica «Miembro expulsado», conservando avisos de error, «Solo registrar», y BAN sin cambio. Sin modificación de esquema, SQLite, datos ni configuración. Regresiones de contrato en `test_member_departure_cards.py`; `python-checks` se ejecuta automáticamente en push a `main`, ahora sin ser check obligatorio. **Al crear esta anotación las verificaciones y Railway todavía están pendientes; consultar el SHA y CI real tras el push.** Prueba interactiva Discord NO realizada. **Proceso administrativo simplificado:** sin PR obligatoria ni checks requeridos; continuar con pruebas, trazabilidad y respaldos proporcionados al riesgo de cada cambio.

## Honeypot — Guardar dentro de Acción y Medida (2026-10-19)

**IMPLEMENTADO, pendiente de publicar:** PR #22 con botones **Guardar cambios** (verde), **Descartar cambios** (rojo) en ambos submenús, y Volver (gris) por separado. Los botones se inhabilitan si no hay borrador. El guardado llama a la misma validación, permisos y transacción atómica `hp_save_settings` que el panel principal; descartar nunca guarda. Se corrigió además un fallo de la paridad visual anterior: `hp_ban_duration_minutes` no existía en producción, lo que hacía fallar Configurar medida al seleccionar Banear. Cuando no hay duración configurada, el panel muestra «Sin configurar» y exige escoger explícitamente una duración, incluida «Permanente» (0), sin guardarla automáticamente. Pruebas nuevas de callbacks y duración permanente en `test_honeypot_runtime.py`. **CI final:** verificar para el nuevo commit de PR #22; el primer CI de la PR detectó legítimamente ese NameError y no debe contarse como aprobado. **Pruebas Discord:** pendientes. No se fusionaron módulos ajenos ni se modificaron sanciones. Railway productivo no se despliega por este commit; solo tras CI y aprobación ya concedida.

## Corrección de paridad visual Honeypot — PR #21 (2026-10-19)

**IMPLEMENTADO EN CANDIDATO:** se detectó visualmente que el panel productivo de PR #19 mostraba texto largo y selectores generales mientras Test tenía embed compacto y navegación por botones. PR #21 sobre la rama selectiva ya existente traslada la interfaz de `Pruebas` sin fusionar todo Test: panel `AutoMod — Honeypot`, subpantallas Acción/Configurar medida/Aviso/Detalles, estados contextuales de Activar/Pausar, botones Retirar canal y confirmación, Guardar y Descartar. Conserva en producción el guardado transaccional `hp_save_settings`, permisos revalidados, confirmaciones de aviso y creación de canal; mantiene sin cambios la lógica de sanciones y la base SQLite. `python-checks` en `0eb58725`: SUCCESS, 108 pruebas funcionales/estáticas del candidato. Discord visual real y despliegue productivo del nuevo panel: **pendientes**. `main` aún ejecuta el panel anterior hasta fusión/despliegue autorizado.

# Candidato selectivo Honeypot — PR #19

Estado comprobado el 18/10/2026. Rama `release/honeypot-selective-20261018`,
base de este trabajo `9fc47d5bc1e77f6d44c0c72781a42044e783e72e`.
`main` permanece en `c6a5c1642d84b776e522473d62cf92c60e018cb3`.
No se ha fusionado ni desplegado el candidato en producción.

Se corrigieron privacidad de la caché en trampas, permisos al confirmar,
guardados atómicos, cancelación y actualización del panel, publicaciones
ambiguas, creación concurrente de canales, purgas de hilos privados/archivados
y conservación del vencimiento de baneos ante fallos. Las rutas ajenas a
Honeypot conservan sus evidencias y sus políticas de purga.

34 pruebas funcionales nuevas; 91 regresiones completas aprobadas en Railway
Test con SQLite temporal. Avisos y purgas también comprobados con la API real
de El Heraldo Test en Heraldo's Lab. Alcance y límites en [PRUEBAS_DISCORD.md](PRUEBAS_DISCORD.md).

Copia SQLite productiva nueva del 18/10 a las 14:55:44 UTC: descarga cifrada,
autenticación y recuperación aislada verificadas. No acredita recuperación
independiente desde Bitwarden; esa condición sigue pendiente.

Integración bloqueada por aprobación independiente ausente, custodia
independiente aún sin verificar y controlador H-03 no eludible pendiente.
También falta aceptación humana de botones/modales del candidato y ensayo
Kick/Ban con cuentas de laboratorio designadas. No se han usado personas reales
como objetivos de prueba. CI de `be742f3` aprobada; el check del último commit
se registra en PR #19. Recuperación del mismo aviso con imagen comprobada
también contra Discord real con el código final.

Los documentos generales fueron consultados desde `Pruebas@b90e3a6`; no se
copió su código ni su documentación histórica completa a esta rama selectiva.


## 2026-11-04 — Estado de promoción de idiomas a main

Cambios selectivos incorporados: `production_report_labels.py`, conexión en `bot.py` para presentar etiquetas oficiales de reportes mediante `guild_language(guild_id)` leyendo el valor manual ya guardado (fallback es-419), prueba `test_production_report_labels.py` y comprobación CI en `member-logs-checks.yml`. Sin migraciones SQLite, sin cambios a Railway, sin fusión de ramas.

Diferencia estructural verificada: `main` conserva un selector de idioma pendiente y NO dispone del recordatorio `reminder_preview`, `refresh_report_reminder_publications` ni del mecanismo histórico de `Pruebas`. Por tanto los recordatorios anteriores y los demás mensajes de sistema en `main` aún NO se traducen automáticamente; la presentación de reportes sigue dependiendo de que haya idioma guardado. No afirmar finalización del objetivo original ni pruebas Discord reales.
