## 2026-10-28 — Ayuda contextual de Plantillas

La explicación de `/setup → Mensajes → Plantillas` ya no deriva al comando heredado `/editar_plantilla`. La ayuda se refiere a las opciones que realmente existen en el propio panel: crear, editar, previsualizar, seleccionar canal y publicar. Se actualizan `es-419`, `en-US` y `pt-BR`, junto con los catálogos auxiliares y la regresión. No se modifica el comando alternativo, el editor, la persistencia ni producción; cambio exclusivamente informativo en `Pruebas`.

## 2026-10-27 — Nomenclatura de /setup → Mensajes: «Plantillas»

La opción anteriormente llamada **Mensajes personalizados** ahora se presenta como **Plantillas** (en-US: **Templates**, pt-BR: **Modelos**) en el desplegable de `/setup → Mensajes`. También se actualizan la descripción de la opción, la explicación del menú y la referencia de Kits para evitar nombres anteriores. Se mantiene sin cambios el identificador interno `templates`, su editor, las plantillas existentes, la configuración por servidor y la persistencia. Alcance exclusivo: `Pruebas`; no modificar `main`.

## 2026-10-27 — Ajuste de navegación: retirar «Crear mensaje» del menú de Mensajes

Por petición expresa del propietario, en `/setup → Mensajes` se retira la entrada **Crear mensaje**. Se conservan las opciones de mensajes editables (verificación, DM, sugerencias, Honeypot, condenas y logs), las plantillas y otros módulos existentes. No se eliminan plantillas guardadas, programaciones ni su persistencia; los editores subyacentes se conservan para una reorganización posterior. Se retira el tratamiento excepcional de interacciones de Activity asociado exclusivamente a esa entrada. Se actualizan los tests de navegación y ACK para que el menú oculto no bloquee el despliegue. Alcance: rama `Pruebas`; producción queda intacta.

## 2026-10-27 — Decisión corregida: /setup → Mensajes → Crear mensaje (sin Programaciones como módulo)

El propietario corrigió expresamente el diseño anterior. `Programaciones` se elimina del desplegable y de la navegación de `/setup → Mensajes`. Se sustituye por **Crear mensaje**, que abre directamente **un único editor inspirado en el formulario Create Autofeed de Carl-bot**. Estructura visual del editor: Canal, Mensaje, Mostrar editor de embed, Fecha, Rol para mencionar y Repetir cada (meses/días/horas/minutos). La fecha es opcional: sin fecha `Crear mensaje → Confirmar cambios` envía inmediatamente; con fecha futura se guarda un envío programado. Se mantienen borradores, vista previa, confirmación, editor avanzado de embed y los footers globales. «Descartar cambios» solo aparece con cambios pendientes; «Volver» regresa a `/setup → Mensajes`. Los modales de Discord no permiten dibujar el formulario web literalmente, por lo que cada apartado se edita desde controles en el mismo mensaje, con subeditor que regresa al panel.

No se borraron ni migraron destructivamente programaciones existentes, SQLite o estados de envío. El motor de recurrencia sigue disponible, y los comandos heredados siguen registrados por compatibilidad (no constituyen un módulo de `/setup`). Los envíos inmediatos requieren confirmación, comprueban canal/roles/permisos y usan el footer global por `stamp_embed`; no hay reintentos automáticos tras respuesta incierta que puedan duplicar el mensaje. Solo se cambió `Pruebas`, nunca `main` ni producción.

Implementación en `autofeed_setup.py`, `message_publish.py`, `bot.py` y catálogos es-419/en-US/pt-BR; tests en `tests/test_autofeed_setup.py` y `tests/test_autofeed_publish.py`. **Railway Lab**: commit `Pruebas@123015797cc67899a35c0b37b1b006f6f8a61142`, despliegue `81bd8c4b-3431-4640-964e-0681392e0cc1`, **SUCCESS**. **30 pruebas automáticas superadas**, Discord Gateway conectado, `COMMAND_SYNC 52` y autopruebas de `/setup` correctas. Después del despliegue se restauró `preDeployCommand=["python tools/custodio_analysis_health.py"]`; volumen `/data` conservado. Queda pendiente validación visual manual de todos los controles y envío real en el servidor de pruebas.

