## Interfaz íntegramente en español — 2026-10-24
El propietario exige español para todos los mensajes, botones, editores, menús, registros y textos del bot en ambos entornos. Se traducen etiquetas heredadas de Roles de ingreso y reglas del servidor; se preservan identificadores internos, nombres de comandos establecidos, propiedades y contenido de terceros. Consultar NH UX-03D. La interfaz nativa del cliente Discord se localiza por las preferencias de Discord y no la controla el bot.

## Honeypot Test — «Configurar aviso» abre editor directo y publica desde su confirmación (2026-10-24)
Por instrucción del propietario, `/setup → AutoMod → Honeypot → Configurar aviso` abre directamente el modal completo (`HoneypotWarningEmbedModal`) sin navegar a un nuevo panel ni ofrecer los botones redundantes «Editar texto»/«Editar diseño». El formulario permite título, descripción, color, imagen y pie adicional. La confirmación **existente** se etiqueta «Guardar y publicar aviso», guarda cambios y sincroniza los avisos en canales trampa, incluso cuando no cambió su contenido; la confirmación cancelada no publica. Mantener permisos, idempotencia, aislamiento por servidor, estado anterior y registros; producción no se modifica. El modal nativo de Discord solo tiene su acción de envío, no botones independientes internos.

## Identidad visual fija en El Heraldo Test — 2026-10-24
Se autoriza la aplicación a `Pruebas` de la política obligatoria de footer aprobada para producción, con **única excepción**: el nombre mostrado en cada footer será **El Heraldo's Labs 🧪** y nunca el nombre real del servidor. El icono seguirá usando `{servericon}` (servidor que origina el mensaje, cuando tenga icono). Las notas de pie personalizadas permanecen como detalle, se ofrecen pistas de `{servidor}` y `{servericon}` en los editores, y se respetan los límites de Discord. El valor `{servidor}` en otros campos sigue siendo el nombre real del servidor. No alterar bases, datos, sanciones ni código de `main`. Ver NH UX-03C.

## Honeypot — primera trampa se activa y Retirar abre confirmación directa (2026-10-24)

**Decisión nueva del propietario:** al guardar por primera vez un canal trampa existente o confirmar la primera creación/registro desde `/setup`, Honeypot debe quedar **activado automáticamente**. Elegir en un desplegable no persiste. Una trampa adicional no cambia el estado elegido posteriormente con Activar/Pausar/Reanudar. Se comprobarán las medidas guardadas y permisos de la activación; si no existe medida explícita ni rol de castigo válido, el inicio automático usará **Solo registrar**, sin sanciones, y lo mostrará. Una medida explícita inválida no se activa silenciosamente.

**Aclaración de navegación posterior (prevalece sobre la simplificación anterior):** **Retirar canal** debe abrir directamente la confirmación, sin pasar por Guardar cambios. En esa confirmación sí deben aparecer **Confirmar cambios** (verde) y **Descartar cambios** (rojo), pero no un Volver adicional. Confirmar modifica solo la lista de trampas y, si queda vacía, desactiva la protección; descartar no modifica esa lista. Ambas rutas regresan al mismo panel, preservando cualquier otro borrador. La interfaz no debe generar mensajes suplementarios cuando baste editar la tarjeta existente. Esta decisión no toca `main` y requiere aceptación Discord Test.

## NH — Confirmación intermedia compacta y regreso automático (2026-10-24)

El propietario confirma que **Confirmar cambios** debe actualizar la tarjeta actual y devolver al editor anterior; no necesita **Descartar cambios** ni **Volver** repetidos en la pantalla de confirmación de retirada de Honeypot. Esos botones permanecen en el editor ordinario, al que se vuelve tras confirmar, y **Descartar** solo elimina borradores posteriores, no revierte configuraciones ya guardadas. Mantener las confirmaciones críticas, los permisos y la prevención de doble acción. Esta simplificación de UI no es autorización para suprimir salvaguardas de sanciones u operaciones irreversibles.

## NH — Activar/Pausar/Reanudar son los únicos botones de guardado inmediato (2026-10-24)

**Aclaración explícita del propietario:** Activar, Pausar y Reanudar guardan en cuanto se pulsan, pero **únicamente la función de estado que representan**; no requieren pulsar Guardar cambios, ni ejecutan ni persisten los demás borradores de la pantalla. Selectores, canales, roles, parámetros y textos mantienen Guardar cambios como único punto de escritura. Mantener revalidación de permisos y precondiciones de activación; no encender una protección sin sus canales o medidas **ya guardados**. El cambio y sus errores se muestran en el panel existente, sin nuevos mensajes rutinarios. Esta es la única excepción general admitida al guardado por borrador; las acciones sensibles siguen conservando sus confirmaciones por separado.

En Honeypot la implementación anterior de `HeraldoHoneypotSetupView.toggle` dejaba el estado en `pending_enabled`/`pending_paused`; se modifica para guardar directamente solo esas claves, preservar los demás cambios pendientes y actualizar estado original/snapshot para un guardado posterior. Pruebas automáticas de pausa, reanudación, activación, selección no guardada y sin mensajes extra; Discord Test sigue siendo comprobación separada.

## NH — controles de guardado y mensajes del mismo panel (2026-10-24)

**Decisión general del propietario, no limitada a Honeypot:** todos los editores de `/setup` deben respetar: selectores/desplegables = borrador sin escritura; `Guardar cambios` = aplicar y actualizar el mismo panel; confirmación adicional únicamente cuando una operación sea sensible y estrictamente lo requiera. `Confirmar cambios` tras el borrador aprobado será **verde** y `Descartar cambios` rojo. Evitar enviar confirmaciones, estados y avisos rutinarios como mensajes efímeros adicionales cuando puedan aparecer en la tarjeta existente; dejar avisos separados para excepciones y situaciones realmente importantes. Tras retirar el último canal Honeypot, mostrar **0 canales trampa, ninguno configurado**, y protección desactivada, jamás la lista anterior. El propietario comprobó que los botones de `/setup` habían vuelto a responder bien en El Heraldo Test tras el despliegue `64537919`; no reintroducir sus fallos al normalizar las interfaces.

Esto concreta NH UX-01/02/03/04 para todo el bot y no autoriza cambios de `main` ni confirma todavía los demás flujos de Discord. Especificar cobertura real y pendientes en `PRUEBAS_DISCORD.md`.

## Alcance aclarado por el propietario — todo /setup (2026-10-24)

El retraso y «Interaction failed» afectan todos los módulos y botones de `/setup`; aplicar UX-04 transversalmente, sin limitar el arreglo a Honeypot. Reconocer las interacciones antes de consultas/renderizado/trabajo remoto y preservar la respuesta inicial de botones que abren modales. No ejecutar después de perder el ACK, no encolar clics duplicados ni saltarse permisos/confirmaciones. Un panel caducado permite iniciar una sesión nueva, sin restaurar ni guardar su antiguo borrador. La advertencia de un panel de verificación eliminado debe conservar una acción administrativa clara sin ensuciar cada arranque; no recrear ni publicar automáticamente. Implementación y aceptación se registran en `ESTADO_PROYECTO.md` y `PRUEBAS_DISCORD.md`; esta aclaración no autoriza producción.

## Reconocimiento inmediato de interacciones — Honeypot (2026-10-24)

**Incidencia descrita por el propietario en Discord Test:** al pulsar botones, especialmente Honeypot, Discord muestra «Interaction failed», y el bot ejecuta la acción después. Se tratará como defecto de la confirmación temprana, no como fallo visual menor. Los callbacks que inspeccionan SQLite, preparan embeds o ejecutan operaciones de canales deben acusar recibo al principio y editar el mensaje ya reconocido o enviar una respuesta efímera posterior. Conservar verificación de permisos, un único Guardar, cancelación sin escrituras, bloqueo de doble confirmación y mensajes claros de error. No convertir esto en una autorización para eliminar controles de seguridad ni generar sanciones en producción.

## NH — nombre automático del servidor en todos los embeds (2026-10-24)

**Alcance solicitado por el propietario:** no limitarlo al DM ni a Personalidad. Todos los módulos deben mostrar el nombre del servidor emisor en el pie del embed. El pie global se aplica también a embeds con pie funcional ya existente: si el nombre del servidor ya aparece no se repite; si falta se antepone, conservando la información útil y el icono propio. Se sustituyen tres pies fijos de módulos de plantilla/perfil/Miembro de la Semana. Las plantillas enriquecidas de Mensajes se identifican **antes de enviarse**, conservan su contenido original y se revalidan ante el límite total Discord de 6000 caracteres; si la plantilla está al máximo, se rechaza con error validado antes de enviar, sin truncar el mensaje en silencio. Nunca se fuerza un nombre de servidor arbitrario a un DM sin contexto de guild verificable. No se borran configuraciones históricas ni datos.

