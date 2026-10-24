# Instrucciones compartidas para asistentes — El Heraldo

Este archivo es el punto de entrada para ChatGPT, Codex, Claude y cualquier agente que trabaje sobre este repositorio. Leer antes de tocar código.

## Fuentes de verdad
1. `ESTADO_PROYECTO.md`: estado comprobado, prioridades, pendientes y entorno.
2. `DECISIONES.md`: criterios de producto y restricciones acordadas.
3. `PRUEBAS_DISCORD.md`: cobertura, resultados y fallos reproducibles.
4. Código y pruebas automatizadas: fuente final del comportamiento implementado. Nunca asumir que una afirmación documental reemplaza la comprobación del código.
5. `PLAN_MENSAJES.md`: plan específico de Mensajes; actualizar cuando avance.

## Flujo obligatorio
- `Pruebas` es la única rama permanente de desarrollo; `main` es producción y no se modifica, fusiona ni despliega sin aprobación específica.
- **Excepción autorizada 2026-10-12:** exclusivamente Codex puede crear ramas temporales por tarea y abrir PR cuyo destino sea `Pruebas`. Revisar diferencias, conflictos, CI y posibles despliegues automáticos antes de fusionar. Eliminar ramas temporales después de integrar o descartar la tarea, verificando que no contienen trabajo pendiente. Otros agentes no crean ramas nuevas sin autorización.
- En Codex Cloud, `work` puede ser una rama interna: verificar el commit base contra `Pruebas` y registrar SHA; no exigir nombre de rama `Pruebas` ni igualdad de SHA después de introducir cambios legítimos. El script de instalación no cambia ramas, hace merge ni push.
- Cuando la interfaz de Codex no permita un flujo determinado, reconocer el límite y no inventar controles. No publicar cambios directamente en `Pruebas` mediante Codex sin nueva aprobación explícita.
- Comenzar con `git fetch` / `git pull` de la rama correcta; no sobrescribir cambios remotos ni forzar pushes.
- Usar el bot de pruebas y el servidor de laboratorio; evitar acciones de prueba en servidores reales.
- Antes de alterar una función, inspeccionar código existente, dependencias y tests; no borrar capacidades silenciosamente.
- Mantener mensajes del bot en español formal y sin emojis decorativos; usar emojis únicamente si son funcionalmente necesarios.
- Cualquier modificación de configuración debe requerir confirmación explícita del administrador; cancelar no debe guardar.
- Comprobar permisos, jerarquía de roles, aislamiento por servidor, persistencia y fallos en interacciones.
- Ejecutar compilación y regresiones; diferenciar claramente pruebas automáticas de pruebas realmente realizadas en Discord.
- Cada sesión debe finalizar con commit descriptivo, archivos afectados, pruebas realizadas, errores y próximos pasos.
- Actualizar los tres documentos de coordinación en el mismo trabajo cuando cambie su información.
- No registrar tokens, credenciales, IDs secretos, datos de usuarios, transcripciones privadas ni evidencias sensibles.
- No automatizar una cuenta personal de Discord con tokens de usuario/self-bots; preferir bot oficial y cuentas de prueba autorizadas.
- Si hay cambios concurrentes, reconciliar primero los commits y documentos relevantes sin sobrescribir ni forzar referencias; una PR ya no es obligatoria.


## NH — Flujo ágil de actualizaciones directas (decisión del propietario, 2026-10-20)

**Este apartado actualiza y prevalece sobre las antiguas exigencias administrativas de PR, revisión externa y checks obligatorios para actualizaciones normales del código.** El propietario optó por un flujo sencillo y directo, manteniendo controles técnicos proporcionales al riesgo.

