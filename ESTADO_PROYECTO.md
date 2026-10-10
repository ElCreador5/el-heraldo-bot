# Estado compartido — El Heraldo

**Actualizado:** 2026-10-08
**Repositorio:** `ElCreador5/el-heraldo-bot`
**Producción:** rama `main` — no modificar sin revisión y autorización.
**Desarrollo/pruebas:** rama `Pruebas`, desplegada desde el servicio Railway `worker` del proyecto independiente **El Heraldo - Test**.
**Bot de prueba:** El Heraldo - Test; servidor de laboratorio: Heraldo's Lab.

## Verificaciones confirmadas
- Railway: despliegue de `Pruebas` en estado `SUCCESS`, commit `a69f59b` (observado 2026-10-08); conectado a Discord Gateway.
- Log de inicio: «Autoprueba /setup correcta en Heraldo's Lab» y conexión del bot de test; **esto no reemplaza ensayos manuales de botones**.
- Almacenamiento Railway independiente: volumen `worker-volume`, mount `/data`; servicio con variables `DISCORD_TOKEN`, `DB_PATH`, `MESSAGE_CONTENT_INTENT` (valores sensibles no documentados).
- GitHub Actions `python-checks`: compilación y pruebas de regresión completadas con éxito en los últimos cambios de código verificados; las pruebas de Discord siguen pendientes.
- Ramas de trabajo: `main` y `Pruebas`. PR histórico #2 fue cerrado sin fusionar.

## Módulo Mensajes en Pruebas (implementación parcial)
- Acceso desde `/setup`; plantillas con embeds, imagen URL, enlace y vista previa.
- Edición y publicación de plantillas; `/sendtemplate`.
- Botones y selectores de roles con comprobaciones de permisos; kits JSON básicos; editor raw.
- Confirmación de guardado, borrado e importación para operaciones del editor.
- `/edittemplate`: edición manual de un mensaje del propio bot mediante enlace y confirmación explícita.
- Pruebas de regresión para confirmación, cancelación, conflictos de kits y aislamiento de sesión.
- **No afirmar paridad completa con Sapphire:** falta completar acciones de componentes, menús avanzados, variables, edición visual avanzada, automatizaciones, programación, sticky y catálogo general de mensajes.


## Desarrollo actual — Logs de miembros (2026-10-08)
- En `/setup → Logs` la navegación hacia las plantillas visuales se eliminó: se editan en `/setup → Mensajes → Logs`.
- Categoría «Miembros»: salidas, expulsiones, baneos y advertencias, con eventos configurables y selección de canal individual. Los nuevos eventos empiezan desactivados y requieren «Guardar cambios» para activarse.
- Se añadió observación de `on_member_remove` y consulta de auditoría (si el bot dispone de acceso) para diferenciar salida, expulsión y baneo, sin emitir los tres registros por el mismo evento. Avatar, roles, fecha de incorporación y recuento actual se incluyen cuando están disponibles.
- **Limitaciones que requieren trabajo adicional:** la atribución de expulsiones/baneos depende de la auditoría de Discord y puede ser insuficiente o tardía; no se ha implementado aún un flujo específico para advertencias (warn), ni una prueba interactiva completa en Discord. La edición de plantillas existente necesita una revisión adicional para confirmar todos los guardados mediante botón explícito.
- No considerar paridad terminada con Sapphire ni desplegar este módulo a `main` sin validaciones.

## Continuidad: ampliación de Logs (2026-10-08)
- Los avisos de `/warn` ya generan un evento de miembros configurable cuando se crea correctamente un caso. El registro original de Moderation continúa independiente; vigilar posibles notificaciones redundantes.
- Se incorporó confirmación explícita para editar contenido y diseño de plantillas de logs y para restaurarlas; cancelar deja la configuración intacta.
- Pruebas offline adicionales: aislamiento por servidor, estado inicial desactivado, confirmación, cancelación y permisos del editor.
- **Pruebas reales de Discord todavía no realizadas:** confirmar salidas, expulsiones, baneos, advertencias, canales, permisos, edición visual, cambios de configuración, reinicios y manejo de auditoría tardía. No desplegar en `main` sin finalizar esta revisión.
- **Limitación:** la clasificación salida/kick/ban utiliza auditoría reciente; si la auditoría no está disponible o llega tarde, se puede clasificar como salida. La configuración de `warn` está disponible, pero no se ha verificado con una advertencia real en el laboratorio.

## Otras áreas que requieren pruebas en laboratorio
- Condena, perdón, tarjeta al canal y DM, evidencias persistentes, duración y permisos.
- Reaction Roles, Join Roles, verificaciones, reportes, logs, sugerencias y recuperación tras reinicio.
- Revisar `PRUEBAS_DISCORD.md` para casos y resultados; no confundir «implementado» con «comprobado».

