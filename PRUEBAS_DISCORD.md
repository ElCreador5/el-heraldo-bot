## Encargo #23 — verificación de candidato (2026-10-23 RD / 2026-10-24 UTC)

- Nuevas regresiones en test_personality_deadline_runtime.py: chequeo antes del plazo, ampliación de plazo, marca rearmada, rol sin reloj, sanción de edad en curso, dos evaluaciones simultáneas, KICK fallido con reintento y construcción real de ambos selectores sin escribir configuración.
- Suites específicas: 57/57 correctas; tras reparar construcción del panel, 21/21 correctas incluyendo matriz de paneles de /setup.
- Candidato selectivo construido desde main@41f55654: 118/118 correctas, incluidas test_regressions y test_member_logs propios de main. No ejecuta Gateway; usa SQLite sintética.
- Suite general local Windows: 708 ejecutadas, 12 fallos, 122 errores y 13 omisiones. Predominan restricciones POSIX/fcntl/getuid, ACL de temporales y SQLite abierta en limpieza. No equivale a regresión Linux aprobada ni se han ocultado pruebas. Compilación y pip check correctos en el entorno con dependencias existentes.
- CI del SHA final: consultar después de push; el workflow issue23-selective-checks prueba separadamente el port sobre producción. La CI Linux de base e9f9f5a terminó SUCCESS (40049704649; Mensajes 40049704617).
- Discord real de este lote, respaldo nuevo/descifrado/restauración de producción: NO REALIZADOS. El estado y bloqueo exactos están en [[ESTADO_PROYECTO]]. No confundir el respaldo histórico del 18/10 ni la autoprueba /setup con estas verificaciones.

## Custodio — pruebas de núcleo, sin acciones Discord (2026-10-23)

tests/test_custodio_core.py comprueba extracción de TERMS, huella/versiones, obligatoriedad de Server Rules, fallos de payload y generación de revisión sin efectos laterales; tests/test_custodio_source.py comprueba lectura asíncrona de dos GET, fallos de API y credenciales, con dobles sin red. Confirmar CI del HEAD antes de decir SUCCESS. API REAL: continúa acreditada la prueba ciega anterior de 12 reglas en Heraldo's Lab; los módulos nuevos no se han empleado en Discord. DISCORD INTERACTIVO: no realizado. PENDIENTE: análisis de 12 reglas con contexto, relectura tras cambio, roles y permisos, canales inexistentes, duplicados y UI /setup.

## Modo Custodio: consulta REAL a API, NO interacción en Discord (2026-10-23 RD / 2026-10-24 UTC)

Prueba ciega autorizada en Heraldo's Lab (servidor 1557230352802644040). El propietario NO entregó el texto a ChatGPT.

Implementado en Pruebas: tools/custodio_rules_probe.py (5c175ce3) y tests/test_custodio_rules_probe.py (56f71528).

Discord real: GET del servidor HTTP 200 con MEMBER_VERIFICATION_GATE_ENABLED=true; GET de member-verification HTTP 200 con 1 campo TERMS y 12 reglas recuperadas de values.

Railway Test worker deployment 148dd771-d592-423c-a193-9a1c169e3a76, commit 56f71528, SUCCESS, Gateway conectado.

Sonda ejecutada una sola vez por preDeployCommand; después se restauró preDeployCommand=[] y sleepApplication=true.

Sin cambios del reglamento, sanciones, SQLite, bot de producción ni main. Las 12 reglas de laboratorio, no mensajes de usuarios, figuran en logs temporales de Railway Test, no en GitHub.

API de member-verification no documentada oficialmente y potencialmente inestable; NO se ha creado un motor Custodio, ni sincronización automática, ni sanciones.

Pruebas unitarias locales: 3/3; CI Mensajes SUCCESS; CI general estaba en progreso al inicio del cierre. No se probaron interacciones en Discord. Obsidian externo no conectado.

PENDIENTE: estabilidad de endpoint, cambios de normas, permisos mínimos, reglas ambiguas y confirmación previa a cualquier sanción.

## Publicación parcial verificada y puerta de datos — 2026-10-24

**PRODUCCIÓN:** GitHub `main@41f55654a92fa44c350d2a33d261979bf595deb2` incorpora solo texto de Verificación de personalidad, título preciso, plazo dinámico en resumen, normalización visual de escapes heredados sin reescribir SQLite y regresiones `tests/test_personality_copy_main.py` en CI. El CI `40046510765` terminó SUCCESS (sintaxis, dependencias, NH UX-03B, personalidad y logs). Railway producción desplegó exactamente el SHA en `54910927-bada-45ce-96c9-ef8cb4a81a84` SUCCESS; el Gateway conectó y los logs registraron autoprueba de /setup correcta. **Discord interacciones reales:** no ejecutadas por el asistente. **Datos:** volumen `heraldo-data` sigue montado en `/data`, sin migraciones ni escrituras deliberadas.

**PENDIENTE, SIN PUBLICAR:** port selectivo completo del módulo de Verificación de edad/personalidad (guardados transaccionales, permisos, exenciones, avisos y reintentos de KICK) y Comentarios voluntarios de salida con persistencia y privacidad. H-03 productivo continúa inactivo. No fusionar toda `Pruebas`: ramas divergentes, mantener funciones de main. Para cambiar sanciones o persistencia: primero copia online consistente de SQLite real **fuera del volumen**, restauración aislada y verificación de la clave y de recuperación; luego pruebas del port selectivo y publicación por entregas.

**RESPALDO:** consulta de solo lectura a Supabase Storage contabilizó dos objetos en `heraldo-production`, el último creado `2026-10-18 14:55:45 UTC`; no acredita recuperación ni actualidad. Las conexiones ChatGPT de Railway disponibles no incluyen consola ni transferencia de archivos del contenedor; no afirmar respaldo actual. Railway documenta SSH/SFTP/volume browse para acceso al volumen, que requiere autenticación del propietario o un acceso autorizado equivalente. No solicitar credenciales ni exponer datos privados.

**ESTADO DE DESARROLLO:** `Pruebas@8ec1681a42ab43359f9ac20e74b9a7c619556a7b` se desplegó en Railway Test `912fa92a-af48-4602-8db4-4c329ab9447a` SUCCESS el 24/10 UTC. Su CI anterior `39613646567` y `39613646672` es SUCCESS, pero no constituye validación interactiva de Discord. Las mejoras de Verificación y Comentarios todavía requieren aceptación en el laboratorio antes de producción. No se modificó ninguna variable de entorno ni se activó el programador productivo.

## Publicación selectiva NH UX-03B a main — 2026-10-21

**GitHub main ACTUALIZADO:** commit `2b6aeeb0fe1cc60154ac3ab179c3bec9463d9287`, base anterior `317ed8668b659af9f9945d1cb36027c7aca008b9`. Solo `bot.py` (botones y navegación /setup), `AGENTS.md` (UX-03B), `tests/test_ux_main_release.py`, y `.github/workflows/member-logs-checks.yml` (contrato UX en CI); sin fusionar toda Pruebas, sin cambios de esquema ni operaciones deliberadas sobre SQLite. Se normalizaron cuatro retornos Join Roles, tres etiquetas «Volver a /setup», rutas de Honeypot/Raid a AutoMod, Edad/Personalidad a Verificación y tres controles finales del editor de Roles del sistema.
**Verificación AUTOMÁTICA:** port aislado del código real de main, `Heraldo Lab - Python regressions` ejecución `39612383661` SUCCESS en 3.11, 3.12, 3.13 y UX-contract; CI de main ejecución `39612776885` SUCCESS.
**RAILWAY PRODUCCIÓN NO ACTUALIZADA EN RUNTIME:** servicio oficial sigue en despliegue `08846736-4ce5-47f2-bd70-7a50ab4cefce` SUCCESS del commit `317ed866`. La fuente del servicio fue fijada a `main@2b6aeeb0` mediante una modificación preparada de un único campo, no destructiva, aceptada en entorno `El Paraíso`, pero NO nació despliegue nuevo. Al intentar iniciar una compilación directa Railway rechazó: `Deploys have been paused temporarily`. El código nuevo NO está confirmado en el bot oficial. No usar «redeploy» de la compilación antigua para afirmar que se ha actualizado. Al reanudarse despliegues, reconstruir el commit fijado y verificar logs, SHA, estado de botones y navegación en Discord.
**Datos:** volumen productivo `heraldo-data` montado en `/data`, sin cambios de configuración; no se ha verificado una copia reciente de la SQLite real ni una restauración. La reversión de código referencia al commit y build anterior, no constituye respaldo de los datos. **DISCORD:** no se realizaron pruebas interactivas oficiales. **Obsidian externo:** no conectado.
**Alcance:** la integración presente cubre UX-03B y no significa integración total del módulo de Verificación de Pruebas ni de otros cambios divergentes. Candidato transitorio de 906 KB en Pruebas eliminado tras pasar las pruebas; contrato de regresión permanente queda en main.

## NH — Normalización transversal de botones y «Volver» (2026-10-21)

### Comprobación UX-03B — 2026-10-21

**IMPLEMENTADO** en `Pruebas@a705629c1cbc` después de corregir la saturación de Roles del sistema (tres botones de creación en fila 3 y Guardar, Descartar, Volver en fila 4). `AGENTS.md` incluye UX-03B, y `bot.py` actualiza navegación inmediata AutoMod/Honeypot/Raid, etiquetas Volver en Join Roles/Mensajes/Moderación/Reaction Roles y filas de Personalidad y Plantillas. **VERIFICADO AUTOMÁTICAMENTE:** GitHub Actions `39600553424` (ux-contract y offline-regressions Python 3.11, 3.12 y 3.13, SUCCESS) y `39600553426` (Mensajes, SUCCESS). El primer intento `8c6ebfb8` falló por seis botones en fila 3 de Roles; resuelto con commit `a705629c`, sin ocultar controles. **RAILWAY TEST:** el despliegue anterior `c4052ca` registró FAILED en fase BUILD_IMAGE; el nuevo SHA no consta como desplegado con éxito, sin evidencia de funcionamiento real. **DISCORD:** pruebas visuales y callbacks reales pendientes en Heraldo's Lab. **PRODUCCIÓN:** `main` y Railway oficial no modificados. **OBSIDIAN:** sin conexión externa confirmada.

**DECISIÓN**: aplicar UX-03B de `AGENTS.md` a todos los paneles de `/setup`: botones compactos/razonables, filas equilibradas y regreso al submenú inmediatamente anterior con la etiqueta exacta «Volver». Conservar otras etiquetas aprobadas, guardado explícito y datos. **Implementado en Pruebas (sujeto a CI):** renombrados los regresos de Join Roles y de módulos principales a «Volver»; las pantallas de Honeypot y Raid Protection regresan a AutoMod, sin perder su validación de borradores; se equilibran filas en Personalidad, Plantillas, Roles y Join Roles. Se conservaron las otras etiquetas. La UI de Discord limita los paneles de 10 controles de edad y reportes a dos filas de cinco botones tras los selectores: no se promete ancho idéntico. Regresiones nuevas en `tests/test_ux_buttons_navigation_nh.py`; pruebas automáticas y validación real en Discord pendientes. Cambio aprobado para `Pruebas`; `main` permanece sin modificar. Obsidian externo sin conexión confirmada.

## NH — Corrección preventiva de Verificación, pendiente de integración selectiva (2026-10-21)

**Pruebas únicamente:** corrección del resultado de expulsión de personalidad: una expulsión rechazada por Discord mantiene `tentado_at` para reintento y no se declara «expulsado»; el chequeo masivo ya no expulsa «Sin Verificar» directamente y remite al evaluador principal con su plazo y acción. Los guardados de edad y personalidad se revalidan antes de escribir, usan una transacción SQLite `BEGIN IMMEDIATE` con comprobación de valores anteriores y rechazo de sesiones obsoletas; personalidad comprueba canal, permisos, jerarquía y roles antes de sincronizar. En caso de fallar la sincronización de personalidad, se intenta restaurar los valores previos sin sobrescribir cambios ajenos y se comunica si requiere revisión. Se añadió regresión `tests/test_verification_nh_release.py`. **Este parche no modifica esquema de SQLite ni borra datos.** Pendiente: resultado CI del nuevo SHA, pruebas Discord, confirmaciones de creación/publicación, protección ante sincronización Discord a mitad de operaciones, preparación de port selectivo de `main` y comprobación previa a despliegue. **`main`: sin modificar.** Obsidian externo: no conectado.

## NH — Puerta de seguridad para publicación selectiva de Verificación (2026-10-21)

El propietario autorizó actualizar selectivamente `main` con el módulo de Verificación, pero la auditoría NH detectó elusión de edad por roles de personalidad y riesgo de roles públicos con permisos peligrosos. **Candidato preparado solo para `Pruebas`:** el procesamiento de reacciones exige verificación previa de edad cuando está activa (salvo exentos), rechaza condenados y roles de autoservicio peligrosos; la elección de roles y sincronización vuelven a validar privilegios; retirar una reacción no sortea «Cambiar elección: No»; el plazo de edad ya no acepta personalidad como verificación. Prueba de contrato en `tests/test_personality_safety_release.py`. **No representa aprobación de publicación:** siguen pendientes robustecer guardados de Edad/Personalidad, resultado y reintentos de KICK por personalidad, confirmaciones de publicación, pruebas de regresión del candidato, ensayos interactivos y comparación selectiva con `main`. No migrar SQLite ni copiar toda `Pruebas`. **Estado:** candidato sin CI / Discord hasta verificar el SHA; `main` y Railway producción no modificados por esta etapa. Obsidian externo no conectado.

## NH — Único plazo para la verificación de edad (2026-10-20, decisión posterior)

**DECISIÓN DEL PROPIETARIO:** por ahora se conserva únicamente el plazo principal de edad (verify_timeout). «Sin Verificar» sigue siendo un rol, pero NO inicia ni recupera un segundo reloj ni puede expulsar por sí mismo. Se retira el campo «Respaldo Sin Verificar» del formulario y de los resúmenes; el plazo de personalidad permanece independiente y sin cambios. Los datos históricos (sin_verificado_at y sin_verificado_timeout_seconds) y el esquema SQLite se conservan para evitar destrucción o migración. Al restaurar Sin Verificar tras levantar una condena, únicamente se programa un plazo principal NUEVO cuando la edad está activada y el miembro no está verificado ni exento. La acción al vencer sigue respetando Expulsar, Banear o Solo registrar, permisos, rol y jerarquía. La confirmación Guardar cambios sigue siendo obligatoria; Cancelar no persiste. Esta decisión prevalece sobre las descripciones históricas del editor con respaldo que siguen abajo. **Código:** solo rama Pruebas; **PRUEBAS AUTOMÁTICAS/CI:** pendientes de ejecutar para este cambio; **DISCORD:** pendiente de verificación real; **main:** sin modificar; **Obsidian externo:** no conectado.