- **`main` y `Pruebas` siguen siendo las únicas ramas permanentes.** Se puede actualizar directamente `main` si el propietario autorizó expresamente el cambio concreto; no exigir otra confirmación por el mismo alcance. `Pruebas` se usa para trabajos que necesiten ensayos o para los que el propietario elija desarrollar allí.
- **Sin PR obligatoria, sin ramas temporales ni checks requeridos como condición de publicación.** La regla activa de GitHub para `main` prohíbe borrar la rama o hacer actualizaciones no fast-forward. La ejecución automática de tests no se elimina, pero sus resultados se deben verificar, documentar y corregir si fallan; no asumir que SUCCESS significa prueba real en Discord.
- **Mantener revisión técnica mínima:** comprobar HEAD/SHA fresco y cambios concurrentes, leer el código afectado, conservar funcionalidades y comprobar sintaxis/regresiones relevantes. Corregir defectos sin incorporar toda la rama `Pruebas` ni funciones no autorizadas.
- **Preservar SQLite y datos privados:** una modificación de logs/interfaz sin migraciones ni cambios de esquema puede publicarse directamente; migraciones, acciones destructivas, secretos y activaciones del sistema H-03 exigen respaldo recuperable y las comprobaciones específicas correspondientes. No convertir la simplificación de GitHub en un permiso para destruir datos.
- **Producción:** considerar el despliegue automático de Railway al escribir en `main`, comprobar el estado real del despliegue, errores y pruebas. Informar lo implementado, lo probado y cualquier límite real; no prometer comportamiento verificado en Discord antes de comprobarlo.
- Esta decisión **no suprime** el requisito de autorización específica del propietario para cambios de producción: una autorización anterior al mismo objetivo sigue válida sin repetir preguntas. Nunca usar force push.

## Conservación de funcionalidades estables de producción (decisión del propietario, 2026-10-12)
- Toda funcionalidad que ya funciona correctamente en `main` se conserva en `Pruebas` sin rediseño ni reimplementación innecesaria.
- Una ausencia de nueva prueba manual no constituye por sí sola un fallo. Comparar primero comportamiento y código de ambas ramas antes de abrir trabajo sobre funciones existentes.
- Modificar una función estable únicamente por petición del propietario, anomalía que observe posteriormente o defecto técnico/de seguridad demostrado. Documentar evidencia, alcance y regresión asociada.
- Si un cambio de `Pruebas` rompe una función estable de `main`, restablecer el comportamiento esperado salvo que el propietario haya autorizado expresamente otro.
- Priorizar cambios realmente nuevos y diferencias comprobadas, conservando interfaces, datos y configuraciones existentes.

## Precisión operativa y respeto al tiempo del propietario (obligatorio)
A partir de ahora, para El Heraldo y cualquier herramienta que utilicemos, todos los agentes seguirán estos criterios:

1. **Verificar antes de instruir.** No indicar botones, menús ni procedimientos sin fundamento.
2. **Distinguir hechos de suposiciones.** Si no se puede comprobar algo, decirlo claramente.
3. **Evitar pasos innecesarios.** Priorizar el procedimiento más directo y seguro.
4. **Respetar el tiempo del propietario.** No pedir capturas o comprobaciones que el agente pueda resolver por su cuenta.
5. **Asumir la coordinación técnica.** El propietario define qué quiere conseguir; los agentes organizan correctamente el trabajo y señalan las decisiones que realmente requieren su autorización.

Estas cinco reglas se aplican a ChatGPT, Codex, Claude, Work y cualquier otro agente del proyecto.

## Normas Heraldo (NH) — nombre oficial y uso obligatorio (decisión del propietario, 2026-10-19)

**Nombre oficial:** **Normas Heraldo**. **Abreviatura:** **NH**. Este nombre designa exclusivamente los estándares internos de desarrollo, diseño, interfaz, configuración, seguridad, funcionamiento, verificación y calidad del bot **El Heraldo**. **No** significa las reglas de convivencia de un servidor de Discord ni las políticas o acciones de moderación que el bot aplica a sus miembros.

**Fuente normativa única:** «NH» es el nombre corto para invocar el **Contrato transversal de interfaz y controles de aceptación** de este archivo (`UX-01` a `UX-05`, incluida `UX-03A`) junto con las decisiones específicas vigentes de `DECISIONES.md` y las demás restricciones de este `AGENTS.md` que correspondan al trabajo. Los identificadores `UX-*` se conservan como referencias técnicas: no duplicar ni renumerar el reglamento, ni crear documentos paralelos. En caso de contradicción, contrastar las decisiones y fechas y pedir aclaración al propietario cuando sea necesario.