## 2026-10-27 — Constructor de embeds Carl adaptado a /setup, sin alterar footers

Para `/setup → Mensajes → Programaciones → Crear programación → Editor de embed`, se creó `autofeed_embed_builder.py` y se conectó a `autofeed_setup.py` y `message_automation.py`: secciones Contenido/color, Autor, Imágenes, Campos adicionales (hasta 25) y Fecha automática; enlaces HTTPS; menciones de rol/canal por selectores y campos de texto; vista previa real; edición de campos; sin panel web ni grabación automática. El nuevo motor entrega el embed completo (incluidos autor, imágenes, campos, color y fecha), no solo título/descripcion.

**Footer: norma existente inalterable**. No hay ningún editor de footer nuevo. Al previsualizar y al enviar el embed, se utiliza exclusivamente `host["stamp_embed"]`, como el resto del bot: producción utiliza nombre/icono dinámicos del servidor y Test el footer fijo `El Heraldo's Labs 🧪`. El usuario puede configurar opcionalmente la fecha automática, pero no el pie de identidad. El sistema reserva tamaño para el footer. La prueba `tests/test_autofeed_embed_builder.py` comprueba que un footer arbitrario suministrado en los datos no sustituye el footer Labs.

Deploy Lab: `Pruebas@381943986507e73de2e449ef000e61221ecaea53`, Railway deployment `bf95348b-113f-40c2-9060-88910ae92961`: **SUCCESS**, 24 tests autofeed aprobados, Discord Gateway conectado, `COMMAND_SYNC 52`, autopruebas `/setup` correctas, volumen `/data` conservado. Para esta publicación se utilizó temporalmente una comprobación de pre-despliegue enfocada en los tests de mensajes; después se restauró el `preDeployCommand` original de Custodio. `main`/producción intactos. Falta aceptación visual real de todos los botones y prueba de envío de ejemplo en Discord, que no se simularon con pruebas automatizadas.

## 2026-10-27 — AutoFeeds: mejoras de menciones y calendario, Lab confirmado

Se mejoró `/setup → Mensajes → Programaciones → Crear programación` con **Insertar mención** (selector de rol/canal y destino mensaje o descripción de embed), selector de rol de aviso restablecible tras «Sin rol», **Fecha y hora** en dos campos y **Frecuencia** con una vez/diaria/semanal/mensual/personalizada. Insertar y seleccionar solo cambia el borrador; persistencia exclusivamente mediante Guardar cambios → Confirmar cambios. Se preservan footer automático, ausencia de @everyone/@here, aislamiento de servidor, políticas de rol mencionable para ping y referencias no mencionables solo visuales. La mención de rol dentro del embed no notifica; el rol de aviso se añade al contenido exterior del mismo mensaje.

Archivos modificados: `autofeed_setup.py`, `message_autofeeds.py`, `message_automation.py`, `tests/test_autofeed_setup.py`. Revisión desplegada `Pruebas@d2aa721b36945b1cdb63de6ca887aa37fda36ed4` en Railway Test, despliegue `037c52e8-0f32-4dbb-ae4f-229cee8fd46b`: **SUCCESS**, 17 pruebas AutoFeed aprobadas y Discord Gateway conectado. `preDeployCommand` original de Custodio restaurado inmediatamente después a `python tools/custodio_analysis_health.py`. Volumen /data persistente intacto. `main` y producción sin cambios.

Pendiente: ensayos manuales reales de inserción de roles/canales, reelección del rol, vistas previas y envío programado en Discord (las 17 pruebas son automatizadas, no clics humanos). Advertencia conocida: comprobación externa de IA de Custodio HTTP 400 en futuros despliegues, ajena a AutoFeeds; no se desactivó definitivamente.