## NH — Plazos de edad y personalidad en los mismos sitios (2026-10-20)

Ambas verificaciones usan el **mismo editor** de plazos desde `/setup → Verificación → Tiempos`, `Verificación de edad → Configurar tiempos` y `Verificación de personalidad → Configurar tiempos`. Se presentan los plazos vigentes de edad (`verify_timeout`), personalidad (`orientation_timeout_seconds`) y respaldo Sin Verificar (`sin_verificado_timeout_seconds`) sin alterar los datos. El formulario permite cambiar minutos y exige **Guardar cambios** en la confirmación; al abrirlo o salir sin cambios no escribe y al editar un único campo conserva los otros segundos originales sin redondeo destructivo. Los editores individuales rechazan abrir Tiempos si tienen otros borradores pendientes, para evitar pérdidas de cambios. PENDIENTE: CI actual y prueba interactiva en Discord Test. `main` no modificada.

## NH — Texto explicativo y distribución de personalidad (2026-10-20)

Decisión: los roles expresan cómo desea participar un miembro, que obtiene una elección mediante la reacción con el emoji del rol y puede cambiarla solo si se permiten cambios; permisos pueden desbloquear canales y la elección no verifica identidad/edad. Si la función está activada y es obligatoria, una falta al vencer el plazo genera expulsión automática con intento de DM previo e invitación de un solo uso para dar oportunidad de reingreso. No afecta la regla sin invitaciones para baneos o expulsiones manuales. En el panel: fila superior Volver/Activar/Desactivar/Editar embed; siguiente Cambiar elección/Expulsar si no elige/Editar DM; última Guardar/Descartar, sin eliminar borradores ni confirmaciones NH. Verificaciones Discord aún pendientes.

## NH — Formato de Verificación de personalidad (20/10/2026)

