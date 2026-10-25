# Internacionalización de El Heraldo — cobertura real

Revisión de `Pruebas`, 25 de octubre de 2026. Base: `b7b177b3abd422bee9b1fc4605de175eac15e4a7`. No se modifica `main` ni producción.

## Estado comprobado

**Implementación transversal validada automáticamente y revisión editorial completa; aceptación interactiva en Discord pendiente de autenticación.** No se acredita el 100 % de los recorridos ni se retiran los avisos de desarrollo.

- **3118 claves** compartidas por `es-419`, `en-US` y `pt-BR`; mismas variables, revisión editorial explícita completa y **cero claves en cola editorial**. `locales/reviewed.json` conserva los pares revisados. Las propuestas iniciales fueron reemplazadas o revisadas; el bot no carga modelos ni consulta traductores en ejecución.
- **3107 claves referenciadas** en código o esquema nativo; la existencia de claves adicionales de reserva no se usa como prueba de cobertura. La auditoría comprueba uso real, no solo paridad de catálogos.
- **181 exenciones técnicas** identificadas por archivo, ámbito y texto. Incluyen identificadores, parsers, nombres reales de recursos, contratos de API y herramientas de mantenimiento; no autorizan nuevas cadenas arbitrarias.
- **51 comandos raíz y 242 campos nativos** de descripciones/opciones examinados a partir del árbol real de Discord. Traducción por servidor, payload independiente, máximo de 100 caracteres, nombres/parámetros/valores/permisos inalterados. No se usa la preferencia personal del cliente.

## Módulos cubiertos por la implementación

| Área | Presentación y comprobaciones |
| --- | --- |
| `/setup`, submenús, `/language` | Selector, etiquetas, descripciones, ayudas, botones y preferencia compartida. Seleccionar no guarda; Guardar persiste y actualiza la ayuda nativa de ese servidor. Conflictos de idioma usan la preferencia vigente. |
| AutoMod y Honeypot | Paneles, avisos, formularios, sanciones, borradores, permisos y errores; activación y confirmaciones anteriores conservadas. |
| Moderación, condenas y advertencias | Sanciones, casos, historial, resoluciones, mensajes privados y clasificación de registros por clave canónica. |
| Verificación de edad y personalidad | Paneles, modales, avisos y recuperación, incluida la variante de elección bloqueada. Estados internos y alias técnicos no se traducen. |
| Protección antirraid | Configuración, alertas, resúmenes, acciones, nombres de perfiles y unidades de tiempo localizadas con los mismos valores internos y límites numéricos. |
| Roles de ingreso y por reacción | Editores, selectores y formularios; valores visibles convertidos a los identificadores históricos. Corrección del español residual y de ayudas mezcladas con inglés. |
| Registros, expedientes, reportes y evidencias | Etiquetas, referencias y mensajes; evidencia literal, motivos personalizados y nombres reales intactos. |
| Mensajes, plantillas y componentes | Editores de texto, embeds, botones, menús, campos, autor, pie, importación/exportación y ayudas. |
| Automatizaciones | Programaciones, respuestas automáticas, sticky, webhooks y avisos recuperan el servidor antes de generar texto. |
| Modo Custodio | Preferencias, acciones por reglas/tipos, reportes, errores y controles; los cambios de idioma externos no rompen la selección ni el estado de los botones. |
| DMs y actividad | Origen por servidor/fila persistida; recuperación y comentarios de salida. Anuncio automático de Miembro de la Semana con plural portugués verificado. |

## Contratos preservados

- Preferencia SQLite única. No se usa `interaction.locale` ni `interaction.guild_locale` como configuración del bot.
- Los desplegables administrativos no guardan; Guardar, descartar, permisos, confirmaciones sensibles y navegación NH conservan su función.
- La sincronización de comandos de un servidor no modifica el árbol global ni otros servidores. Si falla, el idioma queda guardado y el mismo panel permite reintentar; no hay mensajes de confirmación adicionales.
- IDs, parámetros de API, comandos, valores internos, nombres existentes, evidencia y textos personalizados permanecen intactos. Los nombres predeterminados de canales usados para búsqueda/creación se separan de sus etiquetas funcionales traducidas; la regresión evita introducir traducciones en esos nombres técnicos.
- Concatenaciones y uniones resuelven solo textos propios etiquetados. No se traducen cadenas libres aunque coincidan con una plantilla predeterminada.
- Pie de Test exactamente `El Heraldo's Labs 🧪`, con el icono real del servidor. No se reescribe configuración de pies ni de plantillas guardadas.
- **193 sentencias SQL de `bot.py` sin cambios** frente a la base. Sin migración de esquema ni modificación de reglas o límites de sanciones. Los parsers solo añaden equivalentes lingüísticos de unidades y entradas ya admitidas.

## Verificación automática

- **40 pruebas `test_i18n*`**, más **4 pruebas de contrato de idioma**, incluidas en la suite completa.
- Claves faltantes, variables incompatibles, nuevos literales visibles (incluidos textos cortos y f-strings), marcadores de Discord, enlaces, comandos y nombres propios.
- Nueve módulos principales × tres idiomas y **38 constructores/modos de paneles × tres idiomas**, sin escrituras al abrir. Serialización real de botones, selectores y modales, submenús de Mensajes y callbacks.
- Guardado/descartar, paneles obsoletos, concurrencia, permisos y aislamiento por servidor. Textos personalizados y citas literales preservados.
- DMs automáticos y formularios persistentes con su servidor de origen. Plurales y roundtrip de unidades/entradas en los tres idiomas; límites de duración conservados.
- Esquema real de comandos: todos sus campos usan catálogo; agregar o cambiar una descripción/opción sin registro falla. Payloads concurrentes de dos servidores no se contaminan ni alteran IDs/valores. Seleccionar idioma no sincroniza ni guarda; Guardar actualiza solo el origen y admite reintento.
- Suite `tests`: **952 pruebas, 950 aprobadas y 2 omisiones existentes**. Raíz: **39 aprobadas**. Total: **989 aprobadas y 2 omitidas**. Compilación, gramática Python 3.11, `pip check` y `git diff --check` correctos.
- Las regresiones AST históricas usan una vista semántica española; **las pruebas nuevas de i18n inspeccionan y ejecutan el código y los payloads reales**, sin esa adaptación.
- GitHub Actions incluye la auditoría y las pruebas específicas, además de regresiones en Python 3.11/3.12/3.13. Los resultados remotos del commit se registran tras publicarlo.

## Aceptación que permanece pendiente

El navegador conectado no está disponible en este contexto y el navegador de pruebas muestra el inicio de sesión de Discord. No se realizaron clics reales en el servidor de laboratorio ni se aplicaron sanciones de ensayo. Las pruebas automáticas y el arranque en Railway no equivalen a esa aceptación.

Por esta razón se conservan los avisos exactos de inglés y portugués solicitados. El cierre integral y la marca de idiomas completos quedan pendientes del recorrido autenticado de Discord Test; no hay traducciones conocidas pendientes en el catálogo revisado.

## Publicación

Único destino: proyecto Railway Test `747a1ee0-cdab-4ad5-8e45-a6ddfccc9b61`, entorno Lab, servicio `worker`. Se fija el commit validado, conservando el volumen `/data` y sus datos. El recibo con SHA, despliegue, arranque, Gateway y sincronización se registra en `docs/I18N_TEST_DEPLOYMENT.json` después de verificarlo. No se crea otro servicio ni se toca producción.