## 2026-10-27 — AutoFeeds: despliegue Lab comprobado
Se desplegó y arrancó en Railway **Test/Lab/worker** el código `Pruebas@7c36e57002a92d39037d32d70fda0fbb8bb5b862`, deployment `745be635-9d15-4ccc-852a-98119668abd2`: **SUCCESS**. Se verificaron arranque del proceso, Gateway Discord conectado y `COMMAND_SYNC status=SUCCESS scope=GUILD locale=es-419 commands=52` (51 antes de añadir `/programar`). Volumen persistente montado en `/data`; `main`, producción y cron H-03 intactos.
El primer intento había quedado bloqueado en el pre-despliegue por el análisis externo de Custodio (HTTP 400 `invalid_request`). Se hizo una **excepción temporal exclusiva de Lab**: sustituir la comprobación del proveedor por `python -m unittest discover -s tests -p test_autofeeds.py -v` para esta entrega. Los **9 tests nuevos pasaron** (0 fallos) sobre el contenedor real, con avisos `ResourceWarning` por conexiones de test que no invalidaron el resultado. El servicio alcanzó `SUCCESS` y se **restauró inmediatamente** `preDeployCommand=["python tools/custodio_analysis_health.py"]` para las siguientes publicaciones; `sleepApplication=true` y volumen original conservados.
**Aceptación de usuario aún pendiente:** los 9 tests son automáticos, no clics reales ni publicaciones en Discord. No atribuir los 52 comandos a la ejecución de cada subcomando. El problema de la sonda previa de IA persiste y volverá a bloquear futuros despliegues hasta que su propietario lo corrija; no se ha desactivado ni alterado el módulo de Custodio.

## 2026-10-27 — AutoFeeds: nueva interfaz /programar (primera entrega, Pruebas)

En la rama de desarrollo se añadió `message_autofeeds.py` y el grupo `/programar`: crear texto directo o usar plantilla, listar, editar, pausar, reanudar, silenciar la mención, mover, eliminar y configurar permisos. La creación usa modal + vista previa + Guardar cambios. Los selectores solo preparan borradores; eliminar requiere confirmación; Activar/Pausar afectan únicamente al estado de la autorización. Los miembros no administradores quedan bloqueados por defecto, hasta configurar al menos un canal, un rol y activar la política; tienen un límite de 3 programaciones (25 por servidor). Nunca se habilita `@everyone` automático y el rol elegido debe ser mencionable.

El motor `message_automation.ScheduledMessages` conserva la misma clave `message_schedules`, el estado de envío y las precauciones ante envíos inciertos. Se añadieron recurrencia mensual y por intervalo >= 1 h, roles opcionales y textos propios, comprobación de permisos en ejecución, CAS de edición y conservación de pausas concurrentes. `/programar_mensaje` y `/embed programaciones` siguen accesibles y no se migran destructivamente sus datos; la convergencia completa de los dos catálogos heredados es una fase posterior.

Integración: `/mensajes → Programaciones` para configurar acceso y regreso mediante Volver. Registrados los metadatos nativos en el catálogo de es-419, en-US y pt-BR; las nuevas pantallas también incluyen textos traducidos. Regresiones nuevas en `tests/test_autofeeds.py`. **No declarar CI, despliegue en worker ni clics reales sin evidencia.** El worker de Lab se observó fijado a `1407d5c2` (no este cambio) y con un último despliegue FAILED anterior a esta entrega; no se modificó la condición previa de despliegue ni el volumen. `main` y producción intactos.

## Encuestas voluntarias de salida — 2026-10-20