**Implementado en Pruebas, pendiente de CI/Discord:** se corrige el texto predeterminado que mostraba escapes literales \n dentro de la tarjeta de personalidad. El lector de textos normaliza también los escapes heredados guardados anteriormente, tanto en introducción como descripción, sin migrar ni sobrescribir valores existentes. Mantiene título, roles, reacciones, colores y referencias de publicaciones; al sincronizar el panel existente se actualiza el embed sin crear otra tarjeta. Regresiones aisladas en \`tests/test_personality_embed_linebreaks.py\`. No declarar verificación en Discord sin prueba real.

### Seguimiento de comentarios de salida y exenciones (20/10/2026)

Se añadieron regresiones ejecutables de privacidad de canales y segunda lectura de la auditoría de Discord: un acceso individual no moderador o desconocido impide las encuestas; un kick, baneo, error HTTP o falta de permisos también las impide. La solicitud se vincula a su DM y, si falla persistir esa relación, se intenta desactivar el botón sin repetir el aviso. El mantenimiento periódico recupera ediciones pendientes cada 15 minutos; las respuestas que ya se incorporaron a la tarjeta se purgan de SQLite a los 30 días, sin borrar la tarjeta. Las respuestas todavía no incorporadas se conservan para recuperación o revisión. La exención del propietario no detiene las rutas ordinarias de moderación. **Verificación en Discord: todavía no realizada.** No se modificó `main` ni se incorporaron datos privados a Git.

## Encuestas voluntarias de salida — 2026-10-20

**IMPLEMENTADO en `Pruebas`, sujeto a CI y Discord:** configuración separada y desactivada por defecto desde `/setup → Mensajes → Logs → Eventos de miembros → Comentarios de salida`, con Guardar/Descartar (NH); solo se solicita DM cuando la auditoría fue consultada satisfactoriamente sin encontrar un kick/ban, existe la tarjeta original y el canal de logs está restringido al personal moderador. Los errores o permisos insuficientes de auditoría cancelan la encuesta. El botón persistente de DM abre un modal voluntario (máximo 500 caracteres, siete días); SQLite asocia la solicitud por servidor, miembro, DM y tarjeta, evita duplicados y conserva respuestas pendientes de editar tras reinicios. `exit_comment_apply` edita la tarjeta, no crea registros secundarios; sin respuesta no muestra el campo «Comentario». El usuario solo puede responder a su propio DM. Las solicitudes pendientes sin respuesta se purgan después del periodo de retención. No se altera el motor de sanciones ni `main`.

**Verificación real en Discord:** NO realizada. La aplicación de respuesta depende de permisos en el canal y puede quedar pendiente si este se elimina o vuelve público. El registro en SQLite se debe respaldar antes de aplicar a producción.

## NH — Controles de personalidad con guardado explícito (2026-10-20)

**IMPLEMENTADO EN Pruebas, CI/Discord pendientes:** `HeraldoOrientationSetupView` ofrece «Obligatoria», «Cambiar elección» y «Editar DM de recuperación», todos con borradores sin escritura. El modal requiere `{invitacion}` o `{invite_url}`, y solo Guardar cambios persiste las opciones y la plantilla; Descartar no guarda. El listener impide cambiar roles cuando el administrador desactiva esa opción y elimina la reacción no autorizada; nunca retira roles ajenos. La desactivación conserva panel/roles. Corrección de saltos de línea en resumen y panel. Tests nuevos `tests/test_personality_setup_contract.py`. **PENDIENTE:** verificaciones automáticas, pruebas reales Discord, comentarios de salida y comparación de diferencias con main.

## NH — Verificación de personalidad sin eliminación de configuración (2026-10-20)

**IMPLEMENTADO EN Pruebas; CI y Discord por verificar:** se renombra el lenguaje visible de la antigua orientación/preferencia a Verificación de personalidad, sin migrar claves internas ni roles. El sistema puede estar activo sin ser obligatorio mediante `personality_required` (predeterminado activo para respetar instalaciones anteriores); los timers de personalidad no se arman cuando está desactivado/no obligatorio o el miembro es moderador. La desactivación ahora conserva **panel, vínculos y roles existentes**, pausa pendientes `tentado_at` y muestra panel desactivado sin destruir referencias. `personality_allow_change` prepara la opción de cambio (activada por defecto). **PENDIENTE:** exponer controles y plantilla DM en `/setup`, activar política de cambio de elección, tests de desactivación y revisión de compatibilidad antes de producción. Sin migración de esquema.

## NH — Notificaciones de sanciones y recuperación por personalidad (2026-10-20)

**IMPLEMENTADO EN Pruebas (pendiente de CI/Discord):** el bot oficial avisa **antes** del KICK automático por no completar personalidad, con frase «está prevista tu expulsión», variables `{servidor}`, `{razon}`, `{titulo_embed}`, `{invitacion}` resueltas por servidor y plantilla opcional `personality_recovery_dm_template` con fallback formal. El DM previo es la excepción deliberada: si Discord rechaza después el kick, puede haber recibido ese aviso, pero nunca uno que afirme expulsión completada. La notificación especial de El Heraldo Test se mantiene **después de la sanción**: las invitaciones solo se preparan para expulsión automática por personalidad y nunca para BAN o expulsiones manuales. Los fallos de expulsión se registran como advertencia, no como tarjeta de éxito. Tests: `tests/test_test_mode_removal.py` y `tests/test_personality_recovery_dm.py`. **PENDIENTE:** editor de plantilla en /setup, mensajes de otras medidas experimentales, catálogo de personalidad, pruebas reales Discord y publicación selectiva en main.

## NH — Exenciones de moderación en verificación (2026-10-20)

**IMPLEMENTADO EN Pruebas (pendiente de CI y Discord tras este commit):** se añade `verification_is_exempt` para dueño y equipo con permisos efectivos de moderación/administración (incluidos Gestionar servidor, Gestionar mensajes, Expulsar, Banear, Aislar). Las evaluaciones de vencimiento, ingreso, conciliación, verificación por roles y expulsión de orientación preservan la exención. Al adquirir privilegios se cancelan marcas de verificación/orientación; al perderlos, se inicia un plazo nuevo si aún no se verificó, sin sanción retroactiva. **No altera condenas ni privilegios de moderación ordinaria.** Regresiones añadidas a `tests/test_verification_staff_exemption.py`, `tests/test_verification_expiry.py` y `tests/test_verification_reconciliation.py`. La verificación automática y el laboratorio deben comprobarse antes de trasladar selectivamente a `main`; no hay cambios de esquema ni datos.

## Raid Protection — Guardar una sola vez y actualizar el mismo panel (2026-10-20)

**IMPLEMENTADO EN main:** `317ed8668b659af9f9945d1cb36027c7aca008b9` (base `e607ce7`). Se elimina la segunda pantalla de confirmación exclusiva de Detección; el botón verde «Guardar cambios» es la confirmación explícita de los cinco parámetros. Ejecuta persistencia SQLite atómica `BEGIN IMMEDIATE`, compara las cinco claves originales para detectar otra sesión, revalida identidad y permiso Gestionar servidor antes de guardar, valida límites y combinación edad/proporción, y no hace escrituras sobre cambios inválidos o descartados. Tras `commit` relee la configuración guardada, actualiza `original`, `draft`, opciones marcadas y contenido del mismo mensaje, sin «(pendiente)». Se mantienen Descartar y Volver sin guardado, y los borradores independientes del panel principal. No cambia sanciones, motor antiraid ni esquema SQLite.

**PRUEBAS AUTOMÁTICAS:** candidato aislado `317ed866` validado mediante GitHub Actions `39394086440`: compilación, dependencias y suite main de 121 pruebas SUCCESS; incorpora 7 regresiones en `test_raid_save_main.py` y modifica `.github/workflows/member-logs-checks.yml` para ejecutarlas en main. El primer intento `39393893001` falló por una hipótesis inválida del test de concurrencia; corregido y reejecutado con éxito. **PRODUCCIÓN:** publicado con fast-forward; comprobar Railway y CI del SHA final en su propio registro. **DISCORD OFICIAL:** el propietario aportó captura del fallo anterior; todavía no se ha comprobado interactivamente la corrección publicada. **RESPALDOS:** cambio de interfaz y persistencia de settings existentes, sin migración de esquema ni respaldo nuevo/restauración en este trabajo. **OBSIDIAN:** no se actualizó por falta de conexión verificada.

## Raid Protection — publicación selectiva oficial (2026-10-20)

**IMPLEMENTADO EN PRODUCCIÓN:** GitHub `main@e607ce7af38560a694e8c2095871861f8a125178` (base `647b9f5`, actualización fast-forward); solo cambió `bot.py`. Se trasladaron el editor de cinco parámetros, niveles Moderada/Equilibrada/Estricta, valores personalizados, ayudas, selección marcada y confirmación transaccional específica para main con comprobación de propietario/permisos y concurrencia. Se preservó la corrección simultánea de logs de expulsión. No se modificó esquema SQLite, motor antiraid ni sanciones; no se fusionó Pruebas.

**VERIFICADO AUTOMÁTICAMENTE:** ejecución aislada `39392746095` sobre el candidato exacto: compilación, dependencias, suite de regresiones vigente de main, controles de borrador/permisos/confirmación y SQLite desechable: SUCCESS. GitHub Actions de `main@e607ce7`: `python-checks` SUCCESS, Supabase Preview SUCCESS. Railway producción: despliegue `0de1ab67-eee4-44cf-864b-d6c94e3a68f6` SUCCESS, servicio Online, un despliegue activo y sin errores en los registros de arranque consultados.

**VERIFICADO EN DISCORD:** el propietario comunicó que probó satisfactoriamente la interfaz en Discord Test. No se ha ejecutado validación interactiva independiente de la interfaz recién publicada en Discord oficial. **RESPALDOS:** antes del cambio se verificó la existencia de respaldos históricos en Supabase, pero NO se creó un respaldo nuevo ni se probó restauración de SQLite productiva en esta operación; actualización exclusivamente de interfaz sin migraciones según política NH de 2026-10-20. **RIESGO RESIDUAL:** un SUCCESS de Railway no certifica todos los botones en el servidor oficial. **OBSIDIAN:** conexión externa no comprobada; no actualizado.

**SIGUIENTE ETAPA:** comparar capacidades de Pruebas frente a main antes de decidir la reconstrucción de la rama; no eliminar Pruebas sin inventario y acuerdo del propietario.

## DM de expulsión solo tras ejecución confirmada; propietario exento — 2026-10-19

**IMPLEMENTADO en `Pruebas@b2a94d9586f879669aff7a6c48fb970a164d750b` y VERIFICADO AUTOMÁTICAMENTE:** los avisos de expulsión y baneo del laboratorio y el DM de recuperación por orientación se envían solo después del éxito de Discord. El bot puede abrir previamente un canal de DM sin entregar contenido para mejorar la disponibilidad posterior. La creación de invitación y el envío ocurren exclusivamente tras la sanción. Si Discord rechaza la acción, no se manda DM ni se genera enlace; si el DM falla después del éxito, no se repite la expulsión. Se preserva el aviso correspondiente a la primera y segunda expulsión real de orientación. El propietario del servidor queda excluido de vencimientos de verificación, conciliación y chequeos masivos; los temporizadores existentes se limpian al evaluarse. Regresiones en `tests/test_test_mode_removal.py` y `tests/test_verification_expiry.py`: rechazo de KICK/BAN, orden de notificación y caso del propietario. GitHub Actions run `39304602390`: `ux-contract` y `offline-regressions` con Python 3.11, 3.12 y 3.13 SUCCESS; Mensajes run `39304602496`: SUCCESS. Railway Test desplegado (ID `eaf37ecd-a3d4-4fe5-a4cf-282de935e9a9`): SUCCESS. **Prueba real en Discord NO REALIZADA**; Railway SUCCESS no prueba que el DM se entregue tras perder la pertenencia al servidor. **main y producción:** intactos. **Obsidian externo:** no conectado ni modificado.

## Raid Protection — editor de detección y perfiles (2026-10-19)

**IMPLEMENTADO en Pruebas:** el editor abre dos páginas de selectores con los cinco parámetros, perfiles Moderada (15/30s/3d/70%/10m), Equilibrada (10/30s/7d/60%/15m) y Estricta (5/10s/14d/50%/30m); admite valores personalizados individuales. Guardado mediante la confirmación transaccional existente, descarte sin escritura, retorno al panel sin borrar otros borradores, validación de proporción y bloqueo por cambios concurrentes. No se alteraron sanciones, motor de detección ni esquema SQLite. Los perfiles son hipótesis de configuración y NO tienen eficacia empírica demostrada. Pruebas automáticas: CI del nuevo commit por verificar; Discord real: NO REALIZADA. main/producción: NO MODIFICADA, puertas H-03 vigentes. Obsidian externo: sin acceso confirmado.

## Raid Protection — orientación contextual para administradores (2026-10-19)

**IMPLEMENTADO en Pruebas:** cada opción del selector de respuesta describe el efecto real y sus riesgos; el selector de rol explica que es solo para alertas, y los cinco campos de Detección incluyen ejemplos prácticos, distinción de antigüedad, porcentaje y duración del modo raid frente a sanciones. El botón Guardar/confirmación y las sanciones no cambian. Se respeta la norma general UX-03A ya creada en `ad874d7`; no se crean DM ni mensajes de ayuda adicionales. **Regresiones:** `tests/test_raid_contextual_help.py`; **CI:** pendiente de verificar en el SHA de esta modificación. **Discord real:** pendiente. **Otros paneles:** pendiente aplicar UX-03A al revisarlos. **main/producción:** sin cambios. **Obsidian:** sin conexión externa verificada.

## Raid Protection — selección persistente en el desplegable (2026-10-19)

**IMPLEMENTADO en Pruebas:** `HeraldoRaidSetupView` sincroniza la opción marcada con el borrador tras seleccionar una acción, y con el valor guardado tras Guardar o Descartar. Antes el menú marcaba solo el valor inicial, aunque el contenido reflejaba el cambio pendiente. No cambia la acción real hasta Guardar, no modifica sanciones ni esquema SQLite. **Regresión:** `tests/test_raid_action_select.py` prueba selección, varias elecciones, guardado, descarte, rechazo de Condenar sin rol y conservación tras cambiar otro control. **VERIFICACIÓN AUTOMÁTICA:** pendiente de CI para el SHA resultante. **VERIFICACIÓN REAL EN DISCORD:** no realizada. **main/producción:** pendiente de revisar y superar puertas H-03 antes de publicar; no equivale a despliegue. **Obsidian externo:** sin conexión verificada; no actualizado.

## Matriz UX y comprobación automatizada — 2026-10-19

`Pruebas@b3e4afc`: se añadieron 3 pruebas conductuales en `tests/test_ux_panel_matrix.py` que recorren todas las secciones visibles de `/setup` y verifican navegación sin modificaciones SQLite, controles serializables, colores de botones y aislamiento entre vistas. El job `ux-contract` combina esa matriz con 170 regresiones existentes de comportamientos de interfaz, permisos, borradores, confirmaciones y editores. **GitHub Actions run 39256959260: SUCCESS**; la matriz/contrato ejecutó 6 pruebas y el bloque de regresiones 170, en Python 3.12; las 3 variantes de la suite global de Lab también SUCCESS. **VERIFICADO EN DISCORD:** NO REALIZADO: apertura real de módulos, menú a submenú, Cancelar/Guardar, botones antiguos tras reinicio, permisos revocados y aspecto de embeds siguen pendientes en Heraldo's Lab. **Importante:** el check CI no sustituye validación real ni garantiza cobertura completa de callbacks profundos.

## Honeypot — Guardar en submenús, 2026-10-19

**IMPLEMENTADO en `Pruebas@8cf69065`**: los submenús Acción y Configurar medida disponen de **Guardar cambios** (verde), **Descartar cambios** (rojo) y Volver (gris). Sin borrador, Guardar/Descartar permanecen deshabilitados. Guardar reutiliza el mismo procedimiento y validaciones del panel principal; Descartar limpia el borrador sin escribir SQLite y vuelve al panel. No cambian sanciones ni valores existentes. Regresiones de `tests/test_honeypot_panel.py` verifican callbacks, colores y ausencia de guardado implícito. GitHub Actions `39211237913` Python 3.11/3.12/3.13 SUCCESS y `39211237881` python-checks SUCCESS. **Discord real:** pendiente. Port selectivo a producción preparado mediante PR #22; no afirmar desplegado antes del deployment.

## H-03 — Adaptador Railway Test de SHA exacto y preflight opt-in (2026-10-18)

**IMPLEMENTADO en Pruebas, NO activado:** cliente real `h03_railway_test_api.py` de la API GraphQL pública de Railway, limitado al proyecto/entorno/servicio de **Test** y a la rama `Pruebas`. Publica exclusivamente el commit de 40 caracteres indicado mediante `serviceInstanceDeployV2`, sin reintentos automáticos en caso de incertidumbre; comprueba posteriormente por deployment ID, `status=SUCCESS`, commitHash y servicio/entorno de Test. Los fallos de GraphQL ocultan la respuesta del proveedor y jamás registran tokens. Documentación oficial: https://docs.railway.com/integrations/api/manage-services y https://docs.railway.com/integrations/api/manage-deployments.

`h03_test_railway_release.py` conecta el H03 real de Test (`backup_job.run_once(environment="heraldo-test",purpose="preupdate")`, descarga/descifrado AES-GCM, restauración aislada, SHA origen/destino) al diario durable `h03_release_handoff.py`. CLI seguro: `prepare`, `dispatch`, `boot`, `finalize`, `status`. **Sólo admite identidad real de Test**; requiere aprobación del SHA en la variable Test `HERALDO_H03_TEST_APPROVED_TARGET_SHA` y, para enviar/comprobar deployment vía API, un token del **proyecto Test** exclusivamente mediante `HERALDO_H03_TEST_RAILWAY_TOKEN`. Ni variable está instalada por este trabajo en Railway. `bot.py` comprueba el arranque antes de crear Discord solamente cuando la bandera `HERALDO_H03_TEST_STARTUP_GATE=enabled-after-test-owner-approval` esté presente; permanece DESACTIVADO por defecto para no interrumpir Test.

**VERIFICACIÓN:** pruebas mock sin red en `tests/test_h03_railway_test_api.py` y `tests/test_h03_test_railway_release.py`, más regresiones existentes. El estado CI del commit final se verificará después de publicarlo. Se han consultado despliegues reales del worker de Test mediante conexión Railway: `d4bec0cb` figura como `SUCCESS` con commitHash coincidente. Eso comprueba lectura de metadatos mediante el conector; **NO es una publicación H03 real**. Actualmente no existe acceso remoto para ejecutar comandos en el proceso dueño de `/data` desde esta sesión, ni token de proyecto Test configurado, por tanto **NO se ejecutó `prepare`/ `dispatch` ni un despliegue supervisado extremo a extremo**. Nunca afirmar que ocurrió.

**PENDIENTE real:** usar entorno de ejecución autorizado sobre el worker Test para crear la copia y el diario, configurar token de proyecto Test bajo custodia privada temporal, desactivar/desacoplar trigger automático de Test para ensayo, activar la comprobación de arranque sin redeploy prematuro, despachar el commit exacto, confirmar nuevo boot y SUCCESS, finalizar/reconciliar; luego ensayar fallo/rollback. Nada de esto se hará en producción sin nueva autorización. Los auto-deploy de producción continúan desactivados; `main` y PR #19 siguen separados. Discord interactivo: no probado para este desarrollo.

## H-03 — Diario duradero de dos fases (2026-10-18)

**IMPLEMENTADO EN `Pruebas` (LAB-ONLY):** `h03_release_handoff.py` conserva un estado privado POSIX por solicitud y un puntero activo, usando `flock`, escrituras atómicas y `fsync`. Secuencia: preparado (respaldo/restauración verificados por adaptador) → envío registrado antes de contactar proveedor → enviado → nuevo proceso admite arranque solo para SHA correcto y respaldo autenticado → controlador confirma el deployment FINAL y marca completado. Si el resultado es ambiguo o se interrumpe la operación, **no se repite automáticamente el despliegue**, se conserva el recibo y se bloquean autorizaciones superpuestas. Se impide reutilizar solicitudes, continuar diarios huérfanos o saltar estados. Un despliegue completado admite reinicios verificados y deja el historial para el siguiente release.

**Pruebas aisladas:** `tests/test_h03_release_handoff.py` valida proceso Python independiente, reinicios, reintentos, identificadores inválidos, caducidad, carreras y fallos de proveedor; ejecutadas por GitHub Actions en 3.11/3.12/3.13. Estado CI del commit final: pendiente de consultar. No se alteró `main`, la PR #19 ni Railway producción. No se restauró SQLite productiva ni se automatizaron cuentas personales. **LÍMITE:** este diario admite solamente `lab`, no contiene credenciales ni clientes de Railway/GitHub, y no está conectado al preflight opt-in productivo. No prueba un controlador no eludible. Falta controlador externo real, unión criptográfica con la copia del deployment, autorización de arranque por nueva revisión y rollback ensayado antes de activar producción. Discord real: NO REALIZADO para H-03.

## H-03 — Adaptador de publicación y preflight de arranque (2026-10-18)

**IMPLEMENTADO EN `Pruebas`, NO ACTIVADO EN PRODUCCIÓN:** `h03_publication_adapter.py` exige laboratorio y adaptadores fiables, verifica SHA de origen/destino, objetivo aprobado, copia restaurada, callback de autorización único y estado FINAL del despliegue (no confunde recibir un ID con éxito). `h03_startup_gate.py` valida identidad exacta de Railway, recibos privados, estado del permiso, antigüedad y manifiesto remoto autentificado AES-GCM con restauración aislada. `bot.py` ejecuta este preflight antes de crear el bot solo al correr como proceso principal; permanece **desactivado sin `HERALDO_H03_STARTUP_GATE=enabled-after-owner-approval`** y exige ID de solicitud exacto. La variable de activación NO se añadió en Railway Test ni producción.

**IMPORTANTE:** el publicador actual es un CONTRATO DE LABORATORIO con interfaces inyectadas, NO un cliente real de Railway/GitHub. Falta resolver el reinicio del proceso dueño de `/data` mediante protocolo duradero de dos fases; `preupdate_gate.guarded_update` síncrono no puede considerarse un publicador completo si el worker se termina al desplegar. Debe integrarse un adaptador confiable externo, confirmar restauración y cierre durable, y blindar todas las rutas antes de habilitar producción. Un comprobador de arranque opt-in no protege frente a administradores que lo desactiven; los autodespliegues siguen desactivados. La PR #19 se conserva separada.

**PRUEBAS:** regresiones aisladas nuevas de publicación/arranque (falsificación de permiso, caducidad, SHA distinto, resultado de despliegue no confirmado, errores del proveedor); CI pendiente de confirmar tras commit. **Discord real:** no realizado para este controlador. **Railway producción:** intacto; ninguna clave, archivo SQLite ni variable productiva modificada aquí.

## H-03 — núcleo de respaldo previo preparado en Pruebas (2026-10-18)

**IMPLEMENTADO SOLO EN `Pruebas`, INACTIVO EN PRODUCCIÓN:** incorporación de `preupdate_gate.py` y pruebas offline de PR #18, reconciliados con el respaldo de Test actual; `backup_job.py` permite una generación `preupdate` única, vinculada a SHA de origen/destino dentro de manifiesto cifrado y restaurado. `sqlite_recovery.py` conserva la compatibilidad de copias diarias. Identidad real del volumen productivo verificada en preflight, sin acceder a secretos. Ningún script se invoca automáticamente para publicar versiones. **PENDIENTE:** adaptador autorizado conectado a GitHub/Railway, barrera obligatoria de despliegue, prueba end-to-end del publicador y validación en producción. No fusionar `main` por la existencia de este código. Verificar CI antes de afirmar éxito. Pruebas Discord de este núcleo: no realizadas. La PR #19 de Honeypot continúa separada y sin desplegar.

## H-03 Test real — primer respaldo externo recuperado (2026-10-18)

Base GitHub comprobada y sincronizada: Pruebas@926f6d552f42aca1b63b0e8cbff6d8dd7b335d27.
Implementación directa autorizada por el propietario: worker con backup SQLite
online, bucket/identidad/clave exclusivos Test, recibo anterior a upload,
recuperación aislada por fecha y horario 06:15 UTC con catch-up. Se conserva el
cron sintético con sus credenciales y las generaciones históricas. 18 tests nuevos,
72 H-03 y 39 base OK; compilación y dependencias OK. Suite global SSH interrumpida:
pendiente CI. Transferencia REAL completada 18/10/2026 09:02:59 UTC: 479232 bytes SQLite,
89228 cifrados; descarga, AES-GCM, integridad/FK, esquema y contenido recuperados
correctos. Bot en el mismo proceso y copias previas conservadas. Programador
aún pendiente de despliegue/activación y verificación posterior.
Detalles operativos únicos en RESPALDOS_SUPABASE.md. PR #18 revisada, en borrador:
CI 39075261350 SUCCESS, 22 tests del guard; no integra publicador ni evita bypass.
No se fusionó la PR. main y producción conservan el bloqueo de DECISIONES.md.
Discord interactivo y recuperación independiente de clave ORIGINAL: no realizados.

## H-03 — Contrato de controlador de laboratorio (2026-10-17)

**VERIFICADO AUTOMÁTICAMENTE:** `python -m unittest discover -s tests -p 'test_*.py' -v` mediante GitHub Actions `39089544729`, Python 3.11/3.12/3.13 SUCCESS. Los 15 tests nuevos de `tests/test_h03_release_controller_contract.py` figuran OK (Python 3.12: 475 tests/ OK). Incluyen fallos de copia no verificada, origen/candidato alterado, devolución sin publicación, callback omitido/repetido, adaptador ausente e intento de producción; ningún test utiliza datos privados, servicios reales ni Discord. **Discord real: NO REALIZADO**. **Railway Test: el SUCCESS del despliegue no certifica acciones H-03**. PR #18 continúa bloqueada; la integración real del guard remoto/custodia queda pendiente de autorización y pruebas. Ver `audit/H03_CONTROLADOR_LAB_2026-10-17.md`.

## Logs de miembros — patrón compacto inspirado en Sapphire (2026-10-17)

**Commit de código `cfa65386`:** `bot.py` y `tests/test_member_departure_cards.py`; 12 casos nuevos con AST/simulaciones para salida, kick, BAN temporal/permanente/sin datos, expiración, actor, roles masivos, avatar, motivo y tarjeta especial de orientación. **VERIFICADO AUTOMÁTICAMENTE:** GitHub Actions `39072801052` SUCCESS Python 3.11/3.12/3.13, run `39072801040` SUCCESS del flujo Mensajes. Los logs del job Python 3.13 confirman cada uno de los casos específicos como OK, 460 pruebas en la suite. **Railway Test:** worker y cron SUCCESS tras código. **VERIFICADO EN DISCORD:** NO REALIZADO. Pendiente enviar en Heraldo's Lab, con usuarios de prueba autorizados, salidas, expulsión por orientación, kick manual, ban temporal, ban permanente y ban externo; comprobar colores, retrato, motivos, vencimiento y que no aparezcan tarjetas duplicadas. No probar con miembros reales ni desplegar `main`.

## Verificación: deduplicación de alertas y aislamiento de Test — 2026-10-17

**COMMIT:** `4b09b5ff`, archivos `bot.py`, `tests/test_verification_reconciliation.py`, `tests/test_verification_notice_persistence.py`. Los tests nuevos simulan reinicio sin duplicación, cambios de conjunto, resolución/reaparición, envío fallido, nuevos plazos e imposibilidad de rearmar fuera de laboratorio. **VERIFICADO AUTOMÁTICAMENTE:** Heraldo Lab Python 3.11/3.12/3.13 SUCCESS `39071427613`; Mensajes SUCCESS `39071427760`. **Railway Test:** worker/cron SUCCESS y el worker registró arranque y nuevo diagnóstico de 5 casos a las 21:34 UTC tras el commit. Los cuatro avisos anteriores de 11 casos fueron emitidos por Test en 21:18–21:23 UTC. **VERIFICADO EN DISCORD:** recepción del diagnóstico deducida del registro de envío del bot, pero NO se realizó interacción de prueba con cuentas autorizadas ni verificación visual de no duplicación tras un segundo reinicio. Pendiente ensayo de reinicio con conjunto invariable y control administrativo de casos anteriores. Producción no tocada.

## Verificación confirmada por CI — Roles huérfanos (2026-10-17)

**GitHub Actions `Pruebas@8fe6ad50`:** Heraldo Lab `39070454746` SUCCESS en Python 3.11, 3.12 y 3.13, Mensajes `39070454752` SUCCESS. Registro del job de Python 3.11: seis tests `test_verification_reconciliation.py` OK, suite tests/ de 442 tests OK. **Railway Test:** worker y servicio cron SUCCESS, y se observó conexión del worker al Gateway. **VERIFICACIÓN REAL EN DISCORD: NO REALIZADA.** Pendiente prueba segura de roles recientes/antiguos tras desconexión simulada, recuento administrativo, sin expulsiones retroactivas. `main` y Railway producción intactos.

## Verificación: conciliación de roles sin seguimiento — 2026-10-17

**IMPLEMENTADO** en `Pruebas@22078f82`: nuevo test `tests/test_verification_reconciliation.py` verifica en simulación roles antiguos/recentes, estados contradictorios, condena, verificación desactivada, plazo no duplicado y límite de 25; sin expulsión remota. **CI:** Mensajes `39070271627` SUCCESS; Heraldo Lab `39070271559` cancelado por nuevo commit de documentación, nuevo run `39070308567` pendiente de resultado. **RAILWAY TEST:** autodespliegue en curso en el momento de documentar; no confundir despliegue con prueba funcional. **DISCORD REAL: NO REALIZADO.** Ensayar con miembros sintéticos y roles autorizados: simulación de reinicio con SQLite persistente, falta de seguimiento para miembros recientes/antiguos, configuración Solo registrar, rol incompatible, errores de API y ausencia de sanción retroactiva. No probar sobre miembros reales, no ejecutar `/heraldo_check_all` como procedimiento de recuperación.

## Honeypot: cierre de confirmación efímera — 2026-10-17

**Automatizadas:** commit de código `8eb6019`, run `39070088743` SUCCESS para Python 3.11/3.12/3.13 y `39070088787` SUCCESS para Mensajes; Railway Test (worker y cron) SUCCESS en SHA `8eb6019`. Tests actualizados `tests/test_honeypot_warning_publish.py`, helper de `tests/test_safety_regressions.py`: apertura como seguimiento efímero tras defer de componente, confirmación con ACK antes de llamadas API, guardado/actualización del embed del aviso, eliminación del mensaje secundario y cancelación sin persistencia, reentradas, revocación de permisos, plantilla/canales/borradores obsoletos, fallo de panel y cierre alternativo si Discord rechaza la eliminación. Código en `bot.py`; interfaz `/setup → AutoMod → Honeypot → Configurar aviso`. **PRUEBA REAL EN DISCORD: NO REALIZADA** después del parche. Laboratorio: confirmar y cancelar varias veces, verificar que el segundo mensaje desaparece y se actualiza el embed inicial sin reapertura; provocar error de permisos, canal eliminado, plantilla cambiada y red inestable sin duplicaciones. No probar en producción.

## Honeypot sin retención de evidencias — comprobaciones cerradas (2026-10-17)

**GitHub Actions:** commit de código `8816b319`, run `39062591876` SUCCESS en Python 3.11, 3.12 y 3.13; run de Mensajes `39062591851` SUCCESS. Fallo inicial detectado en run `39062406007` (duplicado aún archivaba pruebas) y una vía con límite de cantidad corregidos por `8816b319`. Nueva suite `tests/test_honeypot_no_evidence.py` y pruebas de aislamiento/expulsión actualizadas. **Railway Test:** worker y cron, código `8816b319`, estado SUCCESS. **DISCORD REAL: NO REALIZADO**: pendiente aceptación en Heraldo's Lab con miembros ficticios autorizados. No se alteró main; no afirmar equivalencia entre CI y prueba interactiva.

## Honeypot: exclusión de evidencias por origen — 2026-10-17

Regresiones añadidas `tests/test_honeypot_no_evidence.py`: sólo autor detectado y mismo servidor, límites temporales, permisos revocados, concurrencia, purga en varios canales sin eliminar ajenos, no escritura de contenido, conservación del archivo para moderación ajena y propagación del origen. Actualizadas pruebas de aislamiento y expulsión. **Pruebas automáticas remotas y Discord real: PENDIENTES** al preparar el commit. En Heraldo's Lab validar expulsión de cuenta de prueba y búsqueda sólo de sus mensajes en diferentes canales; aislamiento y condena sin archivo pero con expediente; sanción manual sí conserva evidencia; comprobar roles, falsas capturas, reinicios y canales sin permisos. Nunca usar producción.

## Honeypot: nueva publicación explícita de avisos — 2026-10-17

Nueva suite `tests/test_honeypot_warning_publish.py` verifica botón verde y confirmación/cancelación con colores correctos; sin trampas o con borrador pendiente no publica; Cancelar no escribe SQLite ni sincroniza; autorización revocada y canal/permisos insuficientes bloquean; cambio de plantilla o lista de trampas invalida confirmación; publicar aviso desactivado lo activa y llama una sola vez a la sincronización; errores parciales nunca se anuncian como éxito; aviso ya existente se edita sin crear duplicados. **VERIFICADO AUTOMÁTICAMENTE:** CI Heraldo Lab `39056219619`, Python 3.11/3.12/3.13 SUCCESS; Mensajes `39056219466` SUCCESS; Railway Test worker/cron SUCCESS con código `Pruebas@475c1f8f`. **DISCORD REAL: NO REALIZADO.** Laboratorio: abrir el panel en Test, editar y confirmar texto/diseño, pulsar Publicar aviso (y cancelar una vez), comprobar pin y actualización sin mensaje duplicado, varios canales, pérdida de permiso Embed Links y Manage Messages, canal borrado y plantilla modificada entre apertura/confirmación. No probar fuera de Heraldo's Lab.

La petición relativa a dejar de retener evidencias no Honeypot sigue pendiente de definición antes de tocar motor global de sanciones y purgas.

## Honeypot: expulsión con purga y configuración visual — 2026-10-17

Nuevo archivo `tests/test_honeypot_kick_purge_setup.py`: valida 1 día predeterminado/mínimo incluso con valores incorrectos, programación del motor compartido con intervalo de un día, opciones de 1 a 30 días, selección que solo prepara borrador, Descartar sin escritura, guardar explícito, rechazo de snapshot concurrente, acciones contextuales Role/Timeout/Kick/Ban/Log sin dependencia obligatoria de `/honeypot setup`, duraciones de baneo y aislamiento editables, y valor de baneo independiente del módulo general. Se amplían las regresiones existentes `tests/test_honeypot_kick_ban.py` para comprobar el inicio único de purga tras expulsión y su ausencia ante error API. Las pruebas de evidencias `tests/test_purge_evidence.py` siguen cubriendo archivo antes del borrado del motor compartido. **VERIFICADO AUTOMÁTICAMENTE:** CI Heraldo Lab Python 3.11/3.12/3.13 `39055478658` SUCCESS y Mensajes `39055478741` SUCCESS para `Pruebas@94fac034`; Railway Test worker y cron SUCCESS. El run anterior de `69d04d55` detectó una prueba que elegía el valor predeterminado sin generar borrador; el fixture se corrigió en `94fac034` y se repitió toda la matriz. **DISCORD REAL: NO REALIZADA.**

Aceptación en **El Heraldo Test / Heraldo's Lab** con cuentas autorizadas: comprobar selectores según acción, 1 día por defecto, guardado y descarte, texto del embed, cambio de configuración simultáneo y permiso revocado; en ensayo aislado comprobar Kick único, aviso Test, expediente, ventana de 24 h y que los mensajes no archivados siguen presentes. Comprobar logs de purga parcial/error/reinicio; ninguna prueba destructiva sobre miembros reales ni despliegue de `main`.

## Honeypot: pruebas de Expulsar/Banear — 2026-10-17

Suite agregada: `tests/test_honeypot_kick_ban.py`. Escenarios: no reinterpretar valores legados `kick`/`ban`; mostrar nuevas opciones de menú; selector no escribe SQLite; Descartar cancela el borrador; permisos administrativos y del bot rechazados al guardar; confirmación Slash guarda valores nuevos explícitos; ejecución una sola vez del expulsar/baneo usando funciones existentes y expediente `KICK`/`BAN`; baneo usa duración general y no purga; revocación de permisos, propietario/jerarquía; error Discord sin expediente y fallo de SQLite sin repetir la sanción; embed de ban solo muestra duración pertinente. **VERIFICADO AUTOMÁTICAMENTE:** commit `Pruebas@143c855f`, Heraldo Lab `39053065266` (Python 3.11, 3.12, 3.13 SUCCESS; instalación, pip check, compilación y regresiones de Honeypot), Mensajes `39053065320` SUCCESS; Railway Test worker/cron SUCCESS. **DISCORD REAL: NO REALIZADO.** En Heraldo's Lab y El Heraldo Test probar con cuentas autorizadas, no con miembros reales: abrir selector, elegir y Descartar/Guardar; revocar permisos durante edición y entre detectar/aplicar; confirmar expediente, registro e invitación/aviso Test; comprobar que el ban de Test expire o se pueda revertir; verificar que el umbral antifallos sigue protegiendo al tercer miembro y que las acciones anteriores no regresionan. No activar ban/kick automático en `main` sin autorización expresa.

## Honeypot: aceptación de nueva interfaz de AutoMod — 2026-10-17

Pruebas añadidas en `tests/test_honeypot_panel.py`: distribución y estilos de controles, etiqueta dinámica de pausa y reanudación, selección de canal ya registrado sin duplicar, acción solo en borrador y descarte sin persistir, Crear canal sin efecto antes de confirmación y con revalidación de permisos, rechazo de guardado por cambios de otro administrador, embed conciso con medidas aplicables y los dos editores de aviso accesibles desde un único panel. **VERIFICADO AUTOMÁTICAMENTE:** `Pruebas@2d6b3aa`, CI Heraldo Lab `39050050630` (Python 3.11, 3.12, 3.13 SUCCESS) y Mensajes `39050050561` SUCCESS; pruebas del panel y paleta, compilación y demás regresiones incluidas. Railway Test worker y cron SUCCESS. **DISCORD REAL: NO REALIZADO.** En El Heraldo Test / Heraldo's Lab validar el aspecto real del embed (móvil/escritorio, menciones y límites), subpaneles Volver, canales ya registrados, varias trampas, creación con confirmación/cancelación, retención de configuración en SQLite, efecto de Pausar y Reanudar, aviso texto/diseño con confirmaciones propias, permisos revocados, canal borrado y borrador obsoleto. No sancionar miembros reales; `main` intacta.

## Honeypot: conservación del mensaje que activa la pausa — 2026-10-17

**VERIFICADO AUTOMÁTICAMENTE** en `Pruebas@9d68886f`: GitHub Actions `39040312547` SUCCESS en Python 3.11/3.12/3.13 (instalación, pip check, compilación, tests y regresiones), y Mensajes `39040312540` SUCCESS. Railway Test worker y cron SUCCESS. Se incluye la regresión: regresión `test_threshold_message_stays_original_and_moderators_are_notified` comprueba 2 veteranos anteriores + tercero, no invocar `delete_with_evidence`, no sancionar, registrar pausa 101, enviar aviso formal con canal/miembro y no borrar eventos del servidor 202. Regresión `test_normal_detection_still_archives_before_punishment` comprueba que la ruta sin pausa sigue llamando a la función de archivo/borrado antes del castigo, con sus logs. **DISCORD: NO REALIZADO.** En Heraldo's Lab con Test: configurar canal trampa, logs privados, tres miembros de ensayo con antigüedad suficiente en el servidor (o simulación segura sin sanciones de usuarios reales); observar preservación exacta del tercero, pausa, aviso único, ausencia de sanción al tercero y reinicio/resume. Sin canal de Logs o permisos no se garantiza entrega del aviso: comprobar degradación sin pérdida del mensaje.

## Seguridad Honeypot: aislamiento multiservidor — 2026-10-16

Nueva suite automatizada `tests/test_honeypot_isolation.py`: (1) veteranos mezclados entre servidores no pausan uno ajeno; (2) tercer veterano del mismo servidor pausa solo ese y conserva el historial temporal de otros; (3) eventos concurrentes del mismo miembro en servidores distintos se procesan, pero duplicados simultáneos intraguild siguen bloqueados; (4) caducan detecciones viejas y no persisten falsos umbrales; (5) `/honeypot history` rechaza lectura sin Gestionar servidor. **VERIFICADO AUTOMÁTICAMENTE:** CI `38980795158` sobre `e379fc96`, Python 3.11/3.12/3.13 SUCCESS (instalación, pip check, compilación, regresiones existentes y cuatro pruebas nuevas); Mensajes `38980795137` SUCCESS. Railway Test: despliegues de worker y cron SUCCESS tras el push. **Discord real: NO REALIZADA.** Laboratorio: repetir con dos servidores autorizados, reacciones de usuarios de prueba, revocación de permisos, duplicados y reseteo por umbral. No ejecutar sanciones ni supresiones reales de miembros. Observar que el mensaje del último veterano pasa por `delete_with_evidence` antes de la pausa: comportamiento anterior conservado y pendiente de decisión.

## Pruebas de aceptación de /fusionar_canales renovado — 2026-10-16

**VERIFICADO AUTOMÁTICAMENTE:** commit `4cc337d0`, CI Heraldo Lab `38978968508`, Python 3.11, 3.12 y 3.13 SUCCESS; Mensajes `38978968411` SUCCESS. Pruebas de `tests/test_fusion_preview.py`: descripción de ruta y orden, estado de origen, nombres y contadores, verde Confirmar / gris Volver / rojo Cancelar, editor de borrador no destructivo, verificación previa del contador y permisos, conservación del origen si llegan nuevos mensajes o falla su segunda lectura. **EN DISCORD: NO REALIZADAS.**

Probar exclusivamente con El Heraldo Test y canales de Heraldo's Lab: 1) vista previa precisa de origen/destino/cantidad/secuencia y conservación de mensajes existentes en destino; 2) Volver con cambios en cada selector, nombre personalizado, eliminación sí/no, actualizar vista previa sin persistencia; 3) Cancelar y cerrar sin cambios; 4) Confirmar realmente con pocos mensajes sintéticos, comprobar orden cronológico, autor y fecha en embeds, multimedia y enlace de respaldo si falla archivo; 5) impedir fusión por recuento cambiado y permisos revocados; 6) no borrar origen en caso de mensajes/ediciones nuevos, error de lectura, falla de adjuntos o envío; 7) verificar logs, permisos después de reinicio e idempotencia ante confirmaciones repetidas. Evitar datos privados, purgas y pruebas sobre servidores ajenos. No aprobar `main` por Railway SUCCESS.

## Aceptación pendiente: Cancelar / Cerrar rojos — 2026-10-16

Cambio de estilo en `Pruebas`: etiquetas «Cancelar», «Cancelar edición» y «Cerrar» pasan a rojo en los paneles de `bot.py` y módulos de Mensajes. Regresión `tests/test_button_palette.py` ampliada. Verificación automática de este SHA: pendiente de GitHub Actions al preparar esta nota. **VERIFICACIÓN REAL EN DISCORD: NO REALIZADA.** Probar en Heraldo's Lab: Cancelar en borrador sin modificar BD; Cerrar sin guardar; salir de una confirmación destructiva sin ejecutar la medida; «Volver» conservado gris; tras reinicio, callbacks y botones operativos. No realizar sanciones ni purgas reales fuera del laboratorio autorizado.

## Pruebas pendientes del estándar de colores — 2026-10-16

VERIFICADO AUTOMÁTICAMENTE en `Pruebas@c32141eb`: `tests/test_button_palette.py` integrado en la matriz del CI, GitHub run `38976183423` SUCCESS (3.11/3.12/3.13), verificación Mensajes run `38976183535` SUCCESS. **VERIFICACIÓN REAL EN DISCORD: NO REALIZADA**. En El Heraldo Test / Heraldo's Lab comprobar: botones Guardar verdes, Descartar rojos, Cancelar y Volver grises, formularios Editar azules, y sanciones Banear/Expulsar/Advertir rojas. Verificar colores dinámicos en Activar/Desactivar programación, crear/agregar/retirar trampas Honeypot y componentes de Mensajes cuyo flujo puede eliminar un mensaje. Un botón de enlace usa estilo `link` y no tiene color de acción configurable. Confirmar que cambiar estilos no alteró `custom_id`, callbacks, botones tras reinicio, accesibilidad, permisos ni acciones reales; no ejecutar sanciones sin cuentas de ensayo autorizadas.

La sustitución del doble paso «Revisar» por Guardar cambios directo y la reversión de borradores de programaciones son tareas funcionales **pendientes**, no se consideran validadas por esta prueba de color. Continuar con los demás módulos de forma controlada, sin cambios en producción.

## Aceptación pendiente tras recuperación de CI — 2026-10-16

VERIFICADO AUTOMÁTICAMENTE: GitHub Actions run `38868053698` a `Pruebas@453488d9`, tres matrices 3.11/3.12/3.13 SUCCESS. Los 16 errores de fixtures y dos fallos de AST anteriores se corrigieron sin rebajar protecciones: la normalización real de reglas de `report` y `warn` descarta purgas aun con datos heredados; test del motor `report` exige ausencia de sanciones/purga; el editor de reacciones se comprueba mediante selección de acción, modal de condiciones y ausencia de persistencia hasta Guardar. Unicode 15 (🪽) validado aun simulando Python 3.11. CI verde no prueba el comportamiento en Discord.

PRUEBA EN DISCORD **NO REALIZADA**. En Heraldo's Lab, exclusivamente El Heraldo Test, verificar selección/edición/guardar/cancelar por acción (report, warn, timeout, condemn, kick, ban) sin guardar prematuramente; «Solo reportar» no borra mensajes, conserva evidencias y no aplica sanción; permisos/jerarquía revocados entre interacciones; SQLite bloqueada al perdonar; vistas y paneles tras reinicio con invitaciones negadas; vencimiento MUTE con HTTP fallido y sanción posterior. Confirmar DM, expediente, respuesta efímera y ausencia de logs duplicados. El despliegue Railway Test SUCCESS para `453488d9` no reemplaza ninguna aceptación. No ejecutar purgas destructivas ni pruebas de producción. 

## Aceptación pendiente: vencimiento aislado de MUTE — 2026-10-16

En Heraldo's Lab probar vencimiento normal de un timeout de 1m autorizado; fallo de Discord al retirar el timeout (el expediente debe quedar abierto y reintentarse); nuevo aislamiento activo antes de expirar el antiguo (no debe levantarse), y aislamiento manual posterior más largo no registrado (mantenerlo). Revalidar con reinicio y roles no manejables. Ninguna prueba real realizada por el asistente.

## Auditoría de fiabilidad: ensayos pendientes — 2026-10-16

VERIFICACIÓN EN DISCORD NO REALIZADA. Laboratorio: retirar permiso Gestionar roles durante el fetch de un miembro que pulsa componente, y desplazar jerarquía del rol; no debe asignar/quitar nada y debe responder sin quedar colgado. Simular SQLite bloqueada al intentar perdonar con otra acción en curso: no ejecutar perdón, conservar expediente y registrar el error. Revocar Ver registro de auditoría/gestión de invitaciones o negar invitaciones en un servidor de prueba durante un reinicio: el bot debe continuar arrancando, registrar error y mantener paneles/vistas recuperables de otros servidores. Probar panel antiguo y nuevo tras reinicios, sin mezclar aplicaciones Test/Main. Ejecutar tests/test_reliability_startup_roles.py y verificar CI exacto.

## Matriz complementaria propuesta por investigación de usuarios — 2026-10-16

Fuente: «Voz de los usuarios: quejas, fallos y peticiones sobre bots de Discord», pp. 3–10. **TODAS LAS COMPROBACIONES A CONTINUACIÓN SON PROPUESTAS; NO EJECUTADAS.** Consolidarlas con las pruebas ya descritas en este archivo, sin reemplazar sus resultados. Solo El Heraldo Test y Heraldo's Lab con usuarios autorizados.

- Permisos y jerarquía: retirar permisos del bot o situar el rol objetivo fuera de su alcance durante un ensayo controlado; comprobar explicación precisa y ausencia de cambios parciales en SQLite/Discord.
- Paneles y reinicios: reiniciar Test con varias vistas antiguas y nuevas que compartan diseño; comprobar que cada botón conserva identidad y destino correctos; no reutilizar mensajes/paneles entre aplicaciones Test y producción.
- Interacciones lentas: probar operaciones con latencia o respuestas API fallidas; deben responder/diferir antes del límite de Discord y no declarar éxito sin confirmación.
- Fallos parciales: canal de logs borrado, DM rechazado, canal/permisos revocados, reinicio entre Discord y SQLite; el expediente persistente debe permitir recuperación sin duplicar sanción ni perder evidencia exigida.
- Concurrencia y ráfagas: dos moderadores actuando sobre un mismo expediente y numerosos eventos/logs; verificar idempotencia, control de tasa y ausencia de notificaciones repetidas.
- Reingreso y vencimiento: restauración segura de roles o sanción al volver, con jerarquía, duración y expiración visibles; no levantar un baneo posterior al vencer un caso anterior.
- Datos y secretos: auditar inventario de datos persistidos, acceso, retención, secretos en logs/variables/repositorio, infraestructura innecesaria e intents privilegiados. No volcar secretos ni evidencias privadas a informes.
- Verificación y accesibilidad: causas de rechazo, reintentos autorizados, DM inaccesible y falsa detección; comprobar que los mensajes al usuario son concretos y no prometen acciones que no se completaron.

No implementar un comando de diagnóstico, apelaciones o nuevas medidas de raid basándose únicamente en esta matriz; requieren alcance, riesgos y autorización del propietario.

## Comprobación pendiente: programar embeds y redacción — 2026-10-15

VERIFICACIÓN REAL EN DISCORD: NO REALIZADA. En Heraldo's Lab comprobar Por mensajes (10), canal seleccionado, botón Activar, revisión y Confirmar; los saltos de línea reales, ninguna estructura JSON y ningún texto contradictorio. Tras revisar, modificar estado/canal/frecuencia y asegurar nueva revisión obligatoria. Cancelar antes y después de revisar no debe guardar. Probar modal en seis frecuencias, edición existente y programaciones inactivas. Verificar controles y textos en Discord sin modificar producción. Test test_embed_schedule_wording.py.

## Validación pendiente: duplicación de logs de orientación — 2026-10-15

PRUEBA EN DISCORD NO REALIZADA. En Heraldo's Lab con un miembro autorizado, inducir vencimiento de verificación de preferencia; comprobar un único embed «Kick — Falta de verificación», con primera/segunda falta, estado del DM y resultado correctos, sin «Miembro expulsado» adicional. Repetir con report=False (debe quedar log general cuando esté activado), canal de logs inaccesible, fallo HTTP al enviar, salida voluntaria, expulsión manual por un moderador externo, nuevo ingreso del mismo usuario y ausencia de permisos de auditoría. Ejecutar tests/test_orientation_kick_dedup.py y CI. Verificar otros tipos de expulsión por separado, sin dar por completada una auditoría transversal.

## Pruebas pendientes: /embed crear — 2026-10-15

VERIFICACIÓN REAL EN DISCORD: NO REALIZADA. En Heraldo's Lab comprobar creación con «Información general», «Guía de inicio 🪽», nombres ASCII existentes y longitud 64; rechazo de 65 caracteres, menciones y controles; duplicados con mayúsculas y espacios; editar, enviar, programar, listar y borrar con autocompletado. Conservar embeds anteriores y aislar por servidor. Suite aislada tests/test_embed_names.py y CI del SHA final pendientes de evaluar.

## Comprobación pendiente: Test y Baneo temporal — 2026-10-15

NO REALIZADA prueba real en Discord. Usar únicamente El Heraldo Test y Heraldo's Lab con cuentas autorizadas. Probar motivo único de condena originada por rol manual, comando, Honeypot y raid, y edición al perdonar; expulsar/banear por comando, botón y reacción, DM previo único con disculpa e invitación de 1 uso, DM cerrado/fallo de Create Instant Invite, acceso al canal al volver y no reutilización de invitación; Test BAN 5m predeterminado, sobreescritura temporal y 0 permanente; /setup → Moderation → Baneo temporal, selección, personalizado, confirmación, Cancelar, persistencia tras reinicio, concurrencia, jerarquía y unban fallido. Verificar casos persistidos y logs. Suite CI y Railway del commit final por comprobar.

## Verificación de acciones por reacción y escalamiento WARN — 2026-10-15

Código implementado en `Pruebas` para controles de acciones habilitadas, política al llegar a 3/3 (configurable 1–5), reclamo SQLite idempotente, DM anterior a escalamiento y condena directa con permiso y jerarquía revalidados. Test `tests/test_moderation_reaction_policy.py` prueba defaults y desactivación, reclamo de aislamiento único con SQLite temporal, despacho positivo/negativo del motor de condena, jerarquía y distribución del editor; se ejecutan además `tests/test_moderation_warn_limit.py`, `tests/test_moderation_warning_reaction.py`, `tests/test_moderation_report_actions.py`, `tests/test_setup_editor_selectors.py` y `tests/test_editor_drafts_behavior.py`. **VERIFICACIÓN REAL EN DISCORD: NO REALIZADA**. El despliegue/Test exitoso solo valida arranque, no interacciones. En Heraldo's Lab, con miembros autorizados, ensayar: Reportar sin sanción, WARN/❗ solo staff y relevo de reacción, Aislar, Expulsar, Banear y Condenar por umbral; condena directa con motivo, privilegios revocados, objetivos de jerarquía superior, expediente, hilo, DM, purga con evidencia y ningún doble log; acción global desactivada, umbral 1 y 2, simultaneidad, reinicio, configuración/cancelación y desactivación durante ejecución; máximos 3/3 y 5/5 y reacción del bot. Probar recuperaciones si hay error SQLite/Discord entre reclamo y sanción: nunca reintentar ciegamente. Controlar `main` sin cambios y `preDeployCommand` del worker Test al cierre.

## Ejecución parcial de regresiones WARN — 2026-10-15

**VERIFICADO AUTOMÁTICAMENTE EN RAILWAY TEST (commit `fbd87211`, y repetido en `87da9a6b`):** las cuatro pruebas de `tests/test_moderation_warn_limit.py` pasaron: valor por defecto 3, techo 5, bloqueo transaccional al llegar al límite, historial cerrado e idempotencia por reacción. En esos despliegues la suite `tests/test_moderation_warning_reaction.py` falló por dos expectativas del test: fixture aislado sin la nueva función de límite y comparación textual de comillas de `ast.unparse`. Se corrigieron el fixture en `9e7837ad` y la expectativa de comillas en `a20403b9`. **PENDIENTE:** volver a ejecutar la suite completa sobre el SHA final y probar las interacciones reales de Discord; estas ejecuciones parciales no acreditan funcionamiento completo ni habilitan producción.

## Verificación requerida: máximo de advertencias 3/5 — 2026-10-15

**IMPLEMENTADO en código / Pruebas:** contador de WARN vigentes, valor por defecto 3, selector de máximo 1-5, `/warn`, reacción ❗, consulta `/advertencias` y registro en DM/log. La inserción manual y por reacción se protege con transacción, máximo compartido e historial intacto. Suites aisladas: `tests/test_moderation_warn_limit.py`, `tests/test_moderation_warning_reaction.py`. **No afirmar pruebas ejecutadas hasta confirmar resultados en Railway y CI; pruebas interactivas Discord: PENDIENTES.** En Heraldo's Lab probar 0/3 a 3/3, intento 4/3, actualización 3→5, reducción 5→2 con más casos previos, cierre y expiración, concurrentes `/warn` + ❗, ausencia de autosanciones, aislamiento por servidor y confirmación/Cancelar del selector. Comprobar que una WARN cerrada no cuenta, sin borrar su expediente; verificar DM/log, emisor autorizado, mensaje original y cambio de reacción.

## Acciones automáticas por reportes — 2026-10-15

En `Pruebas` se implementaron controles de permisos, duración y jerarquía, persistencia de expedientes para timeout/kick/ban, y deduplicación del aviso de purga exitosa en el reporte principal. `tests/test_moderation_report_actions.py` contiene regresiones aisladas de caso único, aislamiento por servidor, permisos, fallo de SQLite sin repetir sanción, Solo reportar y timeout sin duración. **Discord real: no probado**. Probar en Heraldo's Lab umbral 1 y 2, usuarios distintos, reacciones repetidas, sanción con y sin purga, archivo privado antes de borrar, permisos revocados, jerarquía, bot protegido, reinicio y fallo de registro; verificar que no se aplique una sanción dos veces ni haya doble aviso de éxito. La creación de expediente tras una sanción aún deja una ventana no atómica Discord/SQLite, que requiere evaluación. No usar producción.

## Pruebas pendientes: nuevos editores de horario y reportes — 2026-10-15

**IMPLEMENTADO EN Pruebas (código):** selector de 7 días y 24 horas para Miembro de la Semana, con confirmación; selector de 5 acciones en Moderation → Reportes, con umbral/duración/purga editables, borrador separado y revalidaciones. Nuevas pruebas de AST y ejecución aislada de callbacks en tests/test_setup_editor_selectors.py y tests/test_editor_drafts_behavior.py. **Las pruebas todavía no se han ejecutado ni acreditado en esta sesión; revisar CI y despliegue exactos.**

**PRUEBA INTERACTIVA EN HERALDO'S LAB: PENDIENTE.** Comprobar elegir/descartar horario, guardar horario, horario sin cambios, confirmar en otro panel, permisos caducados y configuración modificada en otra sesión. En reportes: seleccionar reacción, cambiar acción, abrir Regla, cancelar, guardar, repetir tras reinicio; Solo reportar elimina solo la purga pendiente, nunca ejecuta purga; Timeout sin duración debe rechazar Guardar, y un canal borrado/sin permisos no debe guardarse. Probar el selector adicional dentro del máximo de cinco filas Discord. No usar miembros reales ni producción.

## Reaction Roles: selector de opciones — 2026-10-15

**IMPLEMENTADO, pendiente de verificación real:** el editor de opciones ahora usa tres listas desplegables para modo de acceso (3 opciones), reacciones invertidas (2) y máximo de reacciones (21 valores). Se mantiene borrador separado y Descartar no persiste. Guardar explícitamente desde editor publica; sin escrituras al seleccionar. `tests/test_reaction_options_dropdown.py` añade comprobaciones estructurales, CI del SHA exacto pendiente. Probar real en Heraldo's Lab cambiando modos, cancelando, guardando, reiniciando y verificando la persistencia.

## Validación pendiente: hilo privado de expediente y duración elegible — 2026-10-15

**IMPLEMENTADO en `Pruebas`** (sujeto a CI): tarjeta de condena intacta y ping en el canal, hilo privado sin asociación nativa al mensaje pero enlazado por botón «Conversación privada», miembro condenado invitado, personal con Gestionar hilos autorizado. Persistencia por servidor en guild_cases, sin hilos duplicados si ya hay thread_id; recuperación tras reinicios, cierre archivado sin borrar conversación, errores registrados sin revertir una condena válida. Preparación manual de permisos del rol requiere confirmar en /setup. Duraciones conocidas disponibles mediante desplegable con confirmación y opción personalizada. Migración de BD aditiva, no destructiva.

**VERIFICACIÓN AUTOMÁTICA:** `tests/test_condemnation_private_threads.py` cubre hilo privado exclusivamente, mención y orden de pasos, permisos, reinicios, guardado condicional, archivo y selectores. Ejecutar GitHub Actions y consultar SHA exacto.

**VERIFICACIÓN EN DISCORD:** NO REALIZADA. Solo Heraldo's Lab / El Heraldo Test. Escenarios: bot con permisos Create Private Threads/Manage Threads y usuario rol Condenado con View Channel/Read Message History/Send Messages in Threads; verificar misma tarjeta/DM, mención única, acceso a hilo propio pero no otro, enlace, comunicación, permisos de personal, confirmación de acceso, duración del menú, caída de API, reinicio, perdón y expiración. Confirmar nivel 2 del servidor para privados. Si no está disponible, no improvisar público ni probar en producción. Verificar si una persona con permiso Manage Threads puede ver todos; no concederlo al rol Condenado. `main` intacta.

## Registro único de condena con purga — 2026-10-15

**DETECTADO (captura oficial + código):** el mismo proceso de condena con purga publica «Condena aplicada» y «Purga de condena completada» como dos avisos separados. La copia privada «Evidencia archivada» y el perdón son eventos distintos y deben mantenerse.

**IMPLEMENTADO EN `Pruebas` (pendiente de CI):** se registra inmediatamente la condena y, al concluir la purga, se edita el mismo embed con alcance y resultado. Se conserva el log alternativo si no existe el inicial o falla editarlo; los errores de purga siguen generando advertencia. La orden `/purge` y otras purgas conservan registro independiente.

**VERIFICACIÓN AUTOMÁTICA:** regresiones añadidas en `tests/test_condemnation_log_dedup.py`; consultar ejecución y resultados de GitHub Actions, no presumir que están aprobadas antes de comprobarlos.

**VERIFICACIÓN REAL DISCORD:** no realizada para esta modificación. Ensayar en Heraldo's Lab, sin purgar mensajes reales, una condena de prueba con purga, una sin purga y fallo simulado de edición, comprobando que no desaparecen evidencias ni notificaciones requeridas. `main` intacta.

## Auditoría externa de integración — 2026-10-14

Claude informó 257 pruebas automáticas satisfactorias en `Pruebas`, 29 históricas de `main`, y 51/52 H-03 aplicables en candidato mínimo; **no repetidas por ChatGPT** y **sin pruebas interactivas Discord**. Ver alcance, discrepancia del commit candidato y pendientes exactos en [`audit/AUDITORIA_INTEGRACION_2026-10-14.md`](audit/AUDITORIA_INTEGRACION_2026-10-14.md). La aceptación real de cambios sensibles sigue pendiente. `main` no modificado.

## Preparación sin despliegue y recuperación aplazada — 2026-10-14

El propietario aplaza hasta noviembre de 2026 la verificación independiente de Bitwarden. Existe una nota privada importada con la clave original, pero NO se ha probado su recuperación/descifrado desde una sesión o dispositivo independiente ni la recuperación de acceso a la bóveda. No tocar la clave, no repetir la importación y no ejecutar operaciones productivas que dependan de ese requisito. Esto permite seguir preparando y verificando código con datos sintéticos.

Base de trabajo: Pruebas 13af6c31fc97e8528bf03e571305b9c6b688a539. Main sigue 6f9f9ee0a7ed1c7b7e6c48a13817b9b5f3a5b667. Producción SUCCESS en bbb21914-a87c-44f3-b862-f4ba3ceecd09, sin cambios pendientes. Test SUCCESS, start python bot.py, preDeploy vacío; no se cambiaron sus secretos ni configuración para ejecutar pruebas.

Defecto corregido en backup_job._isolated_restore: SQLite creaba el destino con permisos dependientes de umask (habitualmente 0644). Ahora se reserva con O_EXCL/O_NOFOLLOW y modo 0600 antes de abrir SQLite; no se cambia umask global desde el hilo del bot, ni se sobrescribe un destino existente. Dos regresiones nuevas verifican privacidad con umask 022 y conservación del archivo existente.

Verificación Linux aislada en Railway Test: compilación, pip check, 39 regresiones históricas y 218 de tests/ aprobadas (257). Transporte simulado, sin credenciales en el proceso hijo, sin importar/iniciar el bot para operar Discord. Warnings no fatales preexistentes en mocks. No son pruebas humanas Discord ni prueba productiva.

Siguiente etapa realizada: tools/prepare_h03_candidate.py construye en directorio NUEVO un candidato basado exclusivamente en main fijo, añade cuatro módulos H-03 y cryptography, e inserta un hook protegido por bandera antes de importar dependencias. Una comparación AST comprueba que el resto de bot.py es idéntico. No crea ramas, no publica main ni despliega. La primera ejecución local encontró un error de indentación del comprobador; corregido y candidato válido generado en otro directorio, conservando el anterior.

Candidato ensayado en proceso aislado de Railway Test: 29 regresiones históricas disponibles en main, compilación y dependencias correctas; extracción AST de db_connect/db_init sin ejecutar el módulo del bot, creación de esquema sintético de main, fila sintética, inicialización candidata, backup y restauración nueva y vuelta a inicialización main. Esquema y contenido coinciden; H03_CANDIDATE_PASS. Programador sin bandera no inicia. Ninguna migración nueva se incorpora al candidato. Esto valida compatibilidad sintética del cambio mínimo; NO sustituye instantánea productiva reciente ni aceptación funcional real antes de desplegar.

Pendientes: recuperación independiente en noviembre, alerta con entrega comprobada, auditoría final de candidato/credenciales y nueva instantánea justo antes del futuro despliegue autorizado. El PR 16 no se integró. No hay respaldo diario real de producción activado ni borrado de copias. Revisar CI y autodespliegues del commit de esta etapa antes de atribuirles éxito.

## H-03 — comprobación integral tras integración opt-in (2026-10-14)

**VERIFICADO AUTOMÁTICAMENTE EN RAILWAY TEST:** `python -m unittest discover -s tests -p test_production_backup_scheduler.py -v` → 10/10 OK; `python -m unittest discover -s tests -p 'test_*.py' -v` → 216/216 OK; `python -m unittest -v test_regressions.py test_member_logs.py` → 39/39 OK. Primer intento sin comillas del patrón descubrió erróneamente `test_regressions.py` como directorio, generó `ImportError` y **fue corregido** antes de proclamar éxito. Los registros de Railway acreditan los resultados. Comandos de prueba pre-deploy retirados; sin alteraciones de SQLite real ni Gateway desde H-03.

**PENDIENTE:** no se ha ensayado una copia diaria productiva ni entrega de alertas, no hay pruebas interactivas humanas Discord en esta fase. El monitor de la producción sigue sin canal de notificación confirmado. No se actualizó `main` ni Railway producción.

## H-03: capacidad conservadora de recuperación (2026-10-14)

**VERIFICADO AUTOMÁTICAMENTE EN RAILWAY TEST, SIN DISCORD:** `python -m unittest discover -s tests -p test_backup_job.py -v` → `Ran 10 tests`, `OK`, despliegue `431d16b9-68a4-4b88-af47-9e0bc1fdd771` SUCCESS. Incluye pruebas nuevas de disco sin margen, presupuesto de volumen inválido, volumen con generaciones retenidas y ruta de montaje incompatible; en todos los bloqueos se impide subir y no se crea recibo ni se borra dato. Las seis regresiones originales siguen pasando. Railway Test utiliza cuota explícita de 500 MB en el servicio de cron de laboratorio, no en worker.

**PENDIENTE:** observar un disparo periódico futuro con la nueva cuota. Nunca considerar la ausencia de borrado como política completa de retención. No se modificaron la base productiva ni `main`. Pruebas humanas de Discord: no realizadas.

## H-03: regresión de validación estricta de recibos — 2026-10-14

**VERIFICADO AUTOMÁTICAMENTE, NO EN DISCORD:** `python -m unittest discover -s tests -p test_backup_health.py -v` en Railway Test, `14 tests`, `OK`, despliegue `85eeacfb-63a7-4c56-ad9b-939882446fcd` SUCCESS. Se probó rechazo de recibo sin finalización, con período/entorno/versión ajenos, fechas futuras, orden temporal incorrecto, estado desconocido, nombre de archivo inválido y permisos públicos, además de salud normal, períodos omitidos y antigüedad. Regresiones sin red ni datos de usuarios.

**Cierre técnico:** pre-deploy retirado; Test `worker` Online/SUCCESS y cron Lab `cronReady/SUCCESS`, sin cambios staged. No se realizaron interacciones Discord, pruebas reales de producción, restauraciones productivas ni cambios en `main`. Entrega efectiva de notificaciones de vigilancia: **pendiente**, notificaciones de ChatGPT desactivadas según estado disponible.

## Automatización H-03 verificada en laboratorio — 2026-10-14

Código de ejecución publicado en Pruebas: cf9f2da77406dd79a6abf254fe445e3092a3bb4f, sobre e59bb4f. Main y producción conservan 6f9f9ee0a7ed1c7b7e6c48a13817b9b5f3a5b667. Sin ramas nuevas ni PR; PR #16 no integrado. Checkout anterior divergente preservado.

Servicio independiente heraldo-h03-lab-cron en Railway Test, volumen privado propio de 500 MB, sin DISCORD_TOKEN ni DB_PATH, seis referencias de secretos exclusivamente Lab. Worker conserva python bot.py y preDeploy vacío, SUCCESS y conectado al Gateway. No hubo cambios funcionales en bot.py ni configuración del worker.

**Ejecución programada real:** 2026-10-14 14:15:04–14:15:13 UTC (10:15 local), run 71b4b38d-f85c-4ca2-bb55-fc3a8224955e, despliegue dc2cedd1-e0d7-42f4-bc8d-3012a1dc84a4. VERIFIED_AND_RESTORED a las 14:15:07, H03_HEALTH OK, proceso EXITED. La frontera de activación bloqueó el respaldo durante el despliegue inicial: la primera transferencia completa fue del programador, no manual. SQLite sintética, API backup, AES-256-GCM, subida/descarga autenticadas, SHA-256, integridad/FK y restauración aislada con esquema/recuentos/contenido coincidentes. Supabase pasó de 1 a 2 objetos Lab: solo una generación nueva de 782 bytes cifrados. La generación productiva existente no cambió.

**Persistencia/duplicados:** segunda ejecución manual del cron a las 14:15:44 UTC en contenedor nuevo: ALREADY_ATTEMPTED no_retry=true, H03_HEALTH OK y proceso terminado. Sin nueva subida. No confundir esta segunda invocación manual con el disparo programado anterior. Recibos y generaciones permanecen privados en el volumen.

**Pruebas:** 39 + 195 = 234 regresiones offline en proceso Linux aislado de Railway Test, compilación y pip check aprobados; transporte simulado, sin iniciar Discord. CI del commit cf9f2da: workflows Mensajes y Heraldo Lab aprobados (runs 38577334609 y 38577334553). Prueba negativa real contra Supabase con API key inválida solo en proceso efímero: acceso denegado antes de subida, recibo needs_manual_review, segundo intento bloqueado. Corrupción GCM y clave incorrecta rechazadas con datos sintéticos. Períodos omitidos, fallos, fecha futura y antigüedad desde finished_at cubiertos por regresiones. Logs operativos inspeccionados: solo estados/fechas, sin secretos, filas ni manifiestos. Warnings no fatales preexistentes en mocks SQLite/discord.py; no pruebas humanas Discord.

Horario diario configurado: 06:15 UTC / 02:15 America/Santo_Domingo; se aplica con el despliegue de este commit de cierre y se verifica después. Vigilancia local Codex diaria 08:00, solo Lab, deduplicación por incidencia; depende del equipo/Codex. Vigilancia productiva previa de ChatGPT no modificada. Primer disparo futuro del monitor pendiente: no se afirma entrega de alertas probada.

Producción NO automatizada. Procedimiento, límites y autorización pendiente en AUTOMATIZACION_H03.md. Segunda custodia de clave productiva y ejecutor continuamente disponible siguen pendientes; no se movió la clave. No se borraron respaldos, registros ni datos. Obsidian sin conexión.

## Verificación de entrada cron H-03 — Railway Test, 2026-10-14

**VERIFICADO AUTOMÁTICAMENTE:** `python -m unittest discover -s tests -p test_scheduled_lab_backup.py -v` en pre-deploy temporal del `worker` de Railway Test. Despliegue `7fd7ace1-2fa6-40ff-8548-5517cd199561`, registros: seis pruebas `ok`, `Ran 6 tests in 0.011s`, `OK`. Casos: identidad, token de Discord rechazado, volumen ausente rechazado, SQLite sintética, duplicado no reintentado y error crítico propagado. El archivo `tests/test_scheduled_lab_backup.py` pasó; las ejecuciones remotas de H-03 programadas con acceso Supabase NO se ensayaron en esta fase.

**ESTADO FINAL:** `worker` Test Online/SUCCESS; inicio `python bot.py`, sin pre-deploy, sin recursos/configuraciones en `staged`. Sin pruebas de interacciones reales en Discord y sin escrituras de producción.

## Entrada cron H-03 para Railway Lab — 2026-10-13

**IMPLEMENTADO, PENDIENTE DE PRUEBA AUTOMÁTICA ACTUAL:** `tools/scheduled_lab_backup.py` y `tests/test_scheduled_lab_backup.py` (identidad de servicio de Test, rechazo de credencial de Discord, comprobación de volumen, SQLite sintética, idempotencia y propagación de errores). Workflow de compilación actualizado. Los seis tests de `test_backup_job.py` fueron previamente verificados en Railway Test; los **seis nuevos** de la entrada cron NO deben confundirse con ellos. El entorno de Discord NO se probó.

**Cron no ejecutado:** Railway bloqueó la escritura de la configuración del servicio nuevo; no existe cron activo. Se dejó un borrador STAGED de Test no desplegado, pendiente de descarte manual seguro. No se tocó la producción ni se transfirieron datos reales.

## Regresiones H-03 fase 1 — 2026-10-13

**VERIFICADO AUTOMÁTICAMENTE, SIN DISCORD**: `python -m unittest discover -s tests -p test_backup_job.py -v` ejecutado en pre-deploy efímero de Railway Test: `Ran 6 tests`, `OK`. Casos: recuperación aislada y diario privado, bloqueo de duplicados del mismo día, fallo ambiguo de subida sin reintento, identificación/autorización de producción, rechazo de modo laboratorio en proyecto productivo y segundo intento permitido en día UTC distinto. Transporte remoto simulado; no se leyeron SQLite de Discord. Despliegue `8e87b5b2-64c4-443e-bc38-0a4a67e44dba` finalizó `SUCCESS`, réplica Online 1/1. Pre-deploy de pruebas retirado; `python bot.py` conservado. **CI GitHub Actions específico del HEAD aún por confirmar**, distinto del resultado real Railway. Programador de respaldos de producción: NO activado.

## Actualización H-03 — respaldo externo de producción (2026-10-13)

**REALIZADO SEGÚN INFORME DE CODEX LOCAL:** generada copia consistente SQLite mediante `Connection.backup` sin detener ni modificar el bot de producción. Se cifró externamente con AES-256-GCM usando clave distinta de la empleada en Test, se transfirió a Supabase con la cuenta técnica y se descargó, autenticó y restauró en SQLite aislada. El informe documenta integridad SQLite y claves foráneas correctas, coincidencia de esquema y contenido, prueba de rechazo de manipulación GCM y ausencia de cambios en producción. **Estas verificaciones de contenido/descifrado proceden del informe aportado por el propietario, no han sido repetidas por ChatGPT.**

**VERIFICADO INDEPENDIENTEMENTE POR CHATGPT (consulta 2026-10-13):** en Supabase Storage existe exactamente 1 objeto cifrado bajo la categoría de producción (100609 bytes) y 1 objeto de laboratorio; el bucket sigue privado y las políticas son solo INSERT/SELECT para usuarios authenticated restringidos por identidad. Railway producción sigue Online/SUCCESS con el despliegue anterior; Railway Test también Online/SUCCESS. No se leyó SQLite ni su clave, ni se modificó `main`.

**RIESGO PRIORITARIO:** la clave de descifrado de esta generación se conserva en un único equipo local según el informe. El propietario debe conservar una **segunda copia de la clave** en un medio seguro independiente (p. ej., gestor de contraseñas con recuperación u offline cifrado) y verificar acceso a ella. No publicar clave, rutas privadas, identificadores de generaciones, manifiestos ni datos en repositorio/Discord/chat. No repetir copia ni proceso de subida sin control de idempotencia; no hay aún protección continua.

**PENDIENTE:** periodicidad y supervisión de nuevos respaldos, política de conservación, segundo destino y disponibilidad ante pausas de Supabase Free, ensayos periódicos de restauración y cobertura independiente de adjuntos/evidencias externos de Discord. No implica autorización para desplegar `main`, restaurar producción ni ejecutar escrituras administrativas. Sin pruebas Discord en esta fase.

## Prueba real Supabase H-03 — 2026-10-13 (verificada automáticamente, no en Discord)

Railway **Test** ejecutó `python -m tools.supabase_smoke_test` como pre-deploy en contenedor efímero, aislado del volumen y sin importar `bot.py`. Logs del despliegue `ef2cc191-accd-4b9c-8ab3-4d07acf9fc87`: `H03_SMOKE step=local_backup status=verified`, `encrypted_upload`, `remote_download`, `isolated_restore`, `status=PASS scope=synthetic_no_discord`. Se confirmó en Supabase 1 objeto bajo `lab/`, 766 bytes cifrados. Servicio Test `SUCCESS`, 1/1 réplica Online. El comando pre-deploy se retiró después y el arranque habitual sigue `python bot.py`.

Durante implementación hubo dos builds Test fallidos por resolución de `-r requirements-backup.txt` en Railpack; se corrigió incluyendo `cryptography>=43,<47` directamente en `requirements.txt` de `Pruebas`. La prueba real completa se ejecutó **después** de la corrección. Ni datos reales ni Discord se utilizaron. **No prueba ni protege la base SQLite de producción**. Pruebas de Discord reales: no realizadas en esta fase. Fecha/objetos y logs no deben confundirse con backup real.

## Transporte Supabase (preparación, 2026-10-13)

Añadidas regresiones offline de empaquetado H-03/cifrado AES-GCM/manipulación/identidad/aislamiento por entorno y transferencia simulada. **No ejecutado contra Supabase real; no hay cuenta técnica, clave de cifrado, ni operaciones Discord reales.** Verificar CI del SHA publicado. Railway Test Online tras auto-despliegue, esto no equivale a validación de comandos. Laboratorio para descarga/restauración aún pendiente. `RESPALDOS_SUPABASE.md`.

# Registro de pruebas — El Heraldo Test

**Entorno autorizado:** servidor Heraldo's Lab, bot El Heraldo - Test, rama `Pruebas`.
**Regla:** no probar moderación destructiva sobre usuarios reales ni usar cuentas personales automatizadas.
**Convención:** PENDIENTE / OK / FALLA / BLOQUEADO. Incluir fecha, commit, actor, pasos, resultado y evidencia redactada (sin información privada).

## Registro de ejecución
| Fecha (UTC) | Commit | Prueba | Estado | Observaciones |
|---|---|---|---|---|
| 2026-10-08 | a69f59b | Railway: construcción y arranque | OK | Servicio SUCCESS y Discord Gateway conectado |
| 2026-10-08 | a69f59b | Autoprueba interna `/setup` | OK | Log de inicio de Heraldo's Lab; **no implica prueba interactiva** |
| 2026-10-08 | c1f2e8e | Regresiones offline: confirmación y aislamiento | OK | GitHub Actions `python-checks`; no realizado dentro de Discord |

## Matriz de pruebas interactivas (pendientes)
| Área | Caso a verificar | Estado | Resultado / referencia |
|---|---|---|---|
| /setup | Abrir, navegar, volver y cancelar | PENDIENTE | |
| Mensajes | Crear plantilla; cancelar sin persistencia | PENDIENTE | |
| Mensajes | Guardar plantilla y comprobar persistencia tras reinicio | PENDIENTE | |
| Mensajes | Previsualizar y publicar en canal correcto | PENDIENTE | |
| Mensajes | `/edittemplate`: confirmar edición de mensaje propio | PENDIENTE | |
| Mensajes | `/edittemplate`: rechazar mensaje ajeno o servidor ajeno | PENDIENTE | |
| Mensajes | Botones, selectores, opciones y jerarquía de roles | PENDIENTE | |
| Mensajes | Exportar/importar kit; rechazar conflictos | PENDIENTE | |
| Reaction Roles | Publicar panel, asignar/quitar roles y reiniciar | PENDIENTE | |
| Join Roles | Guardado manual, selección, retrasos y permisos | PENDIENTE | |
| Moderación | Condena manual, duración, tarjeta, DM, roles retirados | PENDIENTE | |
| Moderación | Perdonar, restaurar roles, eliminar castigo | PENDIENTE | |
| Evidencias | Persistir texto/adjuntos cuando desaparece origen | PENDIENTE | |
| Logs y reportes | Coherencia, un solo aviso pertinente, enlaces válidos | PENDIENTE | |
| Seguridad | Restricción por administrador, servidor y permisos | PENDIENTE | |
| Resiliencia | Reinicio de bot y componentes persistentes | PENDIENTE | |

## Modelo de incidencia
### INC-AAAA-MM-DD-001 — [título]
- **Estado:** Abierta / En corrección / Validada.
- **Contexto:** módulo, rama, commit, entorno.
- **Pasos para reproducir:** 1)... 2)... 3)...
- **Esperado:** ...
- **Observado:** ...
- **Impacto:** ...
- **Evidencia segura:** enlace a issue/registro sin datos sensibles.
- **Corrección:** commit ...
- **Reprueba:** fecha, autor, resultado ...

Nunca inventar pruebas ejecutadas. Si una interacción no pudo comprobarse, conservar PENDIENTE.

## Ampliación automatizada del laboratorio (2026-10-09)
- **CI propuesto:** `.github/workflows/heraldo-lab-checks.yml`, ejecutable en PR contra `Pruebas` y manualmente.
- **Casos CI previstos:** `py_compile bot.py`, `py_compile test_regressions.py`, regresiones offline existentes, y `tests/test_*.py` (incluida regresión del selector de logs).
- **Resultados CI:** PENDIENTE hasta recibir resultado de GitHub Actions de este PR.
- **Prueba real en Discord:** NO REALIZADA en esta ampliación. No se simulan clics con cuentas de usuario.
- **Validación posterior al despliegue:** `Heraldo's Lab` → `/setup` → `Mensajes` → `Logs`, abrir categorías y volver; registrar hora, captura saneada y errores.

