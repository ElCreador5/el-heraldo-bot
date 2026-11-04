## 2026-11-02 — Comandos consolidados y constructor de embeds manual

Autorización expresa del propietario: retirar las programaciones del constructor de embeds y trasladar esa corrección junto con la reorganización de comandos a `main`. Implementación selectiva sobre `main@32c9f5d`; no se incorpora toda Pruebas. Los grupos Honeypot, Raid, Embed, Roles de ingreso y Sugerencias son accesos únicos a paneles. Se retiran nueve configuraciones slash redundantes; las acciones y consultas útiles se conservan. `/mensajes` reutiliza Setup, `/list comandos` navega por tipo y módulo, y los accesos se adaptan exclusivamente a funciones existentes de producción. Registro final: 37 comandos raíz / 40 invocables; no se introducen Custodio, la internacionalización de laboratorio, el servidor Activity ni el editor de AutoFeeds.

Constructor `/embed`: creación confirmada, selección persistente, edición, eliminación confirmada y envío manual con vista previa/confirmación de canal. Sin controles ni trabajador de programaciones de embeds. La programación existente de Miembro de la Semana conserva sus claves y comportamiento. No se migran esquemas ni se borran registros o configuraciones. Los helpers de panel mantienen español y el footer productivo `{servidor}` + `{servericon}`. El defecto `view=None` se corrige al enviar respuestas/follow-ups; al editar, None conserva su función de retirar controles.

Validación aislada: **151 pruebas raíz y 9 de subdirectorio, todas correctas**, compilación y diff correctos, sin token/Gateway ni datos reales. Incluye registro real de discord.py, permisos revocados, cierre, navegación, configuración de respaldo con confirmación/concurrencia y ausencia de programación en el constructor. El editor de roles por reacción de cinco filas conserva Opciones/Editar mensaje bajo Más acciones para incorporar Cerrar sin exceder Discord.

**Railway:** el propietario informa despliegues pausados durante 14 días. Se conserva esa pausa; no se ejecuta redeploy, restart ni cambios del servicio. Antes de publicar se observó el último despliegue productivo como REMOVED desde el 29/10 y el volumen `/data` conservado. Publicar el código y pasar CI no acredita un nuevo arranque productivo. Gateway, sincronización y clics reales quedan pendientes del fin de la pausa. El propietario sí aportó evidencia de arranque y COMMAND_SYNC=42 del laboratorio; también aportó el error del botón Programaciones que motiva su retirada.

## Actualizaciones directas y log único de expulsión — 2026-10-20

**IMPLEMENTADO EN CANDIDATO PARA `main`**: se suprimen los dos registros de éxito por KICK de verificación para dejar la tarjeta genérica «Miembro expulsado», conservando avisos de error, «Solo registrar», y BAN sin cambio. Sin modificación de esquema, SQLite, datos ni configuración. Regresiones de contrato en `test_member_departure_cards.py`; `python-checks` se ejecuta automáticamente en push a `main`, ahora sin ser check obligatorio. **Al crear esta anotación las verificaciones y Railway todavía están pendientes; consultar el SHA y CI real tras el push.** Prueba interactiva Discord NO realizada. **Proceso administrativo simplificado:** sin PR obligatoria ni checks requeridos; continuar con pruebas, trazabilidad y respaldos proporcionados al riesgo de cada cambio.

## Honeypot — Guardar dentro de Acción y Medida (2026-10-19)

**IMPLEMENTADO, pendiente de publicar:** PR #22 con botones **Guardar cambios** (verde), **Descartar cambios** (rojo) en ambos submenús, y Volver (gris) por separado. Los botones se inhabilitan si no hay borrador. El guardado llama a la misma validación, permisos y transacción atómica `hp_save_settings` que el panel principal; descartar nunca guarda. Se corrigió además un fallo de la paridad visual anterior: `hp_ban_duration_minutes` no existía en producción, lo que hacía fallar Configurar medida al seleccionar Banear. Cuando no hay duración configurada, el panel muestra «Sin configurar» y exige escoger explícitamente una duración, incluida «Permanente» (0), sin guardarla automáticamente. Pruebas nuevas de callbacks y duración permanente en `test_honeypot_runtime.py`. **CI final:** verificar para el nuevo commit de PR #22; el primer CI de la PR detectó legítimamente ese NameError y no debe contarse como aprobado. **Pruebas Discord:** pendientes. No se fusionaron módulos ajenos ni se modificaron sanciones. Railway productivo no se despliega por este commit; solo tras CI y aprobación ya concedida.