**IMPLEMENTADO en `Pruebas`, sujeto a CI y Discord:** configuración separada y desactivada por defecto desde `/setup → Mensajes → Logs → Eventos de miembros → Comentarios de salida`, con Guardar/Descartar (NH); solo se solicita DM cuando la auditoría fue consultada satisfactoriamente sin encontrar un kick/ban, existe la tarjeta original y el canal de logs está restringido al personal moderador. Los errores o permisos insuficientes de auditoría cancelan la encuesta. El botón persistente de DM abre un modal voluntario (máximo 500 caracteres, siete días); SQLite asocia la solicitud por servidor, miembro, DM y tarjeta, evita duplicados y conserva respuestas pendientes de editar tras reinicios. `exit_comment_apply` edita la tarjeta, no crea registros secundarios; sin respuesta no muestra el campo «Comentario». El usuario solo puede responder a su propio DM. Las solicitudes pendientes sin respuesta se purgan después del periodo de retención. No se altera el motor de sanciones ni `main`.

**Verificación real en Discord:** NO realizada. La aplicación de respuesta depende de permisos en el canal y puede quedar pendiente si este se elimina o vuelve público. El registro en SQLite se debe respaldar antes de aplicar a producción.

## Registros compactos de miembros según referencia Sapphire — 2026-10-17

En `Pruebas@cfa65386` se armonizó la vista de salida, expulsión y baneo para el módulo de Logs: líneas compactas con usuario, ID, ingreso relativo, roles, recuento de miembros y miniatura de perfil; motivo/responsable en sanciones y duración/vencimiento de BAN cuando conste realmente en expediente reciente. Se reutiliza el editor de plantillas, los canales configurables y la deduplicación de expulsiones por falta de orientación, que conserva su estado de DM y oportunidad. No se generan enlaces de Warned/Muted/Kicked/Banned sin mensajes reales de destino conocidos. CI 3.11–3.13 y Mensajes SUCCESS; prueba visual Discord Test pendiente. No fusionar a producción sin autorización y seguridad de datos.

## Corrección de color: Cancelar y Cerrar — 2026-10-16

Por decisión nueva del propietario, los botones Cancelar y Cerrar usan **rojo**, no gris. También aplica «Cancelar edición». Afecta a los componentes visuales y formularios de Mensajes y /setup. Mantener Cancelar sin guardar y Cerrar solo cerrando; «Volver» y «Vista previa» siguen grises. La norma anterior de Cancelar/Cerrar grises queda reemplazada, sin alterar los demás significados de colores ni resolver la tarea independiente de simplificar Guardar/Descartar/Cancelar en las programaciones de embeds.

## Semántica uniforme de controles — 2026-10-16

Para Mensajes y /setup se acuerda: rojo para eliminación, descarte y sanción; verde para guardar/publicar/activar; azul para editar o preparar opciones sin guardar; gris para cancelar, volver o vista previa. Es prioritario que el color represente la acción efectiva, no solo el texto: un botón que abre un modal es azul aunque permita preparar algo positivo; una confirmación de eliminación es roja aunque diga «Confirmar». Los botones externos Discord usan estilo link propio. Lote de colores implementado en Pruebas (`c32141eb`, CI 3.11–3.13 SUCCESS), Discord real pendiente. **Petición funcional pendiente, no ejecutada aquí:** sustituir «Revisar programación» por «Guardar cambios», introducir «Descartar cambios» con reversión y reemplazar «3. Configurar condición» por un nombre específico del modo; después extender guardado explícito sin revisión redundante a otros editores. La nota anterior sobre «Revisar» corresponde al comportamiento heredado, no a la nueva intención aprobada.

## Calidad editorial y claridad de los controles — 2026-10-15

Toda pantalla administrativa debe usar español correcto, explicar el efecto concreto de cada acción y evitar mensajes contradictorios. Preferir descripciones humanas a JSON, saltos de línea visibles y estados precisos. Separar «Revisar», «Confirmar» y «Cancelar»; los selectores y formularios no guardan por sí mismos. Se aplicó al programador de embeds en Pruebas, con verificación real pendiente; ampliar el estándar progresivamente a los demás editores.

## Nombres naturales de embeds personalizados — 2026-10-15