## Etapa 1 — 2026-10-09 (America/Santo_Domingo)
- CI histórico de `ffefb77`: OK, ejecución https://github.com/ElCreador5/el-heraldo-bot/actions/runs/37889193532, 35 regresiones y 1 prueba del selector. Reemplaza el PENDIENTE de la propuesta original exclusivamente para ese commit.
- Actor: Codex, Windows, Python 3.12.10 y discord.py 2.7.1. Árbol reconciliado a partir de `b8480b8`, `6f9f9ee` y `ffefb77`; registrado en el commit de preparación de esta etapa.
- `python -X utf8 -m pip check`: OK.
- `python -X utf8 -m py_compile bot.py test_regressions.py test_member_logs.py`: OK.
- `python -X utf8 -m unittest -v test_regressions.py`: 35 pruebas OK.
- `python -X utf8 -m unittest -v test_member_logs.py`: 4 pruebas OK.
- `python -X utf8 -m unittest discover -s tests -p 'test_*.py' -v`: 1 prueba OK.
- Los primeros intentos de las suites SQLite quedaron bloqueados por los temporales del sandbox, no por una regresión del bot. La repetición autorizada finalizó correctamente.
- Las suites de raíz se ejecutan en procesos separados para mantener aislados sus módulos, variables y bases SQLite. La matriz Linux 3.11/3.12/3.13 requiere comprobar el nuevo CI.
- Pruebas reales de Discord: NO REALIZADAS. La matriz interactiva anterior sigue pendiente, así como los nuevos fallos identificados en la auditoría.