## Corrección UI Honeypot — candidata PR #21, 2026-10-19

**VERIFICADO AUTOMÁTICAMENTE:** `python-checks` SUCCESS, 108 pruebas `unittest` para `0eb58725` (GitHub Actions 39207530631). Pruebas del panel actualizadas: borrador por selector contextual, descarte, revalidación de permisos, confirmación de ban, creación de canales, publicación de avisos, selección y cancelación de retirada, renderizado de embed, labels del panel. **Discord real:** todavía NO se ha abierto ni accionado el nuevo panel en producción desde esta sesión; no confundir CI o despliegue SUCCESS con comprobación visual. No se ejecutaron sanciones ni purgas de prueba.

# Verificación del candidato de PR #19 — 18/10/2026

## Automatización ejecutada

`python -m unittest test_member_logs test_regressions test_release_report_only test_honeypot_selective_main test_honeypot_runtime -q`

91 pruebas aprobadas en Python 3.13.16 dentro de una carpeta temporal de Railway
Test, sin credenciales en el proceso de pruebas y con SQLite desechable.
`compileall` y `pip check` aprobados. Los 34 casos nuevos también pasaron en
Windows/Python 3.12. Código final `bot.py` SHA-256:
`e47e6e72396bb1610d9ed4e00cbd4813bfa0a4a090db75c002a088520dc87fcd`.

Los casos ejecutan clases/callbacks reales de discord.py y persistencia SQLite:
propiedad de panel, permisos revocados, borradores, Guardar/Cancelar/Descartar,
modales desactualizados, confirmaciones concurrentes, actualización del panel,
errores parciales, envío ambiguo/reinicio, autor y periodo de purga, hilos
privados, mínimo de 24 horas, jerarquía y exenciones, ban sin purga implícita,
expediente y vencimiento, reintento de desbaneo, baneo ajeno posterior,
antifallos por servidor, Solo registrar y conservación de evidencia ajena.

## Discord real ejecutado

API oficial del bot Test, servidor cuyo nombre exacto es `Heraldo's Lab`.
Carpeta/SQLite temporal del candidato; no se importó sobre la base viva.
Canal privado de ensayo `pr19-validacion-20261018`, retenido para inspección.

- Publicación, fijado y actualización del mismo aviso: comprobados con nueva
  lectura desde Discord; sin duplicación, incluso recreando el estado en memoria.
- Mensaje del autor seleccionado eliminado y mensaje de otro autor conservado:
  comprobados por lecturas API. Ambos fueron fixtures creados expresamente por
  bot/webhook, no contenido previo de personas.
- Hilos públicos y privados archivados encontrados y purgados: comprobados.
  El primer ensayo detectó que Discord impedía borrar mientras estaban archivados.
  Se corrigió y comprobó desarchivar únicamente durante la operación y rearchivar.
- Webhook temporal eliminado después del ensayo; no se conserva su credencial.
- Worker Test mantuvo el mismo proceso y `Pruebas@b90e3a6`; no se cambió su rama.

Las operaciones API se comprobaron con hash de bot
`d93a2f039ca046cc9969fcd6193ed1a845ce1a9e134a3840c47d1f2cc7b94f4a`.
Las modificaciones posteriores afectan confirmación de creación, seguimiento
de baneos y huella de imágenes del aviso. La corrección de imágenes se comprobó
también con el código final y la API real: imagen añadida al aviso de ensayo,
lectura de metadatos devueltos por Discord y recuperación del mismo ID mediante
recibo persistente. El fallo de ID ausente se inyectó exclusivamente en la
SQLite temporal del ensayo. No se provocó una caída del servicio ni se afirma
haber observado un fallo real de red. Al terminar, el aviso original quedó
restaurado, fijado y único; el proceso y la SQLite activos permanecieron intactos.