## Próximo objetivo
Realizar recorrido real y reproducible de `/setup` → Mensajes (guardar, cancelar, publicar, editar, botones, roles, importación), registrar errores en `PRUEBAS_DISCORD.md` y corregirlos en `Pruebas`. Después ampliar las funciones respecto a la referencia Sapphire.

## Actualización
Cada agente debe registrar fecha, commit, resultado y riesgos reales; preservar historial. Esta página no es una garantía de que todas las funciones estén correctas.

## Publicación aislada de Logs a producción — 2026-10-09 UTC
- PR #4 fusionado a `main` por squash; commit `6f9f9ee0a7ed1c7b7e6c48a13817b9b5f3a5b667`.
- GitHub Actions: comprobaciones `python-checks` exitosas para el PR; sintaxis y cuatro regresiones offline específicas de eventos de miembros.
- Railway `©El Heraldo`, entorno `El Paraíso`: despliegue en estado `SUCCESS`; registro de conexión al Gateway Discord y autoprueba de `/setup` correctos.
- Incluye configuración de eventos/canales de miembros, logs de salidas, expulsiones, baneos, advertencias y guardado confirmado de plantillas desde Mensajes.
- **Pruebas reales de salida/kick/ban/warn en Discord: NO realizadas.** Los eventos nuevos empiezan desactivados y requieren activación administrativa. La consulta de auditoría necesita permisos; algunos eventos pueden no atribuirse con certeza.
- **Continuidad:** `Pruebas` ahora tiene un commit de `main` sin incorporar; reconciliar antes de futuras ediciones y evitar fusionar cambios experimentales completos.

## Laboratorio automatizado — propuesta en revisión (2026-10-09)
- Rama de trabajo: `feature/lab-automated-checks-20261009` (PR pendiente). Sin desplegar a `Pruebas` ni a `main`.
- Se propone CI para PR hacia `Pruebas`: compilación Python, `test_regressions.py` y descubrimiento de las regresiones `tests/test_*.py`, sin Discord ni tokens.
- Railway y la conexión a Discord deben comprobarse por separado tras un despliegue autorizado; `SUCCESS` no sustituye una prueba de botones.
- No existe automatización autorizada de cuentas personales. Una futura prueba de interacciones reales necesita diseño y credenciales de bot oficial separadas, con alcance y acciones limitadas.

## Continuidad — etapa 1 preparada, 2026-10-09 (America/Santo_Domingo)
- Bases comprobadas: `Pruebas@b8480b8`, `main@6f9f9ee`, PR #6 originalmente en `ffefb77`. Divergencia remota de partida: 48 commits exclusivos de Pruebas y 1 de main.
- Copia local preparada en la subcarpeta `el-heraldo-bot`, con entorno `.venv`. No iniciar `bot.py` para comprobar el entorno: el arranque real sincroniza comandos y activa tareas.
- Merge local `b181770`: incorpora `main` conservando íntegro `bot.py` de Pruebas. Los tres conflictos eran el comentario del observador de miembros, `LogTemplateResetConfirmView` y la entrada Mensajes del menú; se conservaron. Se incorporaron `test_member_logs.py` y su workflow.
- También se incorporó el historial del PR #6. Su actualización añade CI completo para Python 3.11/3.12/3.13, pin directo de discord.py solo para CI y exclusiones de archivos locales. La propuesta se publica en la rama existente del PR; no se hace push directo a Pruebas ni a main.
- Verificación local: Python 3.12.10, discord.py 2.7.1; compilación correcta, `pip check` correcto y 40 pruebas aprobadas (35 generales, 4 de miembros, 1 del selector). SQLite desechable, sin conexión a Discord.
- El sandbox de Windows bloqueó inicialmente temporales y red; las instalaciones y las suites SQLite se completaron con permisos concedidos. Se usó `-X utf8` para evitar errores de consola por la ruta Unicode.
- CI histórico del PR #6: ejecución 37889193532 correcta (35 + 1 pruebas). El resultado de la nueva matriz debe consultarse para el nuevo HEAD; no extrapolar el resultado anterior.
- Discord: NO probado en esta sesión. Railway: NO desplegado ni reconfigurado. Producción: sin cambios.
- Pendientes de etapas siguientes, detectados por inspección: rol 0 persistido en condenas nuevas; permisos no revalidados en algunas confirmaciones; emojis inválidos en selector de canales; modales de condenas con guardado inmediato; purga que continúa aunque falle el archivo de evidencias; expiración dependiente de caché y auditoría tardía en Logs.
- Conservar el aviso de verificación de preferencia: el PR #3 que pretendía eliminarlo se cerró sin fusionar.
- Siguiente paso: comprobar CI del PR #6, integrar mediante merge cuando se autorice el efecto de despliegue en laboratorio y abordar regresiones de condenas. Agent AVD no identificado inequívocamente; no atribuirle decisiones sin fuente.