## Regresiones de seguridad y mensajes — 2026-10-10
- Python 3.12.10 y discord.py 2.7.1. `python -X utf8 -m unittest test_regressions.py test_member_logs.py`: 39 pruebas aprobadas.
- `python -X utf8 -m unittest discover -s tests -p 'test_*.py'`: 25 pruebas aprobadas.
- Cobertura nueva: rol persistido de condena, aislamiento entre servidores, bloqueo condena/perdón, permisos revocados, propuestas y cancelación, conflictos concurrentes, expiración fuera de caché, auditoría tardía o inaccesible, autor de evidencia, política de autoservicio, formatos avanzados, kits y límites tras variables.
- Una invocación inicial añadió erróneamente discover como módulo; ese error de comando se corrigió. No confundirlo con una regresión del bot.
- Discord interactivo: NO realizado. Pendiente comprobar restauración parcial de roles, archivo privado y fallos de adjuntos, pérdida de permisos durante formularios, publicación/edición, reconexión y conservación de estado.
- Railway verificado para la versión anterior del PR #6; las correcciones nuevas aún no están desplegadas en este punto de continuidad.

### Ampliación de comprobaciones — 2026-10-10
- Cola persistente de Join Roles: conservación entre conexiones SQLite, recuperación sin volver a esperar y conservación ante servidor inaccesible.
- Formularios: tiempos no guardados antes de confirmar; permiso revocado impide proponer/guardar demora.
- Suites actuales: 39 raíz + 30 tests = 69 aprobadas. CI del primer lote del PR #7 aprobada (38033889706); ampliación pendiente de publicar. No hay pruebas Discord nuevas.