**Desarrollo:** solamente `Pruebas`; `main` requiere integración selectiva y aceptación Discord autorizada conforme al encargo #23. No presentar CI o Gateway como clics verificados.

## Pie de los embeds: identidad automática del servidor — 2026-10-24

**Decisión del propietario (prueba interactiva):** el pie de marca debe reflejar automáticamente el nombre del servidor donde funciona El Heraldo, sin pedir al administrador el texto manualmente. En la edición de DM de verificación y tarjeta de personalidad se elimina el campo de pie, y se resuelve la identidad del servidor al construir cada tarjeta (y su icono cuando corresponda). La plantilla configurable del icono del DM se conserva: el valor predeterminado nuevo es `{servericon}`. Los pies que contienen información funcional (estado, motivo, paginación) conservan dicha información. No sobrescribir ni borrar valores históricos de configuración SQLite solo por esta normalización.

**Alcance inicial autorizado en `Pruebas`:** DM de verificación, editor de personalidad, y comando legado `/verify_dm_texts`. El pie global de embeds sin pie propio ya usa `{servidor}` / `{servericon}`. Otros pies de plantillas específicas requieren auditoría antes de imponer cambios globales que podrían borrar información útil.

## Formato de la verificación de edad — mención sin ID repetido (2026-10-24)

**Aclaración posterior del propietario, prevalece para esta tarjeta:** el registro «Verificación de edad completada» debe mostrar la mención nativa del miembro como @apodo, seguida de «se verificó correctamente.», sin paréntesis ni ID numérico adicional. El identificador subyacente de la mención permanece para que Discord identifique al miembro; no se imprime de nuevo. Esto sustituye el formato de apodo en texto plano de la decisión anterior solo para esta tarjeta. Mantener IDs explícitos cuando son necesarios en expedientes, reportes, condenas y evidencias. La resolución de la mención en cada cliente depende de Discord; no prometer siempre el apodo si falta caché.

## Identificadores en registros de usuarios (2026-10-24)

**Decisión del propietario:** mostrar preferentemente el apodo visible del miembro en el servidor (y, si no existe, su nombre de usuario). Omitir IDs numéricos y menciones innecesarias en mensajes rutinarios, como «Verificación de edad completada». **Mantener el ID cuando facilite identificación inequívoca, investigación o trazabilidad**, particularmente en expedientes, reportes y evidencias administrativas; no eliminar sus claves internas ni referencias persistidas. Escapar nombres suministrados por usuarios para impedir formato o menciones accidentales. La aplicación global a otros registros queda pendiente de revisión específica, sin rediseños masivos.

## Modo Custodio — reportes privados, evidencias mínimas y ámbitos SFW/NSFW (2026-10-23 RD)

**Decisión nueva del propietario:** Modo Custodio dispondrá de canal propio `reportes📢` para observaciones y evidencias con NH. Distinguir servidores y canales SFW/NSFW, siempre sujetos a sus Server Rules particulares. Considerar debates públicos de Reddit, X e Instagram como referencias de contexto y políticas, no como nuevas reglas de los servidores. No habilitar sanciones ni cambiar las preferencias elegidas (`observe`, `balanced`, `eligible`, avisos de cambios desactivados).

**Privacidad y consentimiento:** creación de `reportes📢` solo después de botón Confirmar creación y revalidación de permisos; `@everyone` sin acceso, roles administrativos/moderadores autorizados y bot. Cerrar ante canal eliminado, público o con permisos directos indebidos, sin reparaciones silenciosas. Las tarjetas inicialmente guardan solo referencia original, número de regla, estado, fecha, huella opcional y revisión de normas; no transcripciones ni imágenes. En esta etapa NO hay motor que capture observaciones, ni archivo probatorio duradero. La retención de contenido, cuando se diseñe, requiere controles de privacidad, consentimiento, alcance, almacenamiento y respaldo. No utilizar material sensible de canales restringidos en registros ni entrenar con él.

**Distinción SFW/NSFW:** determinar con guild.nsfw_level y channel.nsfw; los valores no son permiso para ignorar las normas del servidor. Cualquier tipo desconocido se conserva desconocido. Exigir reglamento aprobado por servidor antes de evaluar. Nada de reglas universales inventadas.