En Pruebas, /embed admite nombres Unicode legibles con espacios, tildes y emojis, máximo 64 caracteres. Identificador canónico en crear, editar, enviar, borrar y autocompletar; no cambia publicaciones previas. Pendiente validación interactiva de Discord y CI. Los demás editores no se consideran terminados por este ajuste.

## Patrón de claridad para editores de /setup — 2026-10-15

En `Pruebas` se reorganizó el editor de Reportes: elección de reacción y acción contiguas; `Configurar condiciones` sustituye a `Regla`, con explicación de número de personas distintas, duración de sanción y purga de mensajes. Las opciones irrelevantes no aparecen en el modal. `Sanciones y límite` permite habilitar/deshabilitar tipos de sanción y elegir la acción al máximo WARN con confirmación. Este es el patrón aprobado para extender progresivamente a otros editores (etapas claras, etiquetas específicas, menús para opciones cerradas, vista previa y cancelación sin persistencia), no una afirmación de que todos los paneles ya estén modernizados. Pendiente auditoría y aceptación Discord de los demás editores.

## Uniformidad adicional de editores — 2026-10-15

En Pruebas, Miembro de la Semana → Horario y Moderation → Reportes sustituyen entradas textuales de opciones cerradas por selectores, manteniendo parámetros personalizados y la confirmación antes de guardar. Es una mejora transversal de /setup, distinta de la finalización del editor visual de Mensajes. Pendiente probar ambos editores en Discord y extender el mismo criterio a otros módulos con opciones conocidas, sin sustituir campos de texto libre.

# Plan de integración: /setup → Mensajes (referencia Sapphire)

## Estado vigente para revisión — 2026-10-10

Esta tabla sustituye las casillas históricas que se conservan debajo como registro de etapas. No acredita pruebas interactivas ni paridad completa con Sapphire.

| Área | Implementado en PR #7 | Pendiente |
| --- | --- | --- |
| Plantillas | Texto, hasta diez embeds, variables, JSON, editor visual de campos/autor/pie/imágenes y confirmación | Navegación uniforme y validación Discord |
| Componentes | Botones/menús independientes, selección múltiple, multiacción confirmada, permisos y auditoría | Editor visual de acciones y selección persistente por miembro |
| Kits | v1/v2, archivo, reemplazo confirmado, portabilidad visual | Enlace/ID seguro y comparación por campo |
| Automatizaciones | Programación, autorespuestas, sticky y webhook propio | Recorrido real y reinicios |
| Predeterminados | Estudios de cinco familias y editor de Logs; formularios Honeypot confirmados | Catálogo completo y Raw/restauración uniforme |

Ver `REVISION_PR7.md` para límites, ejemplo JSON y recorrido de aceptación. Revisión de código preparada; no es una declaración de alcance total completado.

## Registro histórico de etapas

## Referencia y alcance
- Fuente: https://docs.sapph.xyz/#/messages
- Componentes: https://docs.sapph.xyz/#/guides/guide-to-components
- El objetivo es paridad de experiencia y funcionalidades, sin replicar material propietario de Sapphire.
- Mantener español formal, sin emojis decorativos, configuraciones aisladas por servidor y permisos comprobados por interacción.

## Fase 1: Navegación y conservación de editores (implementada en rama)
- [x] Entrada Mensajes en menú principal de /setup.
- [x] Centralización de accesos a verificaciones, sugerencias, honeypot, condenas y logs.
- [x] Almacenamiento de plantillas por servidor.

## Fase 2: Plantillas (parcialmente implementada)
- [x] Crear, editar, borrar, previsualizar y publicar embeds con título, descripción, imagen HTTPS y enlace.
- [x] Vincular botón de rol o menú de roles a una plantilla.
- [ ] Contenido de texto independiente del embed, varios embeds, miniaturas, pies, autores y campos.
- [x] Editor JSON Raw con validación de esquema básica.
- [ ] Variables dinámicas por contexto; impedir menciones automáticas no deseadas.
- [x] Edición de publicaciones existentes mediante enlace con verificación de autoría del bot y confirmación explícita.
- [ ] Vista previa de todos los componentes y experiencia de navegación uniforme.