## Punto de continuidad — 2026-10-10: correcciones en desarrollo
- PR #6 fusionado mediante merge en `Pruebas@34fa94f`; incorpora la ascendencia de main. CI posterior correcto; despliegue del laboratorio `f1b82ab5-0a4a-4071-9ee3-bb6fc596e6ab` correcto, con conexión Gateway y autoprueba de setup. No acredita pruebas interactivas. `main@6f9f9ee` permanece intacta.
- Trabajo nuevo: persistencia del rol real de condena; bloqueos por servidor/miembro para condena y perdón; expiración consulta miembros fuera de caché y conserva casos cuando no se puede consultar el servidor.
- Evidencias: sin respaldo al canal de condenados; rechazo de archivo público o autor distinto; copia de hasta diez adjuntos y cancelación de purga vinculada si la copia es incompleta. Pendiente revisar retención y archivo de todos los mensajes de una purga amplia.
- Configuración: permisos revalidados en 31 vistas, selector de canales corregido, propuestas confirmadas para diseño y duración de condenas, rechazo de borradores obsoletos en Mensajes y confirmación genérica.
- Logs: reintentos de auditoría y descripción explícita de incertidumbre. Aún necesita validación real de salidas, kick, ban y warn.
- Mensajes: texto independiente, hasta diez embeds, campos/autor/pie/miniatura mediante JSON o kit, seis variables con límites tras expansión, vistas previas sin ejecutar acciones, kit v2 e importación de archivo de hasta 128 KiB con reemplazo confirmado. Conserva kits v1 y plantillas anteriores.
- Publicación y edición comprueban permisos del usuario en el canal. Autoservicio de roles rechaza permisos administrativos, condenas activas y pulsaciones concurrentes; espera inicial y límite de frecuencia.
- Verificación local: 39 regresiones raíz y 25 en tests aprobadas en Python 3.12, discord.py 2.7.1, sin Gateway. Hubo una invocación incorrecta de unittest con discover como nombre de módulo; corregida y repetida con éxito. CI de estos cambios todavía pendiente.
- No está terminado el alcance completo: editor visual avanzado, menús independientes/multiacción, programación persistente, autorespuestas, sticky, webhooks, catálogo completo de textos y revisión integral de confirmaciones. Join Roles con demora aún utiliza tareas en memoria; pendiente recuperación tras reinicio. Reaction Roles y reportes requieren revisión adicional.
- Siguiente paso: preservar este lote en PR hacia Pruebas, ampliar pruebas de evidencia/restauración y completar módulos restantes antes de declarar preparado el recorrido integral en Discord. Agent AVD sigue sin identificarse inequívocamente.

### Continuidad adicional — 2026-10-10
- El primer lote está preservado en el PR #7 (borrador hacia Pruebas), commit remoto cb58e4e; CI 38033889706 aprobada en la matriz. Sin fusionar ni desplegar.
- Se añade cola SQLite de Join Roles: ingresos conocidos sobreviven reinicios, no repiten demora, esperan aceptación de reglas, consultan al miembro por API y descartan trabajos de ingresos anteriores o condenas activas. No recupera eventos que Discord no entregó durante una desconexión; requiere ensayo de reinicio real.
- Reaction Roles aplica también la política de roles administrativos y bloqueo por condena. Las regresiones existentes ahora declaran explícitamente permisos y tipo de los roles simulados.
- Doce modales adicionales preparan propuestas: tiempos generales, demora/sincronización de Join Roles, horario semanal, orientación, raids y textos/diseño de verificación y sugerencias. La propuesta incluye archivo comparativo y el panel se sincroniza después de confirmar. No implica que todos los comandos/configuraciones heredados hayan sido migrados.
- Pruebas locales: 39 raíz y 30 en tests aprobadas (69). Falta ejecutar la matriz remota para esta ampliación. Próximo bloque: restauración/evidencias y automatizaciones de Mensajes; aún no se declara preparación integral para Discord.