**Fuentes externas:** Reddit (https://redditinc.com/policies/data-api-terms) y X (https://x.com/en/tos) restringen uso para entrenamiento y recolección automatizada; Meta/Instagram exige autorizaciones específicas (https://www.facebook.com/legal/automated_data_collection_terms). Se registran fuentes como referencia general sin extraer comentarios ni entrenar modelos. Obtener permisos/licencias antes de cualquier ingestión.

## Modo Custodio — preferencias aprobadas y corpus de referencia (2026-10-23 RD)

**DECISIÓN:** modo `observe` (Observar), sensibilidad `balanced` (Equilibrada), alcance `eligible` (canales elegibles/autorizados), avisos de cambios de normas desactivados. No autorizar sanciones automáticas, IA externa ni supervisión de mensajes hasta su implementación y aceptación. La pantalla de /setup ofrece solo opciones realmente seguras; Guardar prepara valores mediante confirmación administrativa, Cancelar/Descartar no escribe. Defaults no son prueba de que un servidor haya guardado su configuración.

**Investigación pública para futura inteligencia contextual:** usar como referencias etiquetadas Civil Comments (CC0, https://www.tensorflow.org/datasets/catalog/civil_comments), Wikipedia Talk Labels: Toxicity (CC0, https://figshare.com/articles/dataset/Wikipedia_Talk_Labels_Toxicity/4563973) y Multilingual HateCheck en español (CC BY 4.0, https://huggingface.co/datasets/Paul/hatecheck-spanish). Primero análisis de licencias, sesgos y datos personales; después evaluación fuera de línea. No volcar comentarios de foros sin permiso ni entrenamiento autónomo con mensajes de Discord. Las reglas oficiales de cada servidor son la autoridad; internet solo aporta casos, no nuevas prohibiciones.

## Modo Custodio — diseño y límites (2026-10-23)

**Acordado por el propietario:** nombre Modo Custodio; debe leer automáticamente las Server Rules oficiales del servidor y exigir que estén activadas, sin obligar a reescribir el reglamento en /setup. La lectura real de laboratorio recuperó 12 reglas mediante la API de Member Verification, que no tiene contrato público estable.

**Propuesta técnica, NO autorización de sanciones:** ubicación /setup → AutoMod → Modo Custodio; mostrar versión, número, interpretación, alcance y borrador de acciones; aprobación administrativa explícita antes de supervisión. Modos posibles: Observar, Asistir y, solo después de nuevas pruebas y autorización, Automático controlado. No enviar mensajes a un proveedor de IA sin decidir privacidad y acceso. Ante cambios de reglas, API caída, permisos insuficientes o ambigüedad, nunca inventar normas ni sanciones; suspender acciones o derivar a revisión. Evitar DMs ajenos, canales no autorizados, logs duplicados y retención excesiva.

**Implementación inicial:** módulos aislados y lector asíncrono, sin bot ni /setup operativos. Clasificación real y política final de respuestas siguen pendientes de autorización y pruebas.

## Publicación selectiva NH UX-03B a main — 2026-10-21

**GitHub main ACTUALIZADO:** commit `2b6aeeb0fe1cc60154ac3ab179c3bec9463d9287`, base anterior `317ed8668b659af9f9945d1cb36027c7aca008b9`. Solo `bot.py` (botones y navegación /setup), `AGENTS.md` (UX-03B), `tests/test_ux_main_release.py`, y `.github/workflows/member-logs-checks.yml` (contrato UX en CI); sin fusionar toda Pruebas, sin cambios de esquema ni operaciones deliberadas sobre SQLite. Se normalizaron cuatro retornos Join Roles, tres etiquetas «Volver a /setup», rutas de Honeypot/Raid a AutoMod, Edad/Personalidad a Verificación y tres controles finales del editor de Roles del sistema.
**Verificación AUTOMÁTICA:** port aislado del código real de main, `Heraldo Lab - Python regressions` ejecución `39612383661` SUCCESS en 3.11, 3.12, 3.13 y UX-contract; CI de main ejecución `39612776885` SUCCESS.
**RAILWAY PRODUCCIÓN NO ACTUALIZADA EN RUNTIME:** servicio oficial sigue en despliegue `08846736-4ce5-47f2-bd70-7a50ab4cefce` SUCCESS del commit `317ed866`. La fuente del servicio fue fijada a `main@2b6aeeb0` mediante una modificación preparada de un único campo, no destructiva, aceptada en entorno `El Paraíso`, pero NO nació despliegue nuevo. Al intentar iniciar una compilación directa Railway rechazó: `Deploys have been paused temporarily`. El código nuevo NO está confirmado en el bot oficial. No usar «redeploy» de la compilación antigua para afirmar que se ha actualizado. Al reanudarse despliegues, reconstruir el commit fijado y verificar logs, SHA, estado de botones y navegación en Discord.
**Datos:** volumen productivo `heraldo-data` montado en `/data`, sin cambios de configuración; no se ha verificado una copia reciente de la SQLite real ni una restauración. La reversión de código referencia al commit y build anterior, no constituye respaldo de los datos. **DISCORD:** no se realizaron pruebas interactivas oficiales. **Obsidian externo:** no conectado.
**Alcance:** la integración presente cubre UX-03B y no significa integración total del módulo de Verificación de Pruebas ni de otros cambios divergentes. Candidato transitorio de 906 KB en Pruebas eliminado tras pasar las pruebas; contrato de regresión permanente queda en main.

## NH — Botones proporcionados y navegación «Volver» en todos los módulos (2026-10-21)

Decisión del propietario: aplicar **UX-03B**, añadida a `AGENTS.md`, a todos los módulos de `/setup` y editores administrativos pertinentes, respetando etiquetas aprobadas salvo que el regreso se denominará únicamente **Volver**. Las filas deberán agruparse y equilibrarse sin inventar una capacidad de ancho fijo que Discord no ofrece; `Volver` regresará al nivel inmediatamente anterior. La decisión es transversal y obliga a futuras incorporaciones. Implementación y pruebas escalonadas únicamente en `Pruebas`; `main` se conserva sin modificar por esta petición.

## NH — Puerta de seguridad para publicación selectiva de Verificación (2026-10-21)

El propietario autorizó actualizar selectivamente `main` con el módulo de Verificación, pero la auditoría NH detectó elusión de edad por roles de personalidad y riesgo de roles públicos con permisos peligrosos. **Candidato preparado solo para `Pruebas`:** el procesamiento de reacciones exige verificación previa de edad cuando está activa (salvo exentos), rechaza condenados y roles de autoservicio peligrosos; la elección de roles y sincronización vuelven a validar privilegios; retirar una reacción no sortea «Cambiar elección: No»; el plazo de edad ya no acepta personalidad como verificación. Prueba de contrato en `tests/test_personality_safety_release.py`. **No representa aprobación de publicación:** siguen pendientes robustecer guardados de Edad/Personalidad, resultado y reintentos de KICK por personalidad, confirmaciones de publicación, pruebas de regresión del candidato, ensayos interactivos y comparación selectiva con `main`. No migrar SQLite ni copiar toda `Pruebas`. **Estado:** candidato sin CI / Discord hasta verificar el SHA; `main` y Railway producción no modificados por esta etapa. Obsidian externo no conectado.

## NH — Único plazo para la verificación de edad (2026-10-20, decisión posterior)

**DECISIÓN DEL PROPIETARIO:** por ahora se conserva únicamente el plazo principal de edad (verify_timeout). «Sin Verificar» sigue siendo un rol, pero NO inicia ni recupera un segundo reloj ni puede expulsar por sí mismo. Se retira el campo «Respaldo Sin Verificar» del formulario y de los resúmenes; el plazo de personalidad permanece independiente y sin cambios. Los datos históricos (sin_verificado_at y sin_verificado_timeout_seconds) y el esquema SQLite se conservan para evitar destrucción o migración. Al restaurar Sin Verificar tras levantar una condena, únicamente se programa un plazo principal NUEVO cuando la edad está activada y el miembro no está verificado ni exento. La acción al vencer sigue respetando Expulsar, Banear o Solo registrar, permisos, rol y jerarquía. La confirmación Guardar cambios sigue siendo obligatoria; Cancelar no persiste. Esta decisión prevalece sobre las descripciones históricas del editor con respaldo que siguen abajo. **Código:** solo rama Pruebas; **PRUEBAS AUTOMÁTICAS/CI:** pendientes de ejecutar para este cambio; **DISCORD:** pendiente de verificación real; **main:** sin modificar; **Obsidian externo:** no conectado.

## NH — Plazos de edad y personalidad en los mismos sitios (2026-10-20)

Ambas verificaciones usan el **mismo editor** de plazos desde `/setup → Verificación → Tiempos`, `Verificación de edad → Configurar tiempos` y `Verificación de personalidad → Configurar tiempos`. Se presentan los plazos vigentes de edad (`verify_timeout`), personalidad (`orientation_timeout_seconds`) y respaldo Sin Verificar (`sin_verificado_timeout_seconds`) sin alterar los datos. El formulario permite cambiar minutos y exige **Guardar cambios** en la confirmación; al abrirlo o salir sin cambios no escribe y al editar un único campo conserva los otros segundos originales sin redondeo destructivo. Los editores individuales rechazan abrir Tiempos si tienen otros borradores pendientes, para evitar pérdidas de cambios. PENDIENTE: CI actual y prueba interactiva en Discord Test. `main` no modificada.

## NH — Texto explicativo y distribución de personalidad (2026-10-20)

Decisión: los roles expresan cómo desea participar un miembro, que obtiene una elección mediante la reacción con el emoji del rol y puede cambiarla solo si se permiten cambios; permisos pueden desbloquear canales y la elección no verifica identidad/edad. Si la función está activada y es obligatoria, una falta al vencer el plazo genera expulsión automática con intento de DM previo e invitación de un solo uso para dar oportunidad de reingreso. No afecta la regla sin invitaciones para baneos o expulsiones manuales. En el panel: fila superior Volver/Activar/Desactivar/Editar embed; siguiente Cambiar elección/Expulsar si no elige/Editar DM; última Guardar/Descartar, sin eliminar borradores ni confirmaciones NH. Verificaciones Discord aún pendientes.

## Encuestas voluntarias de salida — 2026-10-20

**IMPLEMENTADO en `Pruebas`, sujeto a CI y Discord:** configuración separada y desactivada por defecto desde `/setup → Mensajes → Logs → Eventos de miembros → Comentarios de salida`, con Guardar/Descartar (NH); solo se solicita DM cuando la auditoría fue consultada satisfactoriamente sin encontrar un kick/ban, existe la tarjeta original y el canal de logs está restringido al personal moderador. Los errores o permisos insuficientes de auditoría cancelan la encuesta. El botón persistente de DM abre un modal voluntario (máximo 500 caracteres, siete días); SQLite asocia la solicitud por servidor, miembro, DM y tarjeta, evita duplicados y conserva respuestas pendientes de editar tras reinicios. `exit_comment_apply` edita la tarjeta, no crea registros secundarios; sin respuesta no muestra el campo «Comentario». El usuario solo puede responder a su propio DM. Las solicitudes pendientes sin respuesta se purgan después del periodo de retención. No se altera el motor de sanciones ni `main`.

**Verificación real en Discord:** NO realizada. La aplicación de respuesta depende de permisos en el canal y puede quedar pendiente si este se elimina o vuelve público. El registro en SQLite se debe respaldar antes de aplicar a producción.

## NH — Excepción de DM previo y aislamiento de Test (2026-10-20)

Para la expulsión automática por no definir personalidad se envía aviso **previo**, expresado como medida prevista, con invitación individual y datos reales del servidor y tarjeta. Nunca afirmar resultado antes de confirmación. En baneos y expulsiones manuales, ni Test ni oficial deben generar enlaces de reingreso. Test debe notificar sus medidas experimentales que afectan la participación, incluidos motivo, embeds y DM, sin afirmar éxito antes de Discord; se permite enlace solo en recuperación de personalidad. Los mensajes de la plantilla oficial nunca muestran disculpas experimentales.

## NH — Alcance de exenciones de verificación (2026-10-20)

El propietario exime de verificación obligatoria a dueño, administradores y moderadores con permisos reales de Discord. Las exenciones afectan exclusivamente a verificación, orientación/personalidad y consecuencias de no completar el proceso: no eximen de otras sanciones. Al perder permisos, conceder un plazo completo y nuevo, sin recuperar plazos anteriores ni alterar roles ajenos. Mantener las comprobaciones antes de sancionar y después de reinicios.

## Raid Protection — guardado directo como confirmación (2026-10-20)

El propietario requiere que pulsar «Guardar cambios» sea suficiente: eliminar la confirmación posterior y actualizar inmediatamente el mismo panel con los valores guardados, sin conservar indicadores «pendiente». La pulsación de Guardar constituye la confirmación administrativa explícita; permanecerán las validaciones de permisos, conflicto concurrente, integridad SQLite, Cancelar/Descartar sin guardar y conservación del motor antiraid. Aplicado selectivamente en `main@317ed866`.

## Normas Heraldo — proceso simplificado para `main` (2026-10-20)

El propietario eliminó los bloqueos administrativos que retrasaban la publicación: GitHub confirmó que «Protección de main.» conserva únicamente `deletion` y `non_fast_forward`. No se exige PR, revisión externa ni checks de estado requeridos. Una autorización expresa de producción permite actualizar `main` directamente sin pedirla otra vez por el mismo cambio. El desarrollo habitual sigue en `Pruebas` salvo decisión específica; no arrastrar funciones ajenas al parche. Se mantienen pruebas automáticas no bloqueantes, compilación, revisión de SHA/concurrencia, registro de resultado y protección proporcional para SQLite, respaldos recuperables y acciones sensibles H-03. Actualizar el código de producción puede disparar Railway automáticamente.

El 20/10/2026 se publicó en `main` la corrección aislada de logs de KICK de verificación, commit `647b9f545a9a1d974726915cfcc33d8372a122c9`, sin migrar SQLite y preservando la tarjeta única «Miembro expulsado». Las verificaciones finales y la interacción de Discord requieren consulta separada: no declarar probadas sin evidencia.

## DM condicionado a expulsión confirmada — 2026-10-19

Decisión del propietario: **si Discord no completó la expulsión, no enviar DM de expulsión, ni crear una invitación de recuperación**. El orden anterior (notificar primero) queda expresamente reemplazado. Mantener el aviso necesario tras la sanción confirmada (incluidos avisos de laboratorio), sin prometer entrega si Discord ya no permite el DM. Excluir al dueño del servidor de la verificación por plazos y sus reintentos. Inicialmente implementar y probar en `Pruebas`; no desplegar `main` al establecer esta decisión.

## Raid Protection — perfiles solo como borrador (2026-10-19)

El propietario aprueba modernizar el formulario Detección con cinco selectores, valores personalizados y perfiles Moderada, Equilibrada y Estricta. No se cambia la lógica de raid ni las sanciones, ni se activan perfiles al seleccionarlos; para persistir se exige Guardar y confirmación final. Evaluaciones sintéticas no prueban tasas reales de eficacia.

## Ayuda contextual en desplegables para administradores — 2026-10-19

El propietario establece que **todos los selectores y desplegables de configuración deberán orientar a quien no conoce el bot**, de forma discreta y sin competir con estados, avisos de seguridad ni confirmaciones importantes. La norma detallada y vinculante es `AGENTS.md` §UX-03A: orientación en el control, usando `placeholder` y descripciones de opciones cuando Discord las permita; en selectores nativos de roles/canales, ayuda en el propio `placeholder`. Se prohíben mensajes de ayuda repetitivos o adicionales. Aplica a menús actuales y futuros durante sus revisiones, sin alterar el guardado explícito. Esta decisión **autoriza establecer la regla**, no certifica que todos los selectores existentes ya la implementen. Solo `Pruebas`; sin cambios a `main` ni a sanciones.

## Contrato transversal obligatorio de interfaz y aceptación — 2026-10-19

El propietario autoriza convertir sus decisiones repetidas sobre botones, menús, borradores, colores, confirmaciones, legibilidad, permisos, persistencia y regresiones en una norma exigible por todos los agentes. La definición normativa reside en `AGENTS.md` (UX-01 a UX-05), sin duplicar su texto. Los módulos existentes se revisarán progresivamente sin reescribir funciones estables ni asumir que un test sintáctico acredita su comportamiento real. **Pruebas** únicamente; no modificar `main` ni producción. Las comprobaciones automáticas se incorporan a la suite existente de GitHub Actions. Sin tests requeridos en protección de rama, una ejecución CI no impide técnicamente pushes directos. Discord Test requiere verificación independiente.

## H-03 — Autorización explícita para adelantar la recuperación productiva (2026-10-18)

**DECISIÓN VIGENTE DEL PROPIETARIO:** se revoca el aplazamiento hasta noviembre de 2026 **únicamente para realizar desde ahora la verificación independiente de la clave original y los ensayos de recuperación productiva**. Esta decisión corrige la referencia histórica al aplazamiento del 17/10 y la reiteración en la autorización de Test del 18/10. No equivale a declarar recuperada la clave, validar la copia remota ni autorizar un despliegue.

**ALCANCE AUTORIZADO:** consultar configuración y metadatos de GitHub/Railway/Supabase, recuperar y probar la clave desde su custodia privada mediante un procedimiento aislado autorizado, comprobar que la copia productiva existente se descarga, descifra, autentica y restaura en una SQLite **distinta** de la activa; verificar integridad, esquema y claves foráneas; preparar y probar el controlador de despliegue en `Pruebas` y elaborar preflight de producción. No publicar claves, tokens, contenido, datos de expedientes, identificadores privados ni objetos de Storage. No copiar la clave original a GitHub, chats, logs o entornos de prueba. Si no hay acceso a la custodia, registrar PENDIENTE sin fingir verificación.

**PROHIBICIONES QUE NO CAMBIAN:** no modificar `main`, desplegar/reiniciar el servicio de producción, alterar la SQLite viva o sus respaldos, activar el programador productivo, incorporar credenciales H-03 al servicio oficial, modificar `sleepApplication` productivo ni fusionar PR #18 mientras falten las verificaciones exigidas en el bloqueo del 17/10 y no exista autorización expresa adicional para esas acciones.

**GATES:** 1) clave original recuperable de manera independiente y descifrado/restauración aislados; 2) copia productiva **nueva** y restauración independiente validada; 3) revisión obligatoria y controlador H-03 no eludible por Railway/GitHub, pruebas y recuperación/rollback; 4) autorización específica del propietario para tocar producción. Eliminar una espera de calendario NO elimina ninguna puerta técnica.