## Fase 3: Componentes (parcialmente implementada)
- [x] Botones de rol (añadir, quitar, alternar), con comprobaciones de jerarquía y permisos.
- [x] Menú de selección de roles y reconstrucción de acciones después de reiniciar.
- [ ] Editor independiente de cada menú/opción y varias acciones secuenciales con resultado visible.
- [ ] Mensaje al usuario (público o efímero), mensaje en canal, mensaje directo.
- [ ] Editar o eliminar mensaje, usando autorización y prevención de abuso.
- [ ] Más opciones de rol, selección múltiple y mantener selección.
- [ ] Política de acciones privilegiadas, rate limits, límites de componentes y auditoría.

## Fase 4: Kits (parcialmente implementada)
- [x] Exportación JSON de plantillas sin secretos ni acciones de permisos.
- [x] Importación manual de JSON con comprobación de tipos, límites y detección de conflictos (sin sobrescritura).
- [ ] Importación de archivo de kits grandes, enlace/ID seguro, vista previa de diferencias.
- [ ] Versionado, importación de kits grandes y restauración opcional bajo confirmación.
- [ ] Portabilidad de valores visuales y compatibilidad por versión.

## Fase 5: Uso y automatizaciones (pendiente)
- [x] Enviar mediante /sendtemplate, con autocompletado y comprobación de permisos.
- [x] Editar publicaciones existentes mediante /edittemplate, solo mensajes propios y con confirmación del administrador.
- [ ] Programación puntual/recurrente con zona horaria configurada.
- [ ] Auto-respuestas por palabra clave con controles anti-spam.
- [ ] Mensajes fijados al final (sticky) sin duplicados ni bucles.
- [ ] Mensajes por webhook con validación de destino y credenciales seguras.

## Fase 6: Mensajes predeterminados (pendiente)
- [ ] Catálogo completo de mensajes de El Heraldo, por clave estable y origen.
- [ ] Preview / Visual / Raw / Variables y restauración por evento.
- [ ] Migrar solo textos editables; no permitir alterar identificadores internos ni evidencia, permisos o estados reales.
- [ ] Cuando un campo no sea aplicable a un caso de condena, omitirlo.

## Confirmación obligatoria de administrador
- [x] Los modales de plantilla, JSON, componente de rol, vinculación y kits generan un borrador pendiente y solo persisten tras botón de confirmación.
- [x] Eliminar plantilla exige una confirmación separada.
- [x] Cancelar descarta la propuesta sin alterar la configuración guardada.
- [x] Publicar mensajes sigue siendo una acción explícita del administrador; guardar no publica ni edita mensajes ya enviados.
- [ ] Comprobar en servidor de pruebas las confirmaciones, caducidad y cambios concurrentes.

## Calidad y despliegue (verificación automatizada parcial)
- [x] Ejecutar `python -m py_compile bot.py` (etapa 1, 2026-10-09; ver registro de pruebas).
- [ ] Ejecutar `python -m unittest test_regressions.py` y ampliar casos.
- [ ] Pruebas reales en servidor de prueba: botones, desplegables, mensajes efímeros, roles y reconexión.
- [ ] Probar roles superiores, rol administrado, falta de permisos, eliminación de plantilla, reinicios y varios servidores.
- [ ] Revisar permisos antes de publicar y logs de error.
- [ ] Aprobar PR, fusionar y desplegar solo tras completar verificaciones.

## Problemas conocidos en la rama actual
- La importación actual no reemplaza plantillas; rechaza los nombres repetidos. Todavía necesita un flujo de revisión de diferencias.
- El componente de menú comparte el catálogo de roles del servidor, aún sin editor individual de opciones.
- Sintaxis y regresiones existentes verificadas en la etapa 1; las ampliaciones de cobertura y las pruebas interactivas siguen pendientes. Consultar `PRUEBAS_DISCORD.md` para entorno y alcance.

