## Actualizaciones directas y log único de expulsión — 2026-10-20

**IMPLEMENTADO EN CANDIDATO PARA `main`**: se suprimen los dos registros de éxito por KICK de verificación para dejar la tarjeta genérica «Miembro expulsado», conservando avisos de error, «Solo registrar», y BAN sin cambio. Sin modificación de esquema, SQLite, datos ni configuración. Regresiones de contrato en `test_member_departure_cards.py`; `python-checks` se ejecuta automáticamente en push a `main`, ahora sin ser check obligatorio. **Al crear esta anotación las verificaciones y Railway todavía están pendientes; consultar el SHA y CI real tras el push.** Prueba interactiva Discord NO realizada. **Proceso administrativo simplificado:** sin PR obligatoria ni checks requeridos; continuar con pruebas, trazabilidad y respaldos proporcionados al riesgo de cada cambio.

## Honeypot — Guardar dentro de Acción y Medida (2026-10-19)

**IMPLEMENTADO, pendiente de publicar:** PR #22 con botones **Guardar cambios** (verde), **Descartar cambios** (rojo) en ambos submenús, y Volver (gris) por separado. Los botones se inhabilitan si no hay borrador. El guardado llama a la misma validación, permisos y transacción atómica `hp_save_settings` que el panel principal; descartar nunca guarda. Se corrigió además un fallo de la paridad visual anterior: `hp_ban_duration_minutes` no existía en producción, lo que hacía fallar Configurar medida al seleccionar Banear. Cuando no hay duración configurada, el panel muestra «Sin configurar» y exige escoger explícitamente una duración, incluida «Permanente» (0), sin guardarla automáticamente. Pruebas nuevas de callbacks y duración permanente en `test_honeypot_runtime.py`. **CI final:** verificar para el nuevo commit de PR #22; el primer CI de la PR detectó legítimamente ese NameError y no debe contarse como aprobado. **Pruebas Discord:** pendientes. No se fusionaron módulos ajenos ni se modificaron sanciones. Railway productivo no se despliega por este commit; solo tras CI y aprobación ya concedida.

## Transferencia — Corrección Honeypot Test → main (2026-10-19)

Rama de publicación **ya existente y autorizada** `release/honeypot-selective-20261018@0eb58725901c2397d3dbcde117829eb9cc92ff5a`; PR nueva #21 (UI, no Honeypot completo) abierta como borrador sobre `main@91e193d5`. Objetivo: equiparar panel productivo con Test preservando transacción/confirmaciones existentes. Cambios: `bot.py`, `test_honeypot_runtime.py`, `test_honeypot_selective_main.py`; CI python-checks SUCCESS 108 tests. Discord UI real no probado. Siguiente: validar que PR no cambia nada ajeno a UI, comprobar CI de último commit documental y base actual; fusionar PR #21 solo con checks correctos y autorización del propietario (otorgada en chat); desplegar SHA exacto manualmente en Railway producción sin alterar volumen `/data`; comprobar logs, Gateway y salud; pedir inspección visual de /setup por el propietario. El H-03 universal sigue pendiente; respaldo cifrado anterior del 18/10 recuperado por separado, no afirmar copia pre-release nueva.

# Continuidad — PR #19

Rama autorizada: `release/honeypot-selective-20261018`. Base de trabajo:
`9fc47d5bc1e77f6d44c0c72781a42044e783e72e`. Recuperar HEAD remoto antes de continuar;
los SHA históricos no autorizan sobrescritura. No crear otra rama/PR.

Cambios: `bot.py`, pruebas funcionales y CI; documentación de esta rama
selectiva. Resultados y límites completos en [PRUEBAS_DISCORD.md](PRUEBAS_DISCORD.md).
91 pruebas, dependencias y compilación aprobadas en Railway Test. API real de
avisos/purga comprobada. Copia productiva nueva recuperada el 18/10/2026.

Commits de continuación: `be742f3` (controles, privacidad, purgas y sanciones;
CI aprobada), seguido por la corrección de huella de imágenes de Discord.
Consultar el comentario de entrega en PR #19 para HEAD y CI definitivos.

No fusionar todavía: falta revisor independiente, recuperación de clave desde
Bitwarden y controlador H-03 no eludible. Falta aceptación humana del candidato
en Discord. No iniciar otro bot con token productivo ni sustituir el worker
Test sin revisar sus funciones de Pruebas y preservar su SQLite.

La bóveda está bloqueada en el navegador disponible; no hay CLI `bw` disponible.
La herramienta de navegador devolvió fallo de revisión automática por límite
de uso. No hubo rechazo por inseguridad y no se intentó eludirlo.

Siguiente intervención del propietario: desbloquear su sesión de Bitwarden
para verificar la recuperación del elemento existente «El Heraldo - H-03
produccion - clave de recuperacion», sin volver a importarlo ni enviar la clave
al chat. Después continúan revisión independiente y cierre de las otras puertas.

Herramientas operativas y recibos privados se conservan fuera del repositorio.
No repetir la generación del 18/10 ni subir otro objeto para ocultar un fallo.
No quedan cambios autorizados en `main`; no se ha desplegado el candidato.