**Comandos en lenguaje natural**, válidos para ChatGPT, Codex, Claude y agentes que lean este archivo:
- **«Aplica NH» / «Aplica Normas Heraldo»**: aplicar los estándares al trabajo o módulo indicado en el contexto actual; revisar antes de editar, respetar lo ya funcional y añadir las regresiones pertinentes.
- **«Aplica NH en [módulo o función]»**: limitar la aplicación y auditoría a ese alcance, incluidas sus dependencias necesarias.
- **«Aplica NH en todo el bot»**: realizar auditoría transversal y plan de corrección por etapas de todos los módulos; documentar cobertura y pendientes. No declarar que todos cumplen las normas sin verificarlos ni realizar una reescritura masiva innecesaria.
- **«Audita NH»**: informar cumplimiento, infracciones demostradas, cobertura de pruebas y verificaciones pendientes. La auditoría por sí sola no autoriza cambios.
- **«Añade a NH: [nueva regla]»**: verificar compatibilidad con las decisiones existentes y, con la aprobación del propietario, registrar la norma en el apartado pertinente de este contrato, añadir o actualizar regresiones y anotar la decisión cuando cambie un acuerdo vigente.
- **«Actualiza NH»**: modificar una regla previamente aprobada solo conforme a la nueva decisión del propietario, preservando trazabilidad y pruebas.

**Límites invariables:** invocar NH por sí solo no autoriza cambios en `main`, pero sí puede aplicarse allí cuando el propietario lo haya autorizado; no autoriza omitir respaldos o controles **necesarios según el riesgo**, confirmaciones de configuración administrativa ni pruebas relevantes, acceder a datos privados o declarar verificación real en Discord sin realizarla. Se aplica el flujo ágil de 2026-10-20 sin volver a exigir PR ni checks bloqueantes.

## Contrato transversal de interfaz y controles de aceptación (obligatorio, 2026-10-19)

**Alcance:** TODOS los paneles de `/setup`, embeds, vistas, modales, selectores, menús y botones del bot, incluidos módulos futuros. Regla de producto vinculante para ChatGPT, Codex, Claude y cualquier agente que escriba o audite código. No reemplaza las decisiones detalladas de `DECISIONES.md`, ni permite retirar funciones o cambiar producción. Cuando una regla general choque con una excepción específica vigente, documentar la discrepancia, verificar el código y respetar la decisión específica más reciente; preguntar al propietario si sigue siendo ambigua.

### UX-01 — Cambios solo tras confirmación explícita
- Selectores, fechas, horas, menús, modales y controles que preparan configuración modifican **únicamente el borrador**. Ni SQLite ni mensajes publicados ni configuración activa se actualizan hasta **Guardar cambios** o confirmación equivalente explícita.
- Guardar vuelve a comprobar permisos y jerarquía, estado actual, integridad de valores y versión del borrador; no informa éxito sin persistencia confirmada. Deshabilitar Guardar si no hay nada que guardar cuando sea posible.
- **Única excepción de persistencia inmediata (24/10/2026):** los botones explícitos **Activar**, **Pausar** y **Reanudar** guardan inmediatamente **solo el estado propio** de activación/pausa que representan, sin exigir **Guardar cambios** ni abrir confirmación rutinaria adicional. **Jamás arrastran otros campos pendientes** (canales, roles, sanciones, plazos, selectores, textos o medidas); estos siguen siendo borradores. El resultado se refleja en el mismo embed/panel. Antes de activar o reanudar, revalidar permisos, protección configurada y dependencias **ya guardadas**; si faltan, no activar y explicar el motivo en el mismo panel. El clic duplicado o sobre un panel desactualizado no puede sobrescribir otro estado. No extender el guardado inmediato a otros botones como Descartar, Desactivar o Retirar sin aprobación específica del propietario.
- **Confirmación breve sin navegación redundante (2026-10-24):** cuando **Guardar cambios** abre una confirmación intermedia de configuración, evitar repetir en esa pantalla los botones **Descartar cambios** y **Volver** del editor original. **Confirmar cambios** ejecuta una vez, edita el mismo mensaje y devuelve automáticamente al submenú anterior con el estado guardado actualizado; allí permanecen los controles normales de edición, **Descartar cambios** y **Volver**. La confirmación intermedia no debe quedar visible después del éxito. Mantener excepciones justificadas cuando se requiera una salida segura antes de una operación irreversible; no retirar los controles de seguridad de sanciones u otras operaciones críticas.
- **Sin doble guardado ni mensajes superfluos (2026-10-24):** los desplegables, selectores y formularios de configuración son solo borradores. **Guardar cambios** persiste directamente una configuración reversible y segura. Únicamente cuando una acción tenga efectos sensibles (retirar la última protección, crear o borrar recursos, publicar, sancionar, purgar) se exige **Confirmar cambios** explícito. Siempre que la API permita, confirmar, descartar, informar errores y mostrar el resultado editando el mismo panel de `/setup`, sin enviar tarjetas efímeras adicionales para cada paso. Una confirmación no constituye un segundo guardado: se revalidan permisos y estado y se ejecuta una sola vez.
- Tras cada guardado, el embed visible debe regenerarse a partir del **estado persistido real** (no de una instantánea anterior): cantidades y listas coherentes, incluido **0 · Ninguno configurado** al retirar el último recurso. `Descartar cambios` jamás persiste. La selección de un control nunca desactiva protecciones por sí misma. Aplicación transversal a TODOS los settings y módulos, actuales y futuros.
- **Cancelar**, **Cerrar** y **Descartar cambios** nunca guardan; descartan según su contexto y no ejecutan la acción. **Volver** navega sin guardar; se conserva el borrador durante la navegación cuando el flujo lo requiera, sin persistirlo por accidente.
- Acciones administrativas de efecto inmediato (publicar, sancionar, crear/retirar, fusionar, purgar) exigen su propia confirmación explícita, con revalidación justo antes de ejecutar. No convertir la selección de un menú en ejecución.
- Controlar concurrencia, caducidad, cierres, interacciones repetidas, revocación de permisos y fallos parciales.