### Programación y estado más reciente — 2026-10-10
- Se incorpora `/programar_mensaje crear/listar/retirar`, accesible desde la ayuda de `/setup → Mensajes → Programación`. Publicación puntual, diaria o semanal con zona IANA y confirmación. Máximo 25 programaciones por servidor. Usa la versión guardada de la plantilla al ejecutar.
- Estado de ejecución en SQLite; vuelve a comprobar permisos del creador y del bot. Reinicios conservan pendientes; un envío interrumpido queda en revisión y no se repite automáticamente. Las ejecuciones vencidas se agrupan en un único envío al volver; no se reproduce todo el atraso. Una retirada no puede deshacer un envío ya iniciado.
- Se añade tzdata para disponibilidad de zonas en Windows. Compilación CI incluye los nuevos módulos.
- Corregida interferencia de los hooks globales: las plantillas explícitas conservan texto independiente y sus pies; no se les añaden caracteres después de validar el límite agregado de embeds.
- Estado de verificación actual: 78 pruebas offline (39 raíz + 39 tests), compilación y pip check correctos. La CI del primer commit del PR #7 pasó; consultar el HEAD más reciente para esta ampliación. Ninguna nueva prueba interactiva ni despliegue.
- Alcance restante: autorepuestas, sticky, webhooks, menús/opciones independientes y multiacción, editor visual avanzado, catálogo completo de mensajes, revisión de comandos heredados sin confirmación, pruebas de restauración parcial/evidencias y recorrido de reportes/verificación. No declarar terminado ni desplegar como versión final.

### Autorespuestas, sticky y webhooks — 2026-10-10
- CI del segundo commit remoto del PR #7, 4e696e6: ejecución 38034714893 correcta. Pruebas remotas y producción permanecen en 34fa94f y 6f9f9ee, respectivamente.
- Se añaden /autorespuesta crear/listar/retirar: coincidencia literal exacta o de palabra/frase, confirmación, máximo 25 reglas, espera persistente por regla y límite común de 30 segundos por canal. Se ignoran bots, webhooks y condenas activas; no se almacenan mensajes recibidos. Requiere Message Content.
- Se añaden /sticky crear/listar/retirar: un sticky activo por canal, confirmación, reposición tras actividad humana, espera configurable y recuperación SQLite. Comprueba que la publicación anterior pertenece al bot antes de retirarla. Actividad durante un envío queda pendiente. Retirar conserva la última publicación; los estados inciertos requieren revisión.
- Se añade /webhook_mensaje: propuesta visual, confirmación separada y permisos del autor/bot en destino. Solo crea/reutiliza webhooks del bot. No se aceptan URLs arbitrarias ni se almacenan tokens. Admite enlaces, pero no acciones de roles: estas deben publicarse mediante el bot. Un fallo incierto exige revisar el canal antes de reintentar.
- Accesos explicativos en /setup → Mensajes; listados extensos se adjuntan completos, sin perder identificadores por truncamiento.
- Verificación: 91 pruebas offline (39 raíz + 52 tests), compilación correcta. Pendiente CI del nuevo HEAD y pruebas reales. No se ha desplegado el PR #7.
- Próximo bloque: componentes por plantilla/opción y acciones múltiples, editor visual avanzado, catálogo de textos, revisión restante de condenas/restauración/evidencias y comandos heredados sin confirmación. Después validar el lote en laboratorio y registrar el recorrido interactivo. No declarar alcance total terminado.


### Estado consolidado para revisión del PR #7 — 2026-10-10
- Esta sección sustituye las listas de pendientes históricas anteriores. Nuevo editor `/editar_plantilla`: borradores visuales de texto independiente, múltiples embeds, imágenes, autor, pie y campos; guardar requiere confirmación y detecta cambios concurrentes. Un modal tardío no reabre un editor cancelado.
- `/componentes_mensaje`: botones y menús por plantilla, opciones independientes, selección múltiple y secuencias confirmadas de roles/respuestas/DM/canal/edición/eliminación. Revalida permisos, condena activa y jerarquía; limita frecuencia en SQLite y conserva auditoría de resultados sin contenido durante 30 días. El primer fallo detiene la secuencia con resultado parcial; no hay reversión automática.
- Honeypot: texto y diseño proponen cambios sin persistir; sincronización después de confirmar. La fotografía de roles de condena se guarda antes de la operación remota.
- Pruebas locales finales: 106 offline (39 raíz + 67 tests), compilación, dependencias y diff correctos. Sin Gateway ni pruebas Discord reales. Consultar GitHub para el resultado de CI del HEAD publicado.
- PR #7 queda preparado para revisión de código; no equivale a alcance total completado ni a despliegue validado. Laboratorio sigue en 34fa94f; main permanece intacta en 6f9f9ee.
- Pendientes y recorrido reproducible en REVISION_PR7.md. Prioridad: configuración heredada sin confirmación, archivo integral de purgas, restauración parcial; después catálogo uniforme y mejoras de importación/navegación. Agent AVD no identificado inequívocamente.