## Autorización vigente de Test real — 2026-10-18

El propietario autoriza implementación directa en Pruebas, sin ramas ni PR nuevas,
configuración del worker Test y recorrido completo con su SQLite real: instantánea
online consistente, cifrado, almacenamiento aislado, descarga y recuperación
obligatoriamente separada de DB_PATH. Se conservan todas las generaciones. Esta
petición sustituye las restricciones históricas a datos exclusivamente sintéticos
en Test; no autoriza restaurar la SQLite activa ni activar producción. Para dar
continuidad al scheduler se prepara desactivar sleepApplication SOLO en Test;
el bloqueo productivo sigue vigente. El aplazamiento histórico de la comprobación de la clave se revocó mediante la autorización posterior del 18/10/2026.

## Bloqueo explícito: activación H-03 productiva y actualización de `main` — 2026-10-17

Decisión autorizada por el propietario tras auditoría de Claude (ver audit/H03_PRODUCCION_2026-10-17.md y PR #18).
Mientras no se cumplan las tres condiciones siguientes, no se fusiona PR #18 ni ningún cambio
relacionado con H-03/respaldo productivo a `main`, no se activa el horario productivo 06:15 UTC,
no se añaden las variables Supabase/clave H-03 al servicio de Railway producción, y no se
desactiva sleepApplication:

1. Recuperación independiente de la clave verificada de hecho (autorizada desde el
   18/10/2026, pero PENDIENTE hasta comprobar descifrado/restauración real aislada).
2. `main` exige revisión aprobatoria (required_approving_review_count ≥ 1) y, cuando exista,
   el check H-03 del controlador de respaldo previo, antes de admitir merge.
3. Generación productiva nueva y verificada (descarga + descifrado + restauración real,
   no solo metadatos de Storage) antes de cualquier despliegue a `main` dependiente de H-03.

Reemplaza cualquier lectura de "Aplicación H-03 — 2026-10-12" o "Almacenamiento externo de
respaldos — 2026-10-13" como autorización suficiente para activar producción.

## Logs de miembros: patrón visual de Sapphire sin enlaces ficticios — 2026-10-17

Se aprueba una tarjeta coherente en español para salida, expulsión y baneo (temporal o permanente), con título de evento, cuerpo en líneas de cita, avatar a la derecha y fecha del mensaje. Mostrar usuario, ID, fecha relativa de ingreso, roles y cantidad de miembros; agregar motivo y moderador para sanciones si proceden. Mostrar duración y vencimiento para baneo cuando el expediente reciente concuerde con motivo y fecha, sin presentar los baneos externos sin duración acreditada como permanentes. Omitir enlaces Warned/Muted/Kicked/Banned cuando no existe un registro real y verificable. Mantener las plantillas configurables, los canales de logs por evento y la deduplicación de la tarjeta de orientación; esa tarjeta conserva DM y número de oportunidad. Solo rama `Pruebas`, sin intervención en producción.

## Conciliación de verificación: recibos persistentes y aislamiento de laboratorio — 2026-10-17

Un mismo estado de revisión sin seguimiento no debe generar múltiples avisos por reinicios de Railway. Guardar únicamente una huella no reversible SHA-256 por guild en `meta` de SQLite después de entrega confirmada, sin actualizar los borradores administrativos. Publicar nuevamente cuando cambia el conjunto de miembros afectados, existen nuevos plazos recién iniciados o reaparece un problema previamente resuelto. Si Discord no entrega el embed, no almacenar un recibo falso. El bot Test no puede iniciar nuevos plazos de conciliación en un servidor distinto de `HERALDO_TEST_LAB_GUILD_ID`; ello no modifica otros flujos de verificación manuales o de ingreso. Los casos antiguos siguen pendientes de revisión y no se expulsan retroactivamente. No intervenir producción.

## Verificación: evitar expulsiones retroactivas por estado huérfano — 2026-10-17

Para miembros con rol Sin Verificar sin temporizador SQLite (p. ej., después de desconexión), no inferir que `joined_at` indica cuándo se asignó el rol. Se permite reiniciar un plazo completo solo en ingresos recientes (máximo 15 minutos, 25 por ronda) que cumplan las comprobaciones de roles, verificación activa, condena y estados actuales. Los antiguos o contradictorios requieren revisión administrativa; la auditoría no expulsa ni modifica roles. Conservar los plazos efectivos y acciones configuradas, incluidos Solo registrar, permisos y protección de duplicados. Producción se trata por separado y requiere respaldo reciente recuperable antes de cambiar Serverless o desplegar `main`.

## UX de confirmación secundaria — Honeypot — 2026-10-17

Decisión del propietario: cuando `Publicar aviso` abra una confirmación secundaria, Confirmar debe ejecutar la acción validada, actualizar el embed de la pantalla original y retirar el mensaje efímero; Cancelar lo retira sin guardar. La interacción se reconoce inmediatamente para evitar timeout. Frente a permisos revocados, concurrencia, cambios obsoletos, fallos parciales o errores de Discord nunca informar un éxito no comprobado. Se aplica en esta etapa a la publicación de avisos de Honeypot, conservando el flujo de guardado explícito y evitando cambios extensivos al resto de `/setup`.

## Honeypot: excepción exclusiva de evidencias — 2026-10-17

**Decisión definitiva del propietario (prevalece sobre dudas históricas):** ninguna acción causada por Honeypot archiva mensajes, adjuntos o pruebas del incidente, incluso si la acción es condenar. La eliminación del disparador y las purgas Kick/Timeout/Condena usarán una ruta especial con verificación de autor, servidor, permisos y periodo. Solo la persona que escribió en la trampa puede ser objeto de la purga; expulsión: al menos últimas 24 horas, ampliables desde /setup. Los demás módulos conservan el archivo verificable previo al borrado, los expedientes y sus garantías. Mantener registros administrativos de Honeypot sin contenido original; no borrar archivos previos. La protección antifallos por miembros antiguos, exenciones y permisos sigue activa para evitar falsos positivos.

## Honeypot: publicación explícita de avisos y protección de evidencias — 2026-10-17

El propietario solicita que `/setup` concentre los ajustes y disponga de **Publicar aviso**. Se confirma la solución con acción visible en `Configurar aviso`, edición y fijado idempotente en todos los canales trampa registrados y confirmación explícita antes de ejecutar. Crear aviso activa la opción de publicación si estaba desactivada; Cancelar no modifica nada. El aviso usa configuración guardada y la confirmación se rechaza si el panel tiene cambios pendientes, faltan permisos/canales o la plantilla se ha vuelto obsoleta.

El propietario también pide no retener evidencias fuera de Honeypot. **Decisión de alcance pendiente:** no se interpreta esta frase como autorización para desactivar el archivo de evidencias obligatorio antes de eliminar mensajes en sistemas ajenos o comprometer expedientes existentes. Antes de modificar el motor compartido, distinguir evidencias del disparador Honeypot, mensajes del resto de un período de purga y evidencias de otras sanciones. Mantener privacidad y conservación de expedientes sin eliminar mensajes sin archivo verificable.

## Honeypot: expulsión con purga mínima de 24 horas y configuración visual — 2026-10-17

El propietario decide que Expulsar debe incorporar al menos **1 día de purga de mensajes del miembro**, configurable desde `/setup`, y que los ajustes cotidianos del módulo deben poder hacerse con menús en lugar de exigir comandos slash. Se adopta valor predeterminado de 1440 minutos, incrementable a 2/3/7/14/30 días; menos de un día o configuraciones inválidas no reducen el mínimo. Solo mensajes del usuario; no es una purga global de todos los miembros. La expulsión se ejecuta una vez por la función compartida; la purga empieza después de que Discord confirme y se archiva evidencia de forma privada y comprobada para cada mensaje antes de borrar. Un fallo de archivo o permisos impide borrar ese mensaje y queda reflejado en el resultado. Se conserva el aviso de Test y el expediente de expulsión. No activar cambio alguno en `main` ni afectar el sistema antifallos. En `/setup`, parámetros de acción son borrador hasta Guardar; Volver y Descartar no persisten.

## Honeypot: expulsión y baneo como acciones explícitas — 2026-10-17

Por indicación del propietario se añaden **Expulsar** y **Banear** al menú de acciones, con aplicación real mediante las rutas de moderación ya existentes, expediente automático y protección de permisos/jerarquía. Cambiar el menú es un borrador; se requiere Guardar cambios, sin persistencia por selección ni Descartar/Volver. Se preserva la compatibilidad de las configuraciones históricas almacenadas como `kick` o `ban`, que hasta ahora significaban `role`. Los nuevos valores `kick_enabled`/`ban_enabled` se crean únicamente con confirmación explícita, nunca por migración silenciosa. El baneo aplica la duración predeterminada de Moderation para ese servidor (en Test 5 min si no se configuró otra; en producción permanente si no se configuró otra). No usar la purga masiva de condena en kick/ban, ni generar sanciones duplicadas ante errores de SQLite. Producción requiere autorización independiente.

## Honeypot: interfaz limpia y semántica de controles — 2026-10-17

El propietario autorizó simplificar la presentación de AutoMod → Honeypot: resumen de estado, canales, acción aplicable y borradores sin ruido de campos vacíos. Configuración secundaria en subpaneles; conservar capacidades existentes. Activar y Reanudar son verdes, Pausar y Retirar rojos; Crear canal es azul porque **abre confirmación**, no crea de inmediato; editores y navegación a subpaneles son azules, Guardar verde, Descartar rojo, Volver gris. Las preferencias anteriores establecen que Cancelar y Cerrar continúan **rojos**, aunque las recomendaciones preliminares usaran gris. Selecciones y cambios de estado son borrador: no guardar hasta pulsar Guardar cambios; crear/retirar canales exigen confirmación propia explícita, con revalidación antes de ejecutar. Las ediciones de aviso ya existentes mantienen confirmaciones independientes para no mezclar su persistencia con el panel. Cambios de diseño no autorizan tocar sanciones, esquema SQLite ni `main`.

## Honeypot: pausa segura y mensaje intacto — 2026-10-17

El propietario autorizó conservar el mensaje del miembro veterano que activa el umbral antifallos (3 miembros distintos del mismo servidor durante 5 minutos), suspender Honeypot en ese servidor y notificar a administradores mediante Logs, sin imponer sanción a ese evento. La comprobación se realiza antes del borrado; la ruta normal conserva el archivo de evidencia antes de eliminar y sus acciones habituales. No reconstruir mensajes eliminados antes del umbral, no notificar en canales públicos alternativos y no alterar `main` sin aprobación específica.

## Seguridad Honeypot: aislamiento multiservidor — 2026-10-16

Se autoriza corregir exclusivamente los dos estados de Honeypot compartidos entre servidores y reforzar `history`/claridad de exenciones, preservando sanciones, configuración, DB y flujo existente. Antifallos: umbral 3 veteranos distintos/5 minutos **por servidor**, sin reiniciar contadores de otros servidores; candado de castigo **por servidor y miembro**. No se habilitan nuevas sanciones ni se cambia el orden de eliminación/antifallos sin decisión adicional. Pruebas aisladas primero; solo laboratorio para Discord. `main` requiere aprobación separada.

## Fusión de canales: vista previa operativa y retorno editable — 2026-10-16

Decisión implementada del propietario: el último paso de `/fusionar_canales` mostrará explícitamente **origen → destino**, recuento actual de mensajes en origen, nombre final y el orden de migración (comprobar permisos/recuento; cambiar nombre del destino si corresponde; recrear mensajes cronológicamente después de los existentes; tratar adjuntos y errores; conservar o eliminar el origen únicamente bajo condiciones seguras). No afirmar que Discord traslada mensajes: el bot los recrea; preserva los ya existentes en destino y el origen por defecto. El botón **Confirmar fusión es verde** (`success`), **Volver es gris** (`secondary`) y **Cancelar rojo** (`danger`). Volver abre un **editor efímero del borrador** con selección de canales, nombre final y eliminación opcional, permite recalcular el recuento y regresar a la vista previa. Ninguna selección ni Volver ejecuta migración. Las comprobaciones de usuario autorizado, Gestionar canales, accesos del bot, límite y variaciones de recuento se repiten antes de cualquier cambio. Si cambia el historial durante la copia, no se elimina el origen. Evitar prometer copia perfecta de respuestas/archivos cuando la API impone limitaciones. Cambios solo en `Pruebas`, sin modificación de `main`.

## Ajuste solicitado: Cancelar y Cerrar en rojo — 2026-10-16

El propietario establece explícitamente que **todos los botones de Cancelar y Cerrar**, incluida la variante «Cancelar edición», deben usar rojo (`discord.ButtonStyle.danger`), aun cuando la operación simplemente descarte un borrador o cierre un panel. Esta decisión **sustituye solo la clasificación cromática** anterior, donde Cancelar y Cerrar eran grises. «Volver», «Vista previa» y las consultas neutrales continúan grises. **Se conserva el comportamiento:** Cancelar/Cerrar nunca guardan por sí mismos; los permisos y las confirmaciones existentes siguen siendo obligatorios. Rojo no implica ejecutar una operación destructiva adicional.

## Estándar visual de botones y consecuencias — 2026-10-16

Decisión del propietario para todas las interfaces de configuración y moderación: **rojo** (`danger`) identifica sanciones, eliminaciones, descartes de cambios pendientes y confirmaciones destructivas; **verde** (`success`) identifica guardado explícito, publicación, activación y acciones positivas definitivas; **azul** (`primary`) identifica configuración, edición y pasos preparatorios que aún no guardan; **gris** (`secondary`) identifica cancelar, volver, cerrar panel sin efectos, consultar y vista previa. Diferencia obligatoria: **Cancelar** no altera datos y es gris; **Descartar cambios** elimina el borrador y es rojo. En una confirmación, el color depende de la operación real (una retirada/destrucción es roja aunque diga «Confirmar»). Los botones de enlace de Discord usan el estilo `link` y no admiten estos cuatro colores. No interpretar el color como autorización para guardar automáticamente: seleccionar o editar un borrador jamás persiste por sí solo.

El criterio es independiente de la petición ya aprobada de simplificar los flujos Guardar/Descartar/Cancelar y eliminar las revisiones redundantes; **esa simplificación funcional aún debe implementarse y probarse donde siga existiendo, incluido el programador de embeds**. No afirmar su finalización por el mero cambio de colores. Mantener etiquetas concretas según cada operación y no perder confirmaciones explícitas para cambios administrativos.

## Política de fiabilidad ante fallos de comprobación — 2026-10-16

Las comprobaciones de permisos y estado deben repetirse tras cualquier espera/red antes de cambiar roles. Si SQLite no permite determinar si hay una sanción pendiente, se bloquea el perdón en vez de asumir estado libre (fail closed); informar del error, conservar datos y evitar reintentos ciegos. Un error de red/API en un servidor no debe abortar el arranque de loops ni impedir la recuperación de otros servidores; aislar por servidor las reconciliaciones sin prometer recuperación total. Mantener confirmaciones y reportes, usar mensajes formales que identifiquen permisos específicos. Test y código se modifican solo en Pruebas.

## Referencia de experiencia real de usuarios de bots — 2026-10-16

Fuente complementaria aportada por el propietario: PDF de 13 páginas «Voz de los usuarios: quejas, fallos y peticiones sobre bots de Discord» (investigación fechada 2026-10-15, compartida en conversación). Sirve para formular riesgos y criterios de aceptación, NO para afirmar que El Heraldo tiene un fallo o que un competidor necesariamente lo tiene. La recopilación combina documentación y prensa con testimonios de diferentes años, fuentes sesgadas y opiniones; no es un muestreo representativo. No reproducir ni publicar el PDF íntegro en el repositorio sin autorización.

**Prioridad de trabajo confirmada como criterio, no como nueva funcionalidad:** (1) fiabilidad operativa — permisos/jerarquía, vistas persistentes tras reinicios, operaciones Discord+SQLite parciales, respuestas rápidas, idempotencia de sanciones/logs; (2) seguridad y privacidad — permisos mínimos, inventario de datos, acceso/retención de evidencias, tokens y secretos fuera de código/logs, revisión de infraestructura en desuso e intents privilegiados; (3) interfaz y experiencia — español formal, errores que indiquen qué falta, borradores con confirmación, sanción explicada al afectado y edición reutilizable; (4) evaluar capacidades solicitadas, como diagnóstico para administradores y apelaciones, SOLO tras consultar código y obtener decisión del propietario. No priorizar módulos adicionales ni integración en `main` por una tendencia o reseña.

Para cualquier propuesta nueva: comprobar implementación vigente, identificar riesgo real, precisar pruebas automatizadas y aceptación en Heraldo's Lab, documentar coste de datos/permisos y solicitar permiso cuando corresponda. El diagnóstico administrativo, las apelaciones integradas y los plazos de retención necesitan definición del propietario; este documento no los autoriza ni los marca como implementados.

## Calidad del lenguaje en El Heraldo — 2026-10-15

Priorizar ortografía, gramática y mensajes formales comprensibles. No mostrar estructuras JSON de configuración cuando se pueden explicar en español natural, ni secuencias \\n literales. Una etiqueta de botón debe describir la acción siguiente; borrador, revisión y confirmación se distinguen claramente. Los estados mostrados deben coincidir con lo que se guardará. Solo mostrar parámetros aplicables; Cancelar jamás persiste. Aplicar esta directriz a los demás mensajes al revisarlos. Sin cambios en producción.

## Un único registro por expulsión de verificación — 2026-10-15

Preservar el embed detallado de verificación (primera o segunda falta, DM de recuperación, resultado) como registro principal; solo suprimir «Miembro expulsado» general cuando hay prueba de publicación correcta de ese mismo evento. No ocultar expulsiones realizadas por otros moderadores, salidas naturales, baneos o eventos sin registro detallado. Registrar la deduplicación con memoria efímera asociada a sesión de ingreso; no eliminar evidencias ni cambios de configuración. Solo Pruebas.

## Nombres de embeds personalizados — 2026-10-15

Los nombres de /embed crear permiten escritura natural en español hasta 64 caracteres, incluyendo tildes, espacios, números, emojis habituales y puntuación segura. Todo comando de embeds debe usar normalización Unicode y sin distinción de mayúsculas para evitar duplicados; mantener nombres antiguos y sus referencias sin migraciones. Rechazar menciones y caracteres de control. Sin modificaciones en main.

## Normas Test: razón única, disculpas y retorno — 2026-10-15

Para una condena experimental en Railway Test el motivo público es «Prueba funcional autorizada de El Heraldo Test.» sin importar origen; conservar campo origin. Antes de cualquier expulsión o baneo originado por El Heraldo Test se intenta DM de disculpa con invitación max_uses=1, max_age=0 en canal visible para rol base, sin publicar URL en logs. No prometer enlace si no se pudo generar ni reingreso de usuarios aún baneados; después de expirar el baneo temporal se podrá usar. La duración predeterminada BAN es 5m exclusivamente en Test y permanente en producción hasta que un administrador confirme ajuste por servidor desde /setup → Moderation → Baneo temporal. /ban con 0 es permanente explícito; duración de regla BAN tiene prioridad. No modificar producción, main ni permisos.

## Reglas de acciones por reportes y límite WARN — 2026-10-15

Decisión autorizada: administrador puede activar/desactivar individualmente Advertir, Aislar, Expulsar, Banear y la opción de Condenar desde Moderation → Reportes, sin alterar manualmente `/warn`, `/mute`, `/kick`, `/ban` ni `/condenar`. Las opciones existentes permanecen habilitadas por defecto hasta que se desactiven expresamente, con confirmación previa. El máximo WARN vigente es configurable de 1 a 5, con valor predeterminado 3. Al alcanzar ese máximo, el valor por defecto es **Solo avisar**. Se pueden configurar Aislar, Expulsar, Banear o Condenar; Aislar permite elegir duración predefinida. La acción elegida debe estar habilitada y contar con permisos y jerarquía suficientes; no implica purgar mensajes. Evitar reintentos automáticos de sanciones con resultado incierto. El administrador debe comprender la operación antes de confirmar y Cancelar no guarda. Condena por reacción directa requiere permiso de expulsión o administrador y respetar jerarquía también al confirmar motivo. No modificar producción sin autorización.

## Expedientes privados — criterio autorizado 2026-10-15

Conservar íntegramente diseño, campos, colores, plantilla, enlaces y botones de la tarjeta de condena actual. Orden: asignar rol Condenado → publicar embed original en el canal de condenados mencionando al miembro → crear hilo privado separado por expediente → invitar al condenado → enlazar conversación mediante botón en tarjeta, sin alterar embed. Personal administrativo con Gestionar hilos puede consultar todos; condenados solo sus hilos privados y cualquier tarjeta visible en el canal compartido. Discord no puede ocultar individualmente tarjetas del canal principal a miembros con permiso de historial. Preservar DM y archivo privado de evidencias; bloquear y archivar hilo al terminar una condena sin borrar historial. No crear hilos públicos como alternativa. Si el servidor no permite privados, advertir y mantener función estable. Permisos de acceso al canal solo cambian con confirmación administrativa expresa. No cambiar `main` sin autorización.

En /setup, utilizar menús desplegables para opciones disponibles o valores predefinidos; dejar campos libres cuando realmente se requieran. Guardar solo después de confirmación explícita y verificar permisos en cada interacción.

## Almacenamiento externo de respaldos — 2026-10-13

Propietario autorizó preparar y probar un destino gratuito en Supabase sin trasladar aún datos de producción. Bucket privado específico, autenticación con cuenta técnica y RLS de bucket; se prohíbe introducir `service_role`, secret y claves S3 globales en el bot. Cifrado independiente AES-256-GCM, claves fuera de Git, sin auto-programación ni retención destructiva. Advertencia: Free no garantiza disponibilidad continua, tiene límite de 50 MB por objeto y puede pausarse. Activación real y cambio de main siguen sujetos a pruebas, respaldo y autorización separada. Procedimiento en `RESPALDOS_SUPABASE.md`.

# Decisiones de producto y desarrollo — El Heraldo

**Actualizado:** 2026-10-08. Este documento recoge acuerdos funcionales; para conocer el estado efectivo consultar `ESTADO_PROYECTO.md` y el código.

## Acuerdos vigentes
1. **Entornos separados.** `main` solo para producción; `Pruebas` para desarrollar y ensayar. Discord bot, token, servidor y base de datos de prueba independientes.
2. **Protección de datos.** No publicar secretos, tokens ni evidencias privadas; nunca reutilizar el token o base de datos de producción.
3. **Configuración consciente.** Los cambios de configuración no se guardan al editar o navegar: exigir botón explícito para guardar, borrar, importar y confirmar acciones.
4. **Lenguaje formal.** Mensajes emitidos por El Heraldo en español formal, coherentes y sin emojis decorativos. Permitir emojis solo cuando son necesarios para su función (p. ej., reacciones).
5. **UX de referencia.** Sapphire inspira la funcionalidad y claridad de los paneles, especialmente Mensajes y Reaction Roles; no copiar contenido propietario ni asumir que una similitud visual basta.
6. **Moderación clara.** La tarjeta de condena debe explicar motivo, autor de la medida, momento, canal de origen y roles retirados cuando proceda. Admitir enlace configurable y comunicación pertinente por canal de castigo y DM.
7. **Evidencia duradera.** Los enlaces a mensajes sujetos a eliminación no bastan como evidencia: preservar copia autorizada del texto/adjuntos con controles de acceso y retención adecuados.
8. **Sin campos irrelevantes.** No incluir secciones, referencias o avisos que no apliquen al caso. Evitar notificaciones duplicadas.
9. **Condena configurable.** Permitir ajustar duración de la sanción y comprobar funcionamiento de perdón/restauración.
10. **Identificadores de casos.** Preferencia por identificadores de siete caracteres alfanuméricos legibles, sin prefijos arbitrarios no acordados.
11. **Plantillas.** Permitir imágenes con URL en embeds; publicación y edición de mensajes por administradores autorizados y confirmación.
12. **Regresión y trazabilidad.** Cada cambio debe llevar commit descriptivo, comprobación automática y registro explícito de pruebas reales o pendientes.
13. **No despliegue automático de experimentos en producción.** Revisar cambios y aprobar su integración mediante PR antes de llevarlos a `main`.
14. **Trabajo entre agentes.** ChatGPT, Codex, Claude y otras sesiones deben leer `AGENTS.md`, revisar esta documentación y actualizarla tras decisiones o verificaciones; GitHub es el punto de intercambio común.

## Revisión de acuerdos
Una nueva decisión debe indicar fecha, motivo y qué regla reemplaza. No modificar decisiones existentes silenciosamente. Toda política de acceso al servidor de pruebas debe mantenerse dentro de las autorizaciones otorgadas.

## Laboratorio de calidad (2026-10-09)
- Preparar verificaciones offline ejecutadas por GitHub Actions antes de incorporar cambios a `Pruebas`.
- Separar rigurosamente resultados CI, despliegues Railway y pruebas reales de Discord; no declarar paridad funcional sin las tres evidencias pertinentes.
- Nunca ejecutar interacciones destructivas en miembros reales ni automatizar cuentas personales; un futuro bot de pruebas auxiliar requerirá autorización, aislamiento y alcance explícitos.

## Etapa 1 autorizada — 2026-10-09 (America/Santo_Domingo)
- La reconciliación incorpora el historial de `main@6f9f9ee` al desarrollo conservando las funciones de `Pruebas@b8480b8`. Los conflictos no justifican eliminar Mensajes ni las confirmaciones de restauración de Logs.
- Preparar la integración en el PR #6; fusionar con un commit de merge (no squash ni rebase) para conservar la ascendencia de `main` y resolver la divergencia histórica.
- CI valida Python 3.11, 3.12 y 3.13 con `discord.py==2.7.1` en `requirements-ci.txt`. Las dependencias transitivas no están bloqueadas; no afirmar reproducibilidad completa. `requirements.txt` y el runtime de Railway permanecen sin cambio en esta etapa.
- La preparación y publicación del PR no acredita pruebas Discord. La fusión hacia `Pruebas` puede activar Railway y debe tratarse como integración en laboratorio; `main` y producción requieren autorización independiente.

## Seguridad y formatos — 2026-10-10
- Las acciones públicas de roles no deben conceder permisos administrativos (administrador, gestión de servidor/roles/canales/webhooks, expulsión, baneo o moderación), ni permitir eludir una condena activa. Se revalida al ejecutar para detectar cambios posteriores del rol.
- Una evidencia parcial no acredita copia íntegra ni permite purgar su mensaje de origen. No usar el canal de condenados como archivo alternativo.
- Kits v2 contienen únicamente valores visuales; se admiten v1 y v2, se excluyen acciones y vínculos privilegiados. Los reemplazos son optativos, confirmados y sujetos a comprobación de cambios concurrentes.
- Las variables son una lista cerrada, no expresiones ejecutables; se validan límites después de expandirlas y se deshabilitan menciones automáticas.
- La autorización vigente permite desarrollar y preparar el laboratorio; no autoriza modificaciones en main ni producción. Las funciones todavía pendientes no se consideran completadas por aprobar pruebas offline.

### Recuperación de ingresos — 2026-10-10
- Los trabajos conocidos de Join Roles se almacenan antes de esperar; el reinicio no reinicia el contador. La ejecución consulta estado actual y no debe otorgar roles durante una condena.
- Los formularios migrados adjuntan el cambio propuesto y anterior; las publicaciones asociadas se sincronizan únicamente después del guardado confirmado.

### Programación de Mensajes — 2026-10-10
- Se valida la zona horaria al crear y se rechazan horas locales inexistentes o ambiguas. Repetición diaria/semanal conserva la hora local; durante un salto de primavera, una futura hora inexistente se normaliza a la hora real posterior al salto.
- Ante incertidumbre de envío se pausa esa programación para revisión; no se garantiza entrega exactamente una vez entre SQLite y Discord. Crear otra exige revisar el canal. La plantilla se resuelve al ejecutar, por lo que sus modificaciones confirmadas afectan futuros envíos.
- Los diseños explícitos de Mensajes no reciben el formato global automático, para conservar texto independiente, pies propios y límites validados. El resto de las respuestas mantiene el comportamiento previo.

### Automatizaciones activadas por actividad — 2026-10-10
- Autorespuestas usan texto literal, sin expresiones regulares suministradas por usuarios. Solo una respuesta por mensaje y límite común del canal, persistente entre reinicios.
- Sticky elimina únicamente su publicación anterior verificada, antes de enviar la sustituta. Se conserva la última publicación al desactivar la regla. Una interrupción no autoriza repetir envíos inciertos.
- Los webhooks se administran exclusivamente mediante el bot y el canal seleccionado; no aceptar tokens o destinos arbitrarios. Los botones y selectores de roles quedan reservados a publicaciones directas del bot, conservando esa funcionalidad por su vía original.


### Editores y componentes para revisión — 2026-10-10
- Los formularios visuales editan un borrador; un valor que exceda la capacidad del formulario se conserva y deriva al editor JSON. Cancelar o caducar invalida los modales pendientes.
- Toda secuencia de componentes requiere confirmación del usuario que la activó, con destinos completos adjuntos; se detiene ante el primer error. Las acciones públicas requieren permisos actuales de Administrar mensajes, acceso y envío para ejecutor y autor en destino. Los resultados parciales son explícitos.
- Los componentes quedan ligados a una revisión de plantilla; cambiar su configuración invalida las publicaciones anteriores hasta republicarlas. Las respuestas generadas no encadenan componentes.
- La copia de roles se persiste antes de retirarlos. Una operación Discord y una escritura SQLite no son atómicas; conservar pruebas de recuperación en el recorrido de revisión.
- El PR preparado para revisión no implica aprobación de producción, paridad completa con Sapphire ni cierre de los pendientes enumerados en REVISION_PR7.md.

## Criterio técnico aplicado en auditoría — 2026-10-11

En la rama de PR #10 se reutilizó el flujo de propuesta, confirmación explícita y comprobación de permisos al pulsar «Guardar cambios» para los comandos administrativos heredados. Cancelar no debe escribir. Operaciones de creación/retiro de canales, destinatarios o exenciones usan confirmaciones específicas con identidad y permisos revalidados. Este criterio desarrolla el acuerdo vigente de configuración consciente; **no autoriza despliegue en producción** ni sustituye pruebas en Discord.

## Continuidad de restauraciones parciales — 2026-10-11

Para evitar perder información al levantar una condena, el registro de roles que no pudieron devolverse se conserva por servidor/miembro y el administrador puede reintentar su restauración con confirmación explícita, permisos de Gestionar roles, control de jerarquía y rechazo de condena activa. Esta implementación está propuesta en PR #11 para el laboratorio y exige prueba interactiva antes de producción.


## Coordinación y auditoría integral — 2026-10-11
- Codex asume el trabajo técnico directamente; ChatGPT coordina propuestas y el propietario decide producto y producción. GitHub es la continuidad compartida. No se añadieron agentes/conexiones.
- Separar inventario estático, pruebas offline, arranque Gateway y pruebas humanas. Una CI verde no prueba el recorrido si sustituye el callback que pretende verificar.
- Mantener códigos de expedientes trazables; la simplificación de títulos, catálogo oficial, purga en «Solo reportar» y navegación común se presenta como propuesta, sin alterar datos existentes por inferencia.
- Servidor real: nombre y autorización pendientes. No conectar, sancionar ni activar automatismos allí; plan supervisado en audit/PROPUESTAS_Y_PLAN_REAL.md. main requiere autorización independiente.


## Coordinación de verificación y respaldo — 2026-10-11
- Los temporizadores de verificación y del rol Sin Verificar pertenecen al mismo proceso cuando ambos están pendientes: comparten exclusión y resolución. El respaldo respeta la acción y plazo configurados del proceso principal.
- Una expulsión confirmada produce un solo registro por estos dos temporizadores. Las opciones ban y solo registrar se conservan; no suprimir registros de moderación necesarios para ocultar duplicados.
- Al fallar la operación remota no se anuncia éxito ni se descarta el pendiente. La prueba de laboratorio debe verificar la corrección después del despliegue, conservando la captura anterior como observación del propietario.

## Alcance confirmado por el propietario — 2026-10-11
- Continuar directamente en Pruebas, sin ramas adicionales ni PR temporales; conservar la copia local histórica divergente y trabajar desde remoto reconciliado.
- Prioridad: H-01, conservación integral de evidencias, respaldo/restauración, hallazgos confirmados y laboratorio. Producción e infraestructura sensible requieren autorización independiente.

## Aplicación de conservación integral — 2026-10-11
La autorización de H-02 se implementa reutilizando el canal privado y SQLite existentes. Ninguna copia parcial autoriza borrar; los recursos no soportados se conservan en origen. El rol administrado del propio bot puede acceder al archivo, junto al acceso inherente de administradores; otros roles visibles bloquean el archivo. No se crean ni reconfiguran canales. Los envíos inciertos requieren revisión y se conservan, sin retención destructiva automática.

## Excepción al flujo de ramas — 2026-10-12
- **Nueva decisión del propietario:** se reemplaza la prohibición absoluta de ramas adicionales indicada en «Alcance confirmado por el propietario — 2026-10-11» únicamente para tareas de Codex.
- Codex puede crear ramas **temporales** por tarea y PR exclusivamente con destino `Pruebas`. `main` permanece protegida; esta autorización no incluye PR, fusiones ni despliegues en producción.
- Antes de integrar: contrastar base actual de `Pruebas`, revisar cambios concurrentes, verificar pruebas pertinentes y riesgos de despliegue en Railway Test. No usar `force push` ni ocultar resultados de CI/Discord.
- Tras integrar o descartar, eliminar la rama temporal cuando se verifique que no conserva trabajo pendiente. No crear ramas permanentes adicionales.
- Otros agentes pueden revisar y coordinar, pero esta excepción de creación de ramas se concede exclusivamente a Codex. La rama interna `work` en Codex no supone por sí sola un error.
- Los cambios en `Pruebas` podrían desplegar Railway Test automáticamente; no asumir que una compilación correcta acredita interacciones Discord.

## Aplicación H-03 — 2026-10-12
La petición del propietario autoriza implementación y pruebas de respaldo/recuperación con SQLite sintético. Se usa la API online de SQLite, no una copia directa del archivo activo. La restauración exige servicio detenido, entorno y esquema explícitos, conserva la base anterior y no borra WAL/journals para forzar una instalación. Los respaldos incluyen datos privados y deben permanecer fuera de Git. La conservación configurable solo propone candidatos; no se autorizó eliminar copias ni evidencias. No se conectó almacenamiento externo ni se programaron tareas en Railway. Su destino, coste, claves, frecuencia y validación de laboratorio quedan sujetos a revisión antes de activarlos; producción sigue protegida.

## Conservación de la funcionalidad estable de main — 2026-10-12
- Decisión expresa del propietario: todo lo que funciona correctamente en `main` permanece como está, salvo que posteriormente observe una anomalía o autorice un cambio; también se pueden corregir defectos técnicos o de seguridad demostrados y justificados.
- En `Pruebas` se preserva ese comportamiento. No repetir desarrollo ni rediseños por falta de una nueva prueba manual; antes de intervenir comparar la implementación vigente de ambas ramas e identificar una diferencia concreta o requisito nuevo.
- Si una modificación rompe una función estable, tratarlo como regresión y restaurar el comportamiento de referencia salvo instrucción distinta del propietario.

### 2026-10-24 — Custodio: acciones configurables por tipo (fase preparatoria)
- Cada comunidad decide sus reglas oficiales. **NH designa exclusivamente estándares internos de El Heraldo**, no normas de convivencia ni un reglamento global. Las plantillas son orientativas; no tipifican faltas por sí mismas.
- Se admiten propuestas `Solo reportar`, `Expulsar` y `Banear` en el nuevo editor `AutoMod → Modo Custodio → Acciones por tipo`. Cinco tipos orientativos: spam/publicidad, acoso reiterado, fraude/suplantación, amenazas graves y contenido fuera de lugar. El botón **Usar sugerencia** copia una propuesta al borrador; ningún valor punitivo se ejecuta por seleccionarlo.
- Los cambios se guardan por servidor mediante CAS en `custodio_rule_actions_v1`, con `enforcement_enabled=false` obligatorio. Cualquier dato inválido falla cerrado; **no hay activación de sanciones ni de supervisión** en esta entrega.
- Para una futura implementación sancionadora harán falta: correspondencia explícita con una Server Rule vigente y aprobada de ese servidor, permisos y jerarquías, exenciones de dueño y moderadores, evidencia y revisión de ambigüedades, idempotencia frente a eventos repetidos, registro privado y confirmación administrativa específica para activar. No se autoriza modificar `main` ni desplegar sanciones por esta decisión.