### Lote ampliado: 78 pruebas offline — 2026-10-10
- 39 regresiones raíz y 39 descubiertas en tests: correctas. Compilación de bot.py, message_payload.py y message_automation.py correcta; pip check correcto.
- Programación: conversión de zona, horas ambiguas/inexistentes, cambio de horario estacional, envío único, permisos revocados, timeout incierto, reinicio y aislamiento por servidor.
- Compatibilidad: las plantillas de texto no se convierten por el hook global; una plantilla de 6000 caracteres no recibe pies que la invaliden.
- Las primeras regresiones de Reaction Roles tras endurecer permisos fallaron por mocks sin permisos/tipo de rol definidos. Los fixtures ahora representan roles ordinarios explícitos; ambas rutas añadir/quitar e inversión volvieron a pasar.
- Recorrido manual pendiente en laboratorio: crear programación futura, cancelar propuesta, confirmar, listar, comprobar destino y variables, retirar una recurrente, reiniciar con un trabajo pendiente y revocar permisos antes del envío. No realizar estos ensayos en producción.
- No se han probado aún Discord Gateway, formularios reales ni reinicios Railway para este lote.

### Automatizaciones: 91 pruebas offline — 2026-10-10
- 39 raíz + 52 tests aprobadas; compilación correcta. Pendiente verificar la nueva CI y despliegue del PR #7.
- Nuevas regresiones: palabras completas y coincidencia literal, variables del usuario que activa la regla, espera entre reinicios, límite común entre reglas, rechazo de bots/webhooks/condenados; sticky con actividad concurrente y rechazo de mensajes ajenos; cancelar webhook sin llamadas, permisos revocados, plantilla modificada, reutilización del propio webhook y exclusión de uno ajeno.
- Ensayos Discord pendientes: mensajes exactos y parciales, adjuntos que provocan sticky, ráfagas de conversación, mensajes del propio bot, reinicio durante espera, pérdida de permisos y publicación confirmada por webhook en canal del laboratorio.
- Ninguna llamada real a Discord ejecutada por estas pruebas. No automatizar cuentas personales para realizar los ensayos.