La huella excluye metadatos de medios añadidos por el servidor, conforme a la
[estructura oficial de embeds](https://docs.discord.com/developers/resources/message#embed-object).
Pruebas negativas verifican que otra imagen y varias coincidencias impiden
conciliar automáticamente y no provocan reenvíos.
NO realizadas: interacción humana con botones/modales; Kick/Ban real de cuentas
de prueba designadas. Los dobles automatizados no se presentan como esos ensayos.

## Copia productiva real

18/10/2026 14:55:44 UTC, origen `main@c6a5c164`, SQLite de 671744 bytes,
WAL activo, instantánea mediante SQLite backup API en el volumen propietario.
Cifrado AES-GCM: 186164 bytes. Subida sin sobrescritura a Supabase privado,
descarga autenticada, SHA-256, integridad, claves foráneas, esquema, recuentos
y contenido de restauración aislada correctos. Clave errónea y ciphertext
alterado rechazados. Cinco archivos previos del volumen conservados y mismo
proceso productivo antes/después. Nunca se restauró sobre la base activa.

Se usó la clave ORIGINAL desde la custodia local con ACL limitadas a propietario
y SYSTEM. Recuperación independiente de Bitwarden: PENDIENTE, no acreditada
por esta prueba. Los objetos, claves, manifiestos privados y datos no se publican.

## Condiciones pendientes

GitHub mantiene una aprobación obligatoria y `python-checks`, sin bypass.
No hay aprobación independiente. Railway producción sigue `main`, con
`checkSuites=false`, sin controlador H-03 universal ni check H-03 obligatorio.
No se alteraron esas protecciones/configuraciones para forzar publicación.
La PR continúa en borrador y no se ha desplegado Honeypot en producción.

Última lectura Railway: producción conserva despliegue
`b2426f15-4826-4e22-9cd1-90ff3573d41b` SUCCESS de `main@c6a5c164`, volumen
`heraldo-data` en `/data`, sin cambios preparados. Test conserva despliegue
`c447c30d-fcb5-46d8-9908-f29747b69d91` SUCCESS de `Pruebas@b90e3a6`.


## 2026-11-04 — Promoción selectiva de etiquetas de reportes en main

- [x] Se añadió fuente independiente de etiquetas de reporte `production_report_labels.py` sin importar componentes extensos de `Pruebas`.
- [x] Se conservaron traducciones solo para etiquetas oficiales con el mismo emoji; textos libres quedan intactos.
- [x] Se añadió una prueba unitaria para tres idiomas y etiquetas personalizadas, y se incluyó en CI de `main`.
- [ ] Validación de visualización en Discord real tras despliegue autorizado.
- [ ] Incorporar el selector de idioma de servidor de `Pruebas` a `main` con sus dependencias, sin crear una experiencia de idioma engañosamente completa.
- [ ] Incorporar el módulo de recordatorios publicado y su índice para actualización histórica, con regresiones y prueba de permisos antes de declararlo listo.
- [ ] Confirmar estado real de Railway tras el próximo despliegue permitido, sin reactivarlo manualmente.

El cambio no despliega el sistema completo de traducción histórica: no trasladar archivos indiscriminadamente de `Pruebas` ni declarar éxito sobre mensajes ya publicados.


## 2026-11-04 — Aceptación selector /language + Recordatorios en main

- [x] Nuevo selector y panel en `/language` y `/setup` guardan por confirmación, conservando borrador y navegación.
- [x] Nuevos recordatorios habilitables solo con canal autorizado; frecuencia diaria, semanal, quincenal, mensual y personalizada con inicio explícito.
- [x] Se revisan y actualizan mensajes institucionales identificados en el mismo canal y mensaje, sin borrado ni publicaciones repetidas.
- [x] Se excluyen publicaciones de `/embed` y editor personalizado.
- [x] Se añadieron pruebas aisladas de catálogos en-US/pt-BR, texto personalizado, estado desactivado, cálculo de fechas, persistencia de referencias, guardado de idioma, reconocimiento de recordatorios y edición de un mensaje histórico simulada sin Gateway.
- [ ] Probar en servidor Discord real cambio es-419 → en-US → pt-BR → es-419 con un aviso anterior, comprobando ID inalterado y ausencia de menciones.
- [ ] Confirmar permisos y error seguro al perder acceso al canal.
- [ ] Confirmar que mensajes de sistema de main no catalogados permanezcan intactos (cobertura parcial).
- [ ] Verificar Railway cuando los despliegues de producción se autoricen de nuevo, sin reactivarlo.

No se habilitan mensajes por defecto ni se modifican los esquemas SQLite. Las regresiones offline no prueban Discord real ni el estado activo del servicio.