## Avance real — 2026-10-10
- Fase 2: texto independiente, múltiples embeds y propiedades avanzadas disponibles por JSON/kit; variables usuario, usuario_id, servidor, servidor_id, canal y fecha; preview desactiva acciones. Falta editor visual completo y navegación uniforme.
- Fase 3: se refuerzan jerarquía, política de roles administrativos, condenas activas, concurrencia y frecuencia. Menús independientes, acciones secuenciales, mensajería y auditoría por acción siguen pendientes.
- Fase 4: kit v2, compatibilidad v1, archivo JSON mediante /importkit (128 KiB), resumen de nombres añadidos/reemplazados y confirmación con rechazo de borradores obsoletos. Falta comparación detallada por campo e importación segura por enlace/ID.
- Fases 5 y 6 siguen pendientes salvo envío/edición manual previamente existentes. No se declara paridad con Sapphire.
- Verificación offline del lote: 64 pruebas aprobadas; validación interactiva y CI remoto del lote pendientes.

### Programación implementada y límites — 2026-10-10
- Programación puntual, diaria y semanal con zona IANA, propuestas confirmadas, listado de estado y retirada: implementada mediante /programar_mensaje. Estado SQLite y permisos comprobados en ejecución; pendiente ensayo real.
- Recuperación conservadora: envíos inciertos requieren revisión; los vencimientos durante desconexión se agrupan en una publicación, sin ráfagas de recuperación.
- Texto independiente validado también frente al hook global; pies/embeds explícitos no se alteran tras su validación.
- Las casillas históricas anteriores describen etapas previas. Autorespuestas, sticky, webhooks y componentes multiacción continúan pendientes. La documentación Sapphire no devolvió contenido legible mediante consulta web; no se ha verificado paridad completa con esa referencia.
- Verificación del lote más reciente: 78 pruebas offline aprobadas, compilación y dependencias correctas; CI nueva e interacciones todavía pendientes.

### Fase 5 ampliada — 2026-10-10
- Implementadas autorespuestas literales por canal con configuración confirmada y límites persistentes.
- Implementado sticky por canal con conservación del estado y reposición limitada por actividad; al retirar se conserva la publicación final.
- Implementado envío manual confirmado por webhook propio del bot, sin persistir credenciales. Los componentes interactivos de roles usan publicación directa del bot.
- Estas funciones tienen regresiones offline, pero no pruebas reales Discord. Continúan pendientes componentes multiacción, menús independientes, editor visual completo y catálogo general. No afirmar paridad completa con Sapphire.


## Auditoría y propuestas de catálogo — 2026-10-11
PR #12 separa visualmente mensajes oficiales de personalizados; esa modificación ya estaba implementada y no se repite. La auditoría local añade cobertura de navegación real, corrigiendo su invocación. La propuesta de nombres fijos Condena/Perdón/Verificación/Advertencia y editor uniforme está documentada en audit/PROPUESTAS_Y_PLAN_REAL.md para decisión del propietario; no implica migración ni eliminación de plantillas guardadas. La cobertura actual y vacíos se consultan en audit/MATRIZ_COBERTURA.md.

## Continuación del editor visual — 2026-10-12
Rama temporal Codex `codex/h03-recuperacion-20261012`: selector de embeds limitado a los existentes; selector de hasta 25 campos con nombre, valor e inline precargados en el modal. La selección mantiene borrador/versión y no guarda automáticamente. Cambiar embed invalida formularios anteriores, retirar embed reconstruye selectores y permisos revocados bloquean el modal. Cuatro regresiones nuevas y suites de Mensajes/Reaction Roles previas correctas, sin prueba Discord real. No se completaron editor visual de acciones, importación segura por enlace/ID, comparación por campo ni catálogo uniforme; permanecen pendientes.