### UX-02 — Paleta de botones según acción EFECTIVA
- `discord.ButtonStyle.success` (verde): Guardar, **Confirmar cambios** después de una propuesta revisada, Confirmar acciones positivas, Publicar y Activar **cuando realmente ejecutan** una acción autorizada. En la confirmación de retirada de canal trampa, **Confirmar cambios es verde**; el control previo **Retirar canal** continúa rojo. Las confirmaciones tituladas `Eliminar`, `Banear` o similares conservan el rojo de operación destructiva.
- `discord.ButtonStyle.danger` (rojo): Cancelar, Cerrar, Descartar, Eliminar, Retirar, Desactivar, sancionar y **confirmar** operaciones destructivas. Cancelar y Cerrar son rojos incluso si solo cierran el editor, conforme a la decisión del 16/10.
- `discord.ButtonStyle.primary` (azul): Configurar, Editar y abrir un subpanel/modal o una confirmación **sin ejecutar** cambios todavía. Ejemplo: Crear canal que solo prepara confirmación.
- `discord.ButtonStyle.secondary` (gris): Volver, Vista previa y consultas neutrales sin mutación.
- El color debe corresponder al callback real, no solo al texto del botón. Para acciones de estado variable, actualizar el estilo dinámicamente. Los botones de enlace usan el estilo de Discord. Los selectores no tienen colores equivalentes: su comportamiento sigue UX-01.

### UX-03 — Pantallas precisas y consistentes
- Embeds en español formal, lenguaje uniforme, sin emojis decorativos (solo emojis funcionales para reacciones). Mostrar estado guardado, selección actual, opciones y cambios pendientes, distinguiéndolos visualmente.
- No mostrar campos sin aplicación al caso, opciones ficticias, mensajes de confirmación repetidos, avisos ruidosos ni datos vacíos. Mantener el diseño actual de los expedientes cuando se modifique una función cercana.
- Nombres de opciones comprensibles; los desplegables solo presentan acciones soportadas y aplicables, con validación de entradas personalizadas y límites de Discord.
- Las acciones sensibles requieren vista previa fiel cuando corresponda; explicar origen/destino, orden, alcance y consecuencias reales, sin prometer operaciones que la API no realiza (por ejemplo, fusionar mensajes como traslado nativo).
- Centralizar configuraciones administrativas en `/setup` cuando proceda en lugar de proliferar comandos slash; conservar accesos existentes hasta que el propietario autorice retirarlos.