### Verificación final del lote de editores — 2026-10-10
- Python 3.12.10 / discord.py 2.7.1: 39 pruebas raíz y 67 descubiertas en tests, total 106. Compilación de bot y los cuatro módulos de Mensajes, pip check y git diff --check correctos.
- Cobertura adicional: cambios solo en borrador, conflictos concurrentes, modal obsoleto/cerrado, embed vacío, descripción larga sin truncar, menú independiente y selección múltiple, esquema de acciones, cancelación y propietario, permisos revocados, condena activa, fallo parcial con auditoría persistente y espera entre ejecuciones.
- Honeypot: cancelar conserva valores y no sincroniza; permisos revocados impiden proponer cambios. Condenas: copia de roles disponible antes de una interrupción de la llamada remota.
- Discord real: NO realizado para PR #7. Laboratorio continúa en la versión anterior 34fa94f. Seguir REVISION_PR7.md después de verificar integración y commit del despliegue. Los resultados offline no acreditan funcionamiento de formularios, Gateway o reinicio real.

## Auditoría PR #10 — 2026-10-11

- **Automatización:** GitHub Actions `Heraldo Lab - Python regressions` ejecución `38146125476`, commit `c3896d7`: SUCCESS en Python 3.11, 3.12 y 3.13. Regresiones de configuración/cancelación, logs, moderación y control de evidencias offline. No equivale a prueba real de Discord.
- **Discord:** NO REALIZADAS para PR #10. **Railway de laboratorio:** última versión observada `Pruebas@34fa94f`, anterior a PR #10.
- **PENDIENTE (laboratorio):** para cada comando heredado corregido, confirmar que «Cancelar» no cambia SQLite, que «Guardar cambios» sí lo hace, que otro administrador no puede reutilizar el borrador y que retirar permisos antes de confirmar bloquea la escritura.
- **PENDIENTE (laboratorio):** `/honeypot add/create/remove/exempt_*` ante canal inexistente, bot sin permisos, exenciones concurrentes y avisos fijados.
- **PENDIENTE (laboratorio):** Raid Protection y condena manual; restauración de roles y casos incompletos; evidencia/adjuntos privados y purgas canceladas cuando no hay archivo; DMs, logs y eliminación de duplicados.
- **PENDIENTE (laboratorio):** panel de sugerencias, canales de anuncios, Join Roles, Reaction Roles, reinicio y persistencia de componentes, y regresiones de Mensajes.

