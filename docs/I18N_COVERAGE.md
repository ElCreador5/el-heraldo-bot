# Internacionalización de El Heraldo — cobertura real

**Revalidación del 27/10/2026:** aviso parcial ajustado al texto exacto vigente en inglés y portugués. 989 regresiones aprobadas y dos omisiones históricas, 44 pruebas de idioma correctas; CI Lab `40503577907` y Mensajes `40503577827` SUCCESS. `Pruebas@069c8d347968458bdababa71c8f3c36c2435153a` desplegado en worker/Lab, deployment `4ff1090b-3ba2-4ac9-bc09-e816150c215b` SUCCESS, Gateway, dos autopruebas de /setup y sincronizaciones de 51 comandos en en-US y pt-BR correctas. Recibo actual: `I18N_TEST_DEPLOYMENT.json`. El recorrido interactivo sigue pendiente: Discord avanzó al segundo factor, pero devolvió un error genérico al elegir otra verificación. Producción y H-03 conservados. Las secciones fechadas el 25/10 documentan la revisión original, no un nuevo recorrido real.

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
- GitHub Actions del commit `8d82172ed5eb41efa146f2346d982c328c9cb770`: [Lab 40226189099](https://github.com/ElCreador5/el-heraldo-bot/actions/runs/40226189099) SUCCESS (Python 3.11/3.12/3.13 y UX); [Mensajes 40226189104](https://github.com/ElCreador5/el-heraldo-bot/actions/runs/40226189104) SUCCESS. Las 952 pruebas completas y las 44 específicas también pasaron remotamente.
- El flujo antiguo [candidato de producción 40226189181](https://github.com/ElCreador5/el-heraldo-bot/actions/runs/40226189181) falla antes de sus pruebas: `Production baseline changed; reconcile before preparing candidate`. No es un fallo de i18n; reconciliar ese candidato no está autorizado en esta tarea y no se altera para ocultar su resultado.

## Aceptación que permanece pendiente

El navegador conectado no está disponible en este contexto y el navegador de pruebas muestra el inicio de sesión de Discord. No se realizaron clics reales en el servidor de laboratorio ni se aplicaron sanciones de ensayo. Las pruebas automáticas y el arranque en Railway no equivalen a esa aceptación.

Por esta razón se conservan los avisos exactos de inglés y portugués solicitados. El cierre integral y la marca de idiomas completos quedan pendientes del recorrido autenticado de Discord Test; no hay traducciones conocidas pendientes en el catálogo revisado.

## Publicación

Único destino: proyecto Railway Test `747a1ee0-cdab-4ad5-8e45-a6ddfccc9b61`, entorno Lab, servicio `worker`. Commit fijado `8d82172ed5eb41efa146f2346d982c328c9cb770`; deployment `b7c68d40-9d48-4dbb-a47f-69d3921a4795` **SUCCESS**, creado el 25/10/2026 a las 19:32:01 UTC. Gateway conectado a las 19:33:15 UTC; dos autopruebas de `/setup` y dos sincronizaciones de **51 comandos** correctas con el `en-US` guardado de sus servidores.

Volumen `85da5175-658b-4f71-9be3-d98f5573dbee` montado en `/data`, sin cambios de volumen, variables ni otra configuración del servicio. Sin migraciones ni reescritura de datos. Cron de respaldo sin modificaciones. `main` observado antes y después: `32c9f5dcc8505a3d6aacde76533d6b60dd88a542`; producción no modificada ni desplegada. Recibo reproducible: [I18N_TEST_DEPLOYMENT.json](I18N_TEST_DEPLOYMENT.json).

El arranque real acredita Gateway y sincronización en el idioma guardado; los otros dos idiomas se comprobaron mediante payloads y ejecución automática. No se presentan esas pruebas como clics reales en Discord.