### UX-03A — Ayuda contextual dentro de selectores y desplegables (obligatoria, 2026-10-19)
- **Siempre** que un panel ofrezca un selector o desplegable de configuración, debe contener orientación para administradores sin experiencia **dentro del propio control**, preferentemente en el `placeholder` y, para `discord.ui.Select` con opciones definidas, en la `description` de cada opción cuyo significado, efecto o riesgo pueda generar dudas. La etiqueta identifica la opción; la descripción explica **qué hace** y **cuándo elegirla**. Cada opción debe poder entenderse sin leer un manual.
- Los textos serán breves, concretos, en español formal y sin tecnicismos ni emojis decorativos. Usar una frase práctica, por ejemplo `Solo registrar — Registra el incidente sin sancionar ni borrar mensajes` o `Condenar — Aplica la condena configurada al confirmar` (el ejemplo no cambia acciones reales). Aclarar requisitos, alcance o consecuencias únicamente si ayudan a elegir con seguridad.
- Respetar los límites reales de Discord para `placeholder`, `label` y `description`; evitar truncamientos que eliminen el significado. No inventar capacidades ni descripciones de opción en selectores nativos de rol, canal, miembro o mención (`RoleSelect`, `ChannelSelect`, etc.): cuando la API no permita descripciones por opción, ofrecer instrucciones breves y claras en el **placeholder del propio selector**.
- **Jerarquía visual:** los mensajes de estado, errores, permisos, avisos de seguridad, borradores y confirmaciones importantes tienen prioridad. La ayuda no debe competir con ellos, ocupar el cuerpo principal de un embed, crear mensajes de chat/DM adicionales, repetirse en cada interacción ni ocultar información esencial. No añadir selectores artificiales solo para mostrar ayuda.
- La ayuda es informativa y **nunca** activa, guarda ni confirma acciones. Debe concordar con los callbacks, permisos y opciones vigentes: si cambia el funcionamiento, actualizar la descripción y su regresión. Al crear/modificar un selector, comprobar la utilidad real de sus textos y su presentación en pruebas sin Gateway; validar visualmente en Heraldo's Lab cuando corresponda.
- La regla se aplica a todos los módulos y submenús de `/setup`, actuales o nuevos, y a otros editores administrativos del bot. Los selectores ya existentes se adaptarán durante su revisión; incorporar esta norma al contrato NO significa que todos estén actualizados ni probados todavía.

### UX-03B — Botones compactos, filas equilibradas y navegación «Volver» (obligatoria, 2026-10-21)
- **Alcance transversal:** todos los módulos y submenús de `/setup`, y los editores administrativos relacionados, presentes y futuros. Conservar las funciones y las etiquetas aprobadas; **la única etiqueta de navegación de regreso es exactamente `Volver`**, sin «a /setup», nombres de secciones ni adornos.
- **Proporciones:** usar botones de tamaño visual compacto o regular, sin filas visiblemente desproporcionadas. Los botones clásicos de Discord no permiten establecer ancho arbitrario: ajustar con textos concisos cuando su etiqueta no esté fijada por el propietario, agrupación por función y distribución por filas. No inventar parámetros de ancho ni prometer alineación píxel a píxel.
- **Distribución:** agrupar primero controles relacionados (edición y consulta, activación/medida, confirmación/descartar/navegación), mantener filas visualmente equilibradas, evitar una fila saturada de etiquetas largas y otra casi vacía cuando haya espacio viable. Respetar máximo cinco botones por fila, cinco filas de componentes en total y los selectores existentes; no ocultar ni suprimir funcionalidades para lograr simetría. Ajustar los componentes dinámicos y vistas secundarias, no solo decoradores estáticos.
- **Regreso correcto:** `Volver` debe reconstruir el **submenú inmediatamente anterior por el que se entró**, no saltar al inicio de `/setup` desde una pantalla secundaria. Únicamente desde un módulo abierto directamente desde el inicio regresa a ese inicio. La navegación no guarda ni ejecuta efectos; tratar borradores sin pérdida silenciosa conforme a UX-01.
- **Aceptación:** añadir regresiones generales de etiquetas, rutas de regreso, filas y componentes dinámicos; construir las vistas sin Gateway y revisar visualmente con El Heraldo Test y Heraldo's Lab. Registrar excepciones causadas por los límites reales de Discord. NO afirmar que toda la interfaz está adaptada sin comprobar el código y las pruebas.

### UX-04 — Funcionamiento real y resiliencia
- Revalidar permisos del usuario y del bot y jerarquía de roles en **cada interacción y antes de guardar/ejecutar**, incluidos canales borrados y permisos revocados; comunicar el error específico sin fingir éxito.
- Reconocer oportunamente las interacciones (defer cuando corresponda), re-registrar vistas persistentes con identificadores válidos tras reinicios y no duplicar botones, logs ni sanciones; conservar los avisos obligatorios de verificación.
- Preservar aislamiento por servidor, configuración SQLite vigente y funcionalidad histórica. No modificar módulos estables solo para uniformar estilos sin comprobación del comportamiento y cobertura de regresión.