## Resultado de integración y caso pendiente de roles — 2026-10-11

- `Pruebas@d190c11a95`: GitHub Actions Python/Mensajes OK; Railway Test despliegue SUCCESS, bot en Discord Gateway y autoprueba /setup OK. Actor: verificación remota de GitHub y Railway; **no se ejecutaron interacciones como un usuario humano**.
- PR #11 `fix/recuperacion-roles-pendientes-20261011`: pruebas SQLite offline para aislamiento por servidor, cancelar, permisos revocados y restauración parcial; ejecutar CI para último SHA del PR.
- Casos interactivos **PENDIENTES** (PR #11, tras integrar al laboratorio): liberar condenado con un rol no asignable, comprobar que se registra como pendiente; reparar jerarquía; ejecutar `/restaurar_roles_pendientes`, cancelar sin modificación y confirmar; comprobar roles restaurados, logs y persistencia tras reinicio; rechazar condena aún activa y permisos perdidos.


## Auditoría de PR #12 — 2026-10-11
- Línea base de a260fec8: 132 pruebas offline aprobadas (39 + 93); CI 38157090799 correcta. Nueva prueba sin sustituir el callback reprodujo TypeError al elegir sección de setup.
- Rama de auditoría: 144 pruebas offline aprobadas (39 + 105), compilación y pip check correctos. Selector real de las siete secciones, etiquetas de cinco acciones, permisos de modal, ledger persistente/aislado, archivo de evidencia privado/incompleto y restauración con defer/error API/permisos revocados cubiertos.
- Railway Test observado en a659b28, despliegue a8314dd2 SUCCESS; solo arranque/Gateway/autoprueba verificados. No se ejecutaron clics, comandos o reacciones humanas ni moderación real durante la auditoría.
- Pruebas manuales mínimas y vacíos por módulo en audit/MATRIZ_COBERTURA.md. El nuevo lote aún no está desplegado.


## Caso observado: dos expulsiones registradas por verificación — 2026-10-11
- Evidencia aportada por el propietario: dos mensajes de expulsión para un miembro, uno del timeout principal y otro del respaldo Sin Verificar. No se copia su identidad al informe. No consta el commit exacto de la captura.
- Reproducción offline antes de corregir: dos llamadas a kick y dos registros; además el respaldo podía saltarse el plazo ampliado o la acción solo registrar/ban.
- tests/test_verification_expiry.py incorpora 11 regresiones: una sanción/registro, concurrencia, aislamiento por servidor, ban, solo registrar, ampliación del plazo, marca reciente, respaldo independiente, miembro verificado y fallos API con pendientes conservados.
- Suite final: 39 raíz/Logs + 116 tests = 155 aprobadas. Compilación e inventario regenerado correctos. Una primera prueba de concurrencia quedó esperando por el defecto reproducido; se detuvo ese proceso de pruebas y se acotó la espera. La repetición tras corrección y la suite completa terminaron correctamente.
- Pendiente laboratorio, después de integrar PR #13: participante voluntario con ambos temporizadores; esperar plazo y comprobar una sola expulsión y un solo registro. Repetir con solo registrar sin expulsión y plazo ampliado. No ejecutar sobre miembros reales sin consentimiento.

## H-01 verificado offline — 2026-10-11
- Base da551f3: 158 pruebas offline aprobadas (119 tests + 39 raíz/Logs), pip check y compilación correctos. Tres guardas AST de Solo reportar pasan.
- Dos regresiones nuevas comprueban la ejecución real sin sanción/purga y normalización heredada. El primer fixture omitía label obligatorio; corregido sin cambiar producción.
- Discord real: no realizado. CI y Railway Test de da551f3 correctos; pendientes recorrido humano y nuevo SHA.

## H-02: barrera de conservación — 2026-10-11
- Purga general, condenas, reportes, Honeypot (incluidos mensajes durante otra sanción) y raid pasan por archivo individual antes del borrado. Baneos usan delete_message_seconds=0; la purga configurada se ejecuta separadamente con archivo.
- evidence_archive.py conserva JSON íntegro y adjuntos en el canal privado de Logs existente; verifica tamaño y SHA-256 leyendo cada copia desde Discord. Ledger SQLite durable y exclusión por mensaje: una interrupción incierta bloquea reenvío/borrado. Condenas conservan el contrato de referencia y texto, sin migrar expedientes previos.
- Si no hay intent de contenido, canal privado, permisos o copia íntegra, no se borra. Archivos superiores al menor límite de Discord/25 MiB, stickers, encuestas y mensajes reenviados quedan conservados en origen. No se crearon almacenamiento ni credenciales.
- Se vuelve a leer el origen para detectar ediciones y comprobar privacidad antes del borrado. Discord no ofrece transacción atómica entre edición, permisos y delete: queda una ventana remota mínima y requiere validación humana. Una copia borrada/corrupta o ledger pendiente exige revisión; no se reintenta un envío incierto automáticamente.
- Pruebas base tras integración: 129 tests y 39 raíz/Logs correctos; añadidas luego tres comprobaciones de roles, excepciones individuales y formatos no soportados. El primer ensayo detectó conexiones SQLite sin cerrar; corregidas con cierre explícito.
- Discord real: no realizado. Pendiente validar CI/Railway del nuevo SHA y copia/recuperación en laboratorio. H-03 y etapas posteriores continúan pendientes.

## H-03 y revisión A–F del lote — 2026-10-12
- Base `Pruebas@9502cea`, rama `codex/h03-recuperacion-20261012`, Codex Cloud Linux, Python 3.12.14 / discord.py 2.7.1.
- `.venv/bin/python -m unittest test_regressions.py test_member_logs.py`: 39 correctas.
- `.venv/bin/python -m unittest discover -s tests -p 'test_*.py'`: 164 correctas; total 203. H-03 aporta 23 tests: WAL confirmado/no confirmado, escritura concurrente atómica, integridad/FK, almacenamiento insuficiente, fallo de fsync/reemplazo, timeout, interrupción de subprocess, reinicio, conservación/rollback, bloqueo entre procesos, esquema, checksums/manifiesto/sidecars, permisos, estados de evidencias/roles y CLI completa. Datos sintéticos temporales.
- Compilación de bot, sqlite_recovery, evidence_archive y módulos de Mensajes: correcta. `pip check` y `git diff --check`: correctos.
- Primer ensayo H-03: un fixture pretendía crear directorio 0755, pero umask lo hizo privado. Se corrigió el fixture con chmod explícito y la repetición pasó; no se relajó la protección.
- Nuevas regresiones: archivado con mutación del objeto original, intent ausente/copia perdida, restauración/confirmación caducadas y selector/edición visual de campos con permisos revocados y límites. Las suites previas de verificación, Solo reportar, Reaction Roles y moderación siguen pasando.
- CI remoto: NO CONSULTADO, API GitHub bloqueada por proxy. Railway: NO CONSULTADO/NO DESPLEGADO. Discord real: NO REALIZADO. No extrapolar el resultado local a estas tres comprobaciones.
- Recorrido humano pendiente: selección de embed/campo, guardar/cancelar, permisos retirados y modal tardío; respaldo/descarga/restauración aislados de Test, reconciliación de operaciones inciertas y comprobación de evidencias remotas. No activar purgas, sanciones ni restauraciones en datos reales por este informe.
