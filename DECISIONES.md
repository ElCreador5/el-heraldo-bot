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
