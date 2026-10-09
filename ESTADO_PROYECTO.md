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