### UX-05 — Puerta de aceptación: NUNCA aprobar solo por apariencia
1. **Antes:** leer `AGENTS.md`, `DECISIONES.md`, estado, pruebas y código del flujo afectado; comparar con conducta previa. Asegurar rama/SHA remoto y efecto posible de Railway Test de publicar en `Pruebas`.
2. **Durante:** probar todos los callbacks afectados (botones, selectores y modales): abrir, editar, guardar, reabrir, cancelar, descartar, volver, permisos revocados, selección inválida, confirmación duplicada, borrador obsoleto y reinicio cuando aplique. Una selección no debe alterar SQLite; una cancelación no debe ejecutar ni persistir.
3. **Después:** ejecutar compilación y regresiones existentes y **añadir o extender prueba que falle con el defecto corregido**. Integrar en CI; no saltarse pruebas para dar verde. Si CI no cubre la función, marcar cobertura PENDIENTE, no darla por aprobada.
4. **Discord:** las pruebas automáticas no prueban interacciones reales; anotar `VERIFICADO EN DISCORD` solo para recorridos ejecutados en El Heraldo Test/Heraldo's Lab y documentar lo pendiente.
5. **Informe:** indicar por funcionalidad IMPLEMENTADO / VERIFICADO AUTOMÁTICAMENTE / VERIFICADO EN DISCORD / DETECTADO / PENDIENTE, SHA, archivos, comandos, resultados, riesgos y efecto de desplegar. Si falta una prueba obligatoria, el estado es **NO APROBADO o PENDIENTE**; nunca "terminado" por suposición.
6. **Propagación:** si se descubre un defecto de regla transversal, identificar los otros paneles susceptibles, añadir regresión general reutilizable y corregir el alcance autorizado sin reescribir funciones que ya funcionan.
7. **Puerta técnica:** las pruebas de interfaz y de borradores deben ejecutarse dentro de GitHub Actions para `Pruebas`. Los checks se ejecutan como verificación informativa y no bloqueante; cualquier fallo exige revisión y corrección, pero no restablecer por defecto restricciones administrativas. No proclamar bloqueo técnico si no se configuró realmente.

**Criterio de cierre:** ninguna interfaz se declara terminada con botones muertos, guardados implícitos, cancelaciones persistentes, inconsistencia de colores, duplicados o pruebas faltantes sin registrar expresamente el problema y detener su aceptación.

## Cierre preventivo antes de agotar créditos o contexto (obligatorio)
- **No esperar a quedarse sin créditos, tokens, mensajes, tiempo de ejecución ni contexto** para preparar el informe de continuidad. La preservación del trabajo tiene prioridad sobre empezar otra tarea.
- Cuando el consumo sea visible, reservar margen para guardar cambios, ejecutar las verificaciones posibles, crear commits, actualizar documentos y entregar el informe; usar como referencia preventiva iniciar el cierre antes del 80 % del presupuesto consumido, sin tratarlo como un cálculo fiable cuando no se conoce el límite.
- Si la plataforma no informa los recursos restantes, producir puntos de control periódicos y documentar avances durante tareas largas. Ningún agente debe fingir conocer el crédito disponible.
- Ante una limitación próxima o un corte probable: detener nuevas tareas, preservar lo realizado, registrar trabajo incompleto, errores y pruebas pendientes, y **entregar inmediatamente el informe de transferencia**.
- Guardar el informe en el repositorio o registro compartido cuando haya permisos y autorización. Si no es posible, entregarlo en la conversación como texto copiable e indicar expresamente que no quedó persistido.
- El informe anticipado debe incluir: proyecto y rama, objetivo, cambios reales, commits, resultados de pruebas (separando automatizadas y Discord), errores y riesgos, archivos guardados o sin confirmar, tareas pendientes, estado exacto al interrumpir y pasos concretos para el siguiente agente.
- Nunca declarar guardados, commits o pruebas que no se hayan ejecutado. No añadir credenciales ni datos privados a los registros.
- **Principio:** es preferible interrumpir una implementación y preservar su estado a perder el progreso por agotar la sesión.

## Informe de cierre (plantilla)
**Rama y commit:** ...
**Objetivo:** ...
**Cambios:** ...
**Verificación automática:** comandos y resultados ...
**Verificación real en Discord:** acciones y resultados, o «no realizada» ...
**Errores / riesgos:** ...
**Documentos actualizados:** ...
**Siguiente paso:** ...

Estado inicial documentado el 2026-10-08. Estas instrucciones se aplican también a agentes que operen desde otra cuenta o sesión si tienen acceso al repositorio.
