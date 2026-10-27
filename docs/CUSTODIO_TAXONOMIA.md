# Modo Custodio — taxonomía de conductas y viabilidad

Investigación pública: 27/10/2026. Versión inicial 1.0.0, ampliable mediante fichas revisadas y pruebas; no hay un tope de categorías del producto. Cada entrada tiene ID estable. La fuente estructurada completa es [custodio_taxonomy.json](../data/custodio_taxonomy.json).

Los ejemplos son sintéticos, no gráficos y no describen personas reales. «Posible caso» supone una regla compatible y no acredita una infracción. Las políticas oficiales aportan definiciones; los estudios aportan límites; los testimonios públicos solo motivan casos. Los criterios y umbrales locales son decisiones de implementación que deben evaluarse en su propio conjunto de pruebas. No se extrapolan porcentajes de otros trabajos ni se usan identidades, idiomas o nacionalidades como señales de culpabilidad.

La asignación debe comprobar una restricción afirmativa, cita literal, versión, ámbito y excepciones. Una categoría por sí sola no activa nada. Toda señal permanece provisional; casos semánticos complejos sin detector fiable quedan para revisión humana. No se llama al proveedor para vigilar cada mensaje. No se descargan archivos arbitrarios ni se leen DMs. Los eventos de reacciones, componentes ajenos, foros, hilos y ediciones no se anuncian como soportados por la ruta actual.

## Fuentes y nivel de evidencia

- **discord_guidelines**, oficial: [https://discord.com/guidelines](https://discord.com/guidelines). Familias de conductas y límites de plataforma; no valida la eficacia de detectores.
- **discord_automod**, oficial/técnica: [https://docs.discord.com/developers/resources/auto-moderation](https://docs.discord.com/developers/resources/auto-moderation). Eventos, palabras, spam, menciones, exenciones y límites técnicos; no es comprensión semántica universal.
- **discord_harassment**, oficial: [https://discord.com/safety/bullying-harassment-threats-policy-explainer](https://discord.com/safety/bullying-harassment-threats-policy-explainer). Definiciones de hostigamiento, intimidación y amenazas; la intención no se deduce de una coincidencia léxica.
- **context_study**, estudio primario: [https://aclanthology.org/2024.lrec-main.740/](https://aclanthology.org/2024.lrec-main.740/). El contexto importa y su incorporación también plantea dificultades; no extrapolar métricas a es-419/pt-BR.
- **use_mention_study**, estudio primario: [https://aclanthology.org/2024.naacl-long.331/](https://aclanthology.org/2024.naacl-long.331/). Citas y contradiscurso pueden disparar falsos positivos, incluso en modelos recientes.
- **moderator_experience**, experiencia pública ilustrativa: [https://www.reddit.com/r/ModSupport/comments/nzoyfa/automods_roll_out_aka_tips_from_rmodsupport/](https://www.reddit.com/r/ModSupport/comments/nzoyfa/automods_roll_out_aka_tips_from_rmodsupport/). Revisión de enlaces de dominios no aprobados; no demuestra que una URL sea spam.
- **edited_link_experience**, experiencia pública ilustrativa: [https://www.reddit.com/r/ModSupport/comments/1romj62/heads_up_new_spam_technique_where_links_are_added/](https://www.reddit.com/r/ModSupport/comments/1romj62/heads_up_new_spam_technique_where_links_are_added/). Ediciones tardías como caso de evasión; no se recopilan usuarios ni conversaciones.

No se accedió a espacios privados ni se copiaron conversaciones o perfiles. La investigación no obtuvo evidencia suficiente adicional de X/Instagram para justificar criterios nuevos; no se simula esa consulta ni se necesita iniciar sesión.

## Fichas

Las fichas describen viabilidad y limitaciones. `planned_signal` todavía exige implementación/evaluación; `existing_signal` se refiere solo al mecanismo, no a aceptación interactiva ni sanciones. Las métricas reproducibles se añaden después de ejecutar el corpus local; no se inventan cifras.

### `exact_text` — Repetición textual

**Familia/versión:** spam / 1.0.0. **Capacidad:** objetiva/determinista (señal). **Estado:** `existing_signal`.

**Descripción/señal:** Mismo autor y huella textual repetida dentro de una ventana. **Regla necesaria:** Prohibición o restricción afirmativa vigente de repetición textual, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** El mismo anuncio se publica tres veces en pocos segundos. **Caso legítimo:** Varias personas felicitan a un miembro una vez cada una.

**Contexto, excepciones y polisemia:** Una repetición puede ser una corrección o un reenvío solicitado; «spam» también es una marca de alimento. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** repeat. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Varias personas felicitan a un miembro una vez cada una. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod.

### `near_text` — Mensajes casi idénticos

**Familia/versión:** spam / 1.0.0. **Capacidad:** heurística/contextual (señal). **Estado:** `existing_signal`.

**Descripción/señal:** Huellas aproximadas próximas, longitud parecida y reiteración del propio actor. **Regla necesaria:** Prohibición o restricción afirmativa vigente de mensajes casi idénticos, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** El mismo anuncio cambia solo un número. **Caso legítimo:** Respuestas de soporte que comparten una plantilla pero resuelven preguntas distintas.

**Contexto, excepciones y polisemia:** La similitud léxica no demuestra intención de molestar ni equivalencia semántica. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** similar_text. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Respuestas de soporte que comparten una plantilla pero resuelven preguntas distintas. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod.

### `repeated_links` — Enlaces repetidos

**Familia/versión:** spam / 1.0.0. **Capacidad:** objetiva/determinista (señal). **Estado:** `existing_signal`.

**Descripción/señal:** El propio actor repite destinos de enlaces en un periodo limitado. **Regla necesaria:** Prohibición o restricción afirmativa vigente de enlaces repetidos, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Un mismo enlace se insiste en varias publicaciones. **Caso legítimo:** Dos participantes citan una documentación común.

**Contexto, excepciones y polisemia:** Una URL puede ser documentación, cita, promoción autorizada o publicidad; no clasificar por dominio aislado. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** links. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Dos participantes citan una documentación común. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod, moderator_experience.

### `character_flood` — Saturación de caracteres

**Familia/versión:** spam / 1.0.0. **Capacidad:** objetiva/determinista (señal). **Estado:** `planned_signal`.

**Descripción/señal:** Secuencia extraordinariamente larga de un mismo carácter. **Regla necesaria:** Prohibición o restricción afirmativa vigente de saturación de caracteres, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Una publicación contiene cientos de letras iguales. **Caso legítimo:** Una palabra alargada de celebración.

**Contexto, excepciones y polisemia:** La longitud es verificable; la intención de interrumpir requiere contexto y prohibición expresa. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** character_flood. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Una palabra alargada de celebración. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod.

### `emoji_flood` — Saturación de emojis

**Familia/versión:** spam / 1.0.0. **Capacidad:** heurística/contextual (señal). **Estado:** `planned_signal`.

**Descripción/señal:** Carga extraordinaria de símbolos emoji en una publicación. **Regla necesaria:** Prohibición o restricción afirmativa vigente de saturación de emojis, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Un mensaje ocupa la pantalla con emojis repetidos. **Caso legítimo:** Un saludo con tres emojis o una celebración permitida.

**Contexto, excepciones y polisemia:** No confundir escrituras no latinas, símbolos matemáticos y secuencias normales con abuso. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** emoji_flood. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Un saludo con tres emojis o una celebración permitida. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod.

### `fragmented_posts` — Fragmentación excesiva

**Familia/versión:** spam / 1.0.0. **Capacidad:** heurística/contextual (señal). **Estado:** `existing_signal`.

**Descripción/señal:** Ráfaga de publicaciones cortas del mismo actor. **Regla necesaria:** Prohibición o restricción afirmativa vigente de fragmentación excesiva, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Una frase se divide artificialmente en veinte mensajes seguidos. **Caso legítimo:** Una persona escribe dos aclaraciones seguidas.

**Contexto, excepciones y polisemia:** El rate-limit solo observa frecuencia; no puede probar que la fragmentación sea deliberada. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** flood. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Una persona escribe dos aclaraciones seguidas. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod.

### `message_burst` — Ráfagas de mensajes

**Familia/versión:** spam / 1.0.0. **Capacidad:** objetiva/determinista (señal). **Estado:** `existing_signal`.

**Descripción/señal:** Cantidad propia elevada frente a la actividad reciente del canal. **Regla necesaria:** Prohibición o restricción afirmativa vigente de ráfagas de mensajes, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Un actor ocupa casi toda una ventana con mensajes rápidos. **Caso legítimo:** Conversación de muchos participantes durante un evento.

**Contexto, excepciones y polisemia:** La actividad colectiva legítima debe elevar el umbral; el volumen total no atribuye culpa individual. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** flood. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Conversación de muchos participantes durante un evento. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod.

### `cross_channel_repeat` — Repetición entre canales

**Familia/versión:** spam / 1.0.0. **Capacidad:** objetiva/determinista (señal). **Estado:** `existing_signal`.

**Descripción/señal:** Un mismo autor repite contenido en varios canales. **Regla necesaria:** Prohibición o restricción afirmativa vigente de repetición entre canales, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Un anuncio idéntico aparece en tres canales sin relación. **Caso legítimo:** Un aviso administrativo autorizado en varios canales.

**Contexto, excepciones y polisemia:** No unir historiales de reglas o servidores; las exenciones de cada canal cuentan antes del análisis. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** cross_channel. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Un aviso administrativo autorizado en varios canales. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod.

### `mass_forwarding` — Reenvío masivo

**Familia/versión:** spam / 1.0.0. **Capacidad:** heurística/contextual (señal). **Estado:** `existing_signal`.

**Descripción/señal:** Repetición propia distribuida entre canales. **Regla necesaria:** Prohibición o restricción afirmativa vigente de reenvío masivo, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** La misma solicitud se copia en varios espacios en una ráfaga. **Caso legítimo:** Información solicitada por distintos equipos.

**Contexto, excepciones y polisemia:** Un mensaje reenviado no es infracción por su forma; importan autorización, frecuencia y destino. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** cross_channel. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Información solicitada por distintos equipos. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod.

### `chain_messages` — Cadenas de mensajes

**Familia/versión:** spam / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Contenido que exige republicarse y se distribuye en cadena. **Regla necesaria:** Prohibición o restricción afirmativa vigente de cadenas de mensajes, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Una cadena invita a copiar un mensaje en todos los canales. **Caso legítimo:** Un juego de escritura expresamente permitido.

**Contexto, excepciones y polisemia:** Reconocer una instrucción de reenvío no prueba su ejecución; no usar palabras aisladas para acusar. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Un juego de escritura expresamente permitido. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines.

### `insistent_requests` — Solicitudes insistentes

**Familia/versión:** spam / 1.0.0. **Capacidad:** heurística/contextual (señal). **Estado:** `existing_signal`.

**Descripción/señal:** Reiteración propia de una solicitud dentro de una ventana de baja actividad. **Regla necesaria:** Prohibición o restricción afirmativa vigente de solicitudes insistentes, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** La misma petición interrumpe repetidamente una conversación. **Caso legítimo:** Una consulta repetida tras un problema técnico.

**Contexto, excepciones y polisemia:** No se sabe si recibió respuesta o si la necesidad era legítima solo a partir de huellas. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** repeat, similar_text. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Una consulta repetida tras un problema técnico. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod.

### `repeated_images` — Imágenes idénticas repetidas

**Familia/versión:** media / 1.0.0. **Capacidad:** objetiva/determinista (señal). **Estado:** `existing_signal`.

**Descripción/señal:** Hash criptográfico igual entre adjuntos acotados del propio actor. **Regla necesaria:** Prohibición o restricción afirmativa vigente de imágenes idénticas repetidas, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** La misma imagen se publica varias veces seguidas. **Caso legítimo:** La misma imagen se usa una vez por persona en un juego permitido.

**Contexto, excepciones y polisemia:** La igualdad de bytes no determina si publicar era indebido; no descargar adjuntos sin límite. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** images. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** La misma imagen se usa una vez por persona en un juego permitido. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod.

### `similar_images` — Imágenes visualmente similares

**Familia/versión:** media / 1.0.0. **Capacidad:** heurística/contextual (señal). **Estado:** `existing_signal`.

**Descripción/señal:** Huellas perceptuales próximas de imágenes informativas. **Regla necesaria:** Prohibición o restricción afirmativa vigente de imágenes visualmente similares, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Variantes mínimas de una misma imagen se reiteran. **Caso legítimo:** Dos diagramas con fondo uniforme.

**Contexto, excepciones y polisemia:** Una distancia de hash no acredita identidad, significado ni intención; excluir huellas triviales. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** similar_images. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Dos diagramas con fondo uniforme. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod.

### `repeated_gifs` — GIF reiterados

**Familia/versión:** media / 1.0.0. **Capacidad:** heurística/contextual (señal). **Estado:** `existing_signal`.

**Descripción/señal:** Igualdad de bytes de GIF descargados bajo el límite de imagen. **Regla necesaria:** Prohibición o restricción afirmativa vigente de gif reiterados, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** El mismo GIF se insiste varias veces. **Caso legítimo:** Dos GIF diferentes comparten el primer fotograma.

**Contexto, excepciones y polisemia:** El hash perceptual de un fotograma no compara toda la animación; no anunciar comprensión de vídeo. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** images. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Dos GIF diferentes comparten el primer fotograma. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod.

### `repeated_stickers` — Stickers reiterados

**Familia/versión:** media / 1.0.0. **Capacidad:** objetiva/determinista (señal). **Estado:** `planned_signal`.

**Descripción/señal:** Identificador de sticker repetido por el mismo actor. **Regla necesaria:** Prohibición o restricción afirmativa vigente de stickers reiterados, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Un sticker se publica repetidamente en segundos. **Caso legítimo:** Un sticker de saludo una sola vez.

**Contexto, excepciones y polisemia:** La repetición del ID es observable sin descargar imágenes; las celebraciones pueden estar permitidas. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** sticker_repeat. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Un sticker de saludo una sola vez. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod.

### `attachment_burst` — Saturación mediante adjuntos

**Familia/versión:** media / 1.0.0. **Capacidad:** objetiva/determinista (señal). **Estado:** `planned_signal`.

**Descripción/señal:** Acumulación extraordinaria de adjuntos del actor en una ventana breve. **Regla necesaria:** Prohibición o restricción afirmativa vigente de saturación mediante adjuntos, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Numerosos archivos ocupan consecutivamente el canal. **Caso legítimo:** Un envío solicitado de varios documentos.

**Contexto, excepciones y polisemia:** Contar archivos no analiza su contenido ni los convierte en malware; no descargar archivos arbitrarios. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** attachment_flood. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Un envío solicitado de varios documentos. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod.

### `embed_burst` — Saturación mediante embeds

**Familia/versión:** media / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Reiteración de tarjetas o vistas previas que dificulta leer. **Regla necesaria:** Prohibición o restricción afirmativa vigente de saturación mediante embeds, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Publicaciones insistentes generan muchas tarjetas. **Caso legítimo:** Una lista útil de recursos solicitada.

**Contexto, excepciones y polisemia:** Las vistas previas pueden generarlas Discord o bots permitidos; sin evento/atribución fiable, revisión humana. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Una lista útil de recursos solicitada. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines.

### `unauthorized_promotion` — Promoción no autorizada

**Familia/versión:** promotion / 1.0.0. **Capacidad:** heurística/contextual (señal). **Estado:** `existing_signal`.

**Descripción/señal:** Enlace acompañado de llamada comercial y una regla que restringe promoción. **Regla necesaria:** Prohibición o restricción afirmativa vigente de promoción no autorizada, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Una oferta comercial con enlace fuera del espacio permitido. **Caso legítimo:** Un enlace documental sin oferta comercial.

**Contexto, excepciones y polisemia:** Un enlace no es publicidad; «oferta» puede ser de ayuda, trabajo o una cita. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** advertising. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Un enlace documental sin oferta comercial. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod.

### `repeated_promotion` — Promoción reiterada

**Familia/versión:** promotion / 1.0.0. **Capacidad:** heurística/contextual (señal). **Estado:** `existing_signal`.

**Descripción/señal:** Señales comerciales y reiteración propia de destino. **Regla necesaria:** Prohibición o restricción afirmativa vigente de promoción reiterada, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Una oferta con enlace se repite varias veces. **Caso legítimo:** Una oferta autorizada una sola vez en promociones.

**Contexto, excepciones y polisemia:** Respetar canales, roles y autorizaciones expresas; la repetición y la promoción son dimensiones diferentes. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** advertising, links. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Una oferta autorizada una sola vez en promociones. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod.

### `server_invites` — Invitaciones a servidores

**Familia/versión:** promotion / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Enlaces con formato de invitación y regla que restringe invitaciones. **Regla necesaria:** Prohibición o restricción afirmativa vigente de invitaciones a servidores, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Invitación no solicitada para captar miembros. **Caso legítimo:** Un enlace al propio servidor o colaboración autorizada.

**Contexto, excepciones y polisemia:** El formato de invitación no demuestra captación abusiva ni que el destino exista. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Un enlace al propio servidor o colaboración autorizada. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines.

### `referral_links` — Referidos y recompensas

**Familia/versión:** promotion / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Referencia explícita a recompensas o atribución de referidos. **Regla necesaria:** Prohibición o restricción afirmativa vigente de referidos y recompensas, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Captación insistente con una recompensa. **Caso legítimo:** Enlace de referencia autorizado y claramente rotulado.

**Contexto, excepciones y polisemia:** No afirmar fraude por parámetros de URL; se necesita una prohibición concreta y contexto. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Enlace de referencia autorizado y claramente rotulado. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines.

### `commercial_solicitation` — Solicitudes comerciales

**Familia/versión:** promotion / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Solicitud de compra, venta o contacto comercial bajo regla aplicable. **Regla necesaria:** Prohibición o restricción afirmativa vigente de solicitudes comerciales, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Una solicitud comercial no permitida en soporte. **Caso legítimo:** Consulta comercial permitida en el canal de comercio.

**Contexto, excepciones y polisemia:** No inferir intercambio ilícito ni intención a partir de «vendo» o «compro» por sí solos. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Consulta comercial permitida en el canal de comercio. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines.

### `covert_advertising` — Publicidad encubierta

**Familia/versión:** promotion / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Indicios contextuales de promoción que se presenta como recomendación neutral. **Regla necesaria:** Prohibición o restricción afirmativa vigente de publicidad encubierta, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Una recomendación oculta reiterada con beneficio comercial comprobable. **Caso legítimo:** Una recomendación espontánea sin relación comercial.

**Contexto, excepciones y polisemia:** No se puede deducir una relación económica o intención oculta por similitud de textos. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Una recomendación espontánea sin relación comercial. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines.

### `invasive_recruitment` — Captación invasiva

**Familia/versión:** promotion / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Peticiones reiteradas de trasladar la conversación o unirse a otro espacio. **Regla necesaria:** Prohibición o restricción afirmativa vigente de captación invasiva, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Captación insistente tras una negativa verificable. **Caso legítimo:** Invitación aceptada a una colaboración.

**Contexto, excepciones y polisemia:** No leer DMs ni atribuir negativas que el bot no presenció. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Invitación aceptada a una colaboración. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines.

### `directed_insult` — Insultos dirigidos

**Familia/versión:** interpersonal / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Expresión descalificadora dirigida a una persona identificable y contexto suficiente. **Regla necesaria:** Prohibición o restricción afirmativa vigente de insultos dirigidos, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Un ataque personal directo bajo una regla contra insultos. **Caso legítimo:** Cita de un insulto para denunciarlo.

**Contexto, excepciones y polisemia:** Citas, ironía, usos regionales, bromas consentidas y palabras polisémicas impiden una conclusión por léxico. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Cita de un insulto para denunciarlo. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, discord_harassment, context_study, use_mention_study.

### `repeated_devaluation` — Descalificación reiterada

**Familia/versión:** interpersonal / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Secuencia reiterada de descalificaciones a un mismo destinatario. **Regla necesaria:** Prohibición o restricción afirmativa vigente de descalificación reiterada, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Ataques persistentes a una persona en distintas intervenciones. **Caso legítimo:** Crítica concreta a una propuesta.

**Contexto, excepciones y polisemia:** Distinguir crítica de ideas de ataques personales; no inferir relación interpersonal. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Crítica concreta a una propuesta. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, discord_harassment, context_study, use_mention_study.

### `persistent_provocation` — Provocación persistente

**Familia/versión:** interpersonal / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Intervenciones repetidas que buscan una reacción bajo evidencia contextual. **Regla necesaria:** Prohibición o restricción afirmativa vigente de provocación persistente, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Provocaciones verificables que continúan tras una indicación válida. **Caso legítimo:** Desacuerdo intenso sobre una idea.

**Contexto, excepciones y polisemia:** La intención de provocar no se mide por sentimiento o frecuencia por sí solos. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Desacuerdo intenso sobre una idea. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, discord_harassment, context_study, use_mention_study.

### `repeated_harassment` — Hostigamiento reiterado

**Familia/versión:** interpersonal / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Persistencia dirigida no deseada respaldada por secuencia y destinatario. **Regla necesaria:** Prohibición o restricción afirmativa vigente de hostigamiento reiterado, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Insistencia dirigida tras una negativa visible. **Caso legítimo:** Intercambio recíproco consentido.

**Contexto, excepciones y polisemia:** No inferir consentimiento o rechazo; no entrenar con conversaciones privadas. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Intercambio recíproco consentido. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, discord_harassment, context_study, use_mention_study.

### `cross_channel_pursuit` — Persecución entre canales

**Familia/versión:** interpersonal / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** El mismo destinatario recibe interacciones persistentes en distintos canales accesibles. **Regla necesaria:** Prohibición o restricción afirmativa vigente de persecución entre canales, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Seguimiento dirigido reiterado tras un rechazo verificable. **Caso legítimo:** Dos miembros participan normalmente en varios canales.

**Contexto, excepciones y polisemia:** Coincidir en canales no prueba persecución; preservar ACL y revisión humana. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Dos miembros participan normalmente en varios canales. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, discord_harassment, context_study, use_mention_study.

### `collective_harassment` — Hostigamiento colectivo

**Familia/versión:** interpersonal / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Acciones dirigidas y evidencia de participación propia de varios actores. **Regla necesaria:** Prohibición o restricción afirmativa vigente de hostigamiento colectivo, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Varios actores reiteran ataques a una persona. **Caso legítimo:** Muchas personas responden una vez a una pregunta pública.

**Contexto, excepciones y polisemia:** La coincidencia temporal o pertenencia grupal no demuestra coordinación ni culpa individual. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Muchas personas responden una vez a una pregunta pública. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, discord_harassment, context_study, use_mention_study.

### `threats` — Amenazas

**Familia/versión:** interpersonal / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Expresión dirigida de daño con suficiente contexto y referencia verificable. **Regla necesaria:** Prohibición o restricción afirmativa vigente de amenazas, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** [Ejemplo sintético no gráfico de una amenaza dirigida]. **Caso legítimo:** Cita o relato para pedir ayuda.

**Contexto, excepciones y polisemia:** «Te voy a ganar» en un juego no es automáticamente amenaza; la gravedad exige más evidencia, no menos. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Cita o relato para pedir ayuda. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, discord_harassment, context_study, use_mention_study.

### `intimidation` — Intimidación

**Familia/versión:** interpersonal / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Presión dirigida mediante consecuencias hostiles contextualizadas. **Regla necesaria:** Prohibición o restricción afirmativa vigente de intimidación, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Presión intimidatoria verificable contra otro miembro. **Caso legítimo:** Descripción neutral de consecuencias de una regla.

**Contexto, excepciones y polisemia:** No confundir advertencia administrativa legítima con intimidación. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Descripción neutral de consecuencias de una regla. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, discord_harassment, context_study, use_mention_study.

### `degrading_mockery` — Burlas degradantes

**Familia/versión:** interpersonal / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Burla dirigida cuya naturaleza degradante se acredita por contexto. **Regla necesaria:** Prohibición o restricción afirmativa vigente de burlas degradantes, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Humillación reiterada a un miembro. **Caso legítimo:** Humor consentido entre participantes.

**Contexto, excepciones y polisemia:** La relación, el consentimiento y los registros regionales no pueden suponerse. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Humor consentido entre participantes. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, discord_harassment, context_study, use_mention_study.

### `discrimination` — Discriminación

**Familia/versión:** interpersonal / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Trato o expresión de exclusión bajo una regla concreta y evidencia suficiente. **Regla necesaria:** Prohibición o restricción afirmativa vigente de discriminación, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** [Ejemplo sintético no gráfico de exclusión discriminatoria]. **Caso legítimo:** Discusión crítica de discriminación para rechazarla.

**Contexto, excepciones y polisemia:** No inferir identidad, nacionalidad, atributos sensibles ni intención de la persona. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Discusión crítica de discriminación para rechazarla. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, discord_harassment, context_study, use_mention_study.

### `protected_attribute_attacks` — Ataques por atributos protegidos

**Familia/versión:** interpersonal / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Ataque dirigido basado expresamente en un atributo protegido. **Regla necesaria:** Prohibición o restricción afirmativa vigente de ataques por atributos protegidos, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** [Ejemplo sintético no gráfico de un ataque de odio]. **Caso legítimo:** Contradiscurso que menciona una frase para condenarla.

**Contexto, excepciones y polisemia:** Distinguir uso de mención y reapropiación; no usar listas de términos como prueba de culpabilidad. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Contradiscurso que menciona una frase para condenarla. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, discord_harassment, context_study, use_mention_study.

### `harassment_incitement` — Incitación a hostigar

**Familia/versión:** interpersonal / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Llamamiento contextualizado a dirigir acciones hostiles a un destinatario. **Regla necesaria:** Prohibición o restricción afirmativa vigente de incitación a hostigar, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Una convocatoria verificable de hostigamiento. **Caso legítimo:** Invitación a denunciar una infracción de buena fe.

**Contexto, excepciones y polisemia:** No confundir denuncia legítima, cita y llamada al acoso. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Invitación a denunciar una infracción de buena fe. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, discord_harassment, context_study, use_mention_study.

### `contextual_hostility` — Hostilidad contextual

**Familia/versión:** interpersonal / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Contexto conversacional suficiente para valorar lenguaje aparentemente hostil. **Regla necesaria:** Prohibición o restricción afirmativa vigente de hostilidad contextual, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Una expresión hostil dirigida y no consentida. **Caso legítimo:** Una expresión regional afectuosa entre amigos.

**Contexto, excepciones y polisemia:** El sentimiento negativo o una puntuación de confianza no sustituye evidencia. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Una expresión regional afectuosa entre amigos. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, discord_harassment, context_study, use_mention_study.

### `sexual_harassment` — Hostigamiento sexual

**Familia/versión:** interpersonal / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Conducta sexual no deseada acreditada sin divulgar material sensible. **Regla necesaria:** Prohibición o restricción afirmativa vigente de hostigamiento sexual, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** [Ejemplo sintético no gráfico de insistencia sexual no deseada]. **Caso legítimo:** Conversación adulta consentida en un espacio autorizado.

**Contexto, excepciones y polisemia:** Nunca inferir consentimiento o edad; no recopilar contenido privado ni material gráfico para entrenar. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Conversación adulta consentida en un espacio autorizado. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, discord_harassment, context_study, use_mention_study.

### `credential_solicitation` — Solicitudes de credenciales

**Familia/versión:** security / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Petición contextualizada de secretos de acceso. **Regla necesaria:** Prohibición o restricción afirmativa vigente de solicitudes de credenciales, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Un falso soporte solicita una contraseña. **Caso legítimo:** Un aviso que dice que nunca se comparta la contraseña.

**Contexto, excepciones y polisemia:** Mencionar «contraseña», «token» o «senha» en una guía no constituye robo ni prueba fraude. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Un aviso que dice que nunca se comparta la contraseña. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, use_mention_study, context_study.

### `staff_impersonation` — Suplantación de personal

**Familia/versión:** security / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Afirmación de autoridad contrastada con un registro autorizado. **Regla necesaria:** Prohibición o restricción afirmativa vigente de suplantación de personal, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Una persona se atribuye falsamente un cargo verificable. **Caso legítimo:** Un mensaje que cita a una persona del equipo.

**Contexto, excepciones y polisemia:** No probar identidad con nombre, avatar o similitud; no descargar perfiles ni desanonimizar. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Un mensaje que cita a una persona del equipo. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, use_mention_study, context_study.

### `user_impersonation` — Suplantación de miembros

**Familia/versión:** security / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Afirmación engañosa de identidad contrastada con evidencia administrativa. **Regla necesaria:** Prohibición o restricción afirmativa vigente de suplantación de miembros, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Suplantación acreditada por revisión administrativa. **Caso legítimo:** Dos personas comparten un apodo.

**Contexto, excepciones y polisemia:** Un nombre parecido, cuenta nueva o idioma no demuestra suplantación. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Dos personas comparten un apodo. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, use_mention_study, context_study.

### `phishing_links` — Enlaces potencialmente engañosos

**Familia/versión:** security / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Destino y contexto de una solicitud de acceso que requieren revisión. **Regla necesaria:** Prohibición o restricción afirmativa vigente de enlaces potencialmente engañosos, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Un mensaje de falsa asistencia dirige a una página de acceso ajena. **Caso legítimo:** Documentación legítima que enlaza otra web.

**Contexto, excepciones y polisemia:** No visitar destinos de miembros ni afirmar phishing por un dominio desconocido. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Documentación legítima que enlaza otra web. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, use_mention_study, context_study.

### `masked_link` — Diferencia entre URL visible y destino

**Familia/versión:** security / 1.0.0. **Capacidad:** objetiva/determinista (señal). **Estado:** `planned_signal`.

**Descripción/señal:** Etiqueta con forma de URL cuyo host difiere del enlace Markdown real. **Regla necesaria:** Prohibición o restricción afirmativa vigente de diferencia entre url visible y destino, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Una etiqueta presenta https://seguro.example pero apunta a otro host. **Caso legítimo:** Un enlace cuyo texto no pretende ser una URL.

**Contexto, excepciones y polisemia:** La discordancia es observable, pero no demuestra malicia; pueden existir redirecciones o acortadores legítimos. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** masked_link. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Un enlace cuyo texto no pretende ser una URL. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod, use_mention_study, context_study.

### `financial_scams` — Posibles estafas

**Familia/versión:** security / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Solicitud de beneficio económico y elementos verificables de engaño. **Regla necesaria:** Prohibición o restricción afirmativa vigente de posibles estafas, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Una solicitud fraudulenta acreditada por revisión. **Caso legítimo:** Transacción autorizada con información transparente.

**Contexto, excepciones y polisemia:** No decidir fraude, legalidad o responsabilidad basándose en una palabra o URL. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Transacción autorizada con información transparente. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, use_mention_study, context_study.

### `fake_support` — Falsa asistencia técnica

**Familia/versión:** security / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Afirmación falsa de soporte y solicitud sospechosa de acceso. **Regla necesaria:** Prohibición o restricción afirmativa vigente de falsa asistencia técnica, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Un falso soporte pide secretos para resolver un problema. **Caso legítimo:** Soporte autorizado ofrece instrucciones públicas.

**Contexto, excepciones y polisemia:** Validar roles y alcance; un saludo de soporte no acredita identidad ni engaño. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Soporte autorizado ofrece instrucciones públicas. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, use_mention_study, context_study.

### `giveaway_fraud` — Fraude de regalos o sorteos

**Familia/versión:** security / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Promesa de premio con condiciones engañosas verificadas. **Regla necesaria:** Prohibición o restricción afirmativa vigente de fraude de regalos o sorteos, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Un premio falso exige entregar una credencial. **Caso legítimo:** Sorteo autorizado que no solicita secretos.

**Contexto, excepciones y polisemia:** «Regalo» o «giveaway» puede ser un evento legítimo; no acusar por publicidad aislada. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Sorteo autorizado que no solicita secretos. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, use_mention_study, context_study.

### `nonconsensual_pii` — Divulgación no consentida de datos

**Familia/versión:** security / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Información identificable y contexto que acredita falta de autorización. **Regla necesaria:** Prohibición o restricción afirmativa vigente de divulgación no consentida de datos, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** [Datos ficticios] se difunden contra una prohibición explícita. **Caso legítimo:** Una persona publica su propio contacto autorizado.

**Contexto, excepciones y polisemia:** Un número no acredita que sea real, personal, ajeno o no consentido; minimizar copia y audiencia. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Una persona publica su propio contacto autorizado. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, use_mention_study, context_study.

### `social_engineering` — Ingeniería social

**Familia/versión:** security / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Secuencia de manipulación y solicitud de una acción sensible respaldada por contexto. **Regla necesaria:** Prohibición o restricción afirmativa vigente de ingeniería social, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Una falsa urgencia induce a revelar acceso. **Caso legítimo:** Aviso legítimo de un administrador conocido.

**Contexto, excepciones y polisemia:** La urgencia o cortesía no demuestran manipulación; no atribuir intención sin prueba. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Aviso legítimo de un administrador conocido. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, use_mention_study, context_study.

### `suspicious_files` — Archivos sospechosos

**Familia/versión:** security / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Metadatos o alerta de una fuente de seguridad autorizada. **Regla necesaria:** Prohibición o restricción afirmativa vigente de archivos sospechosos, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Un archivo con alerta verificable requiere revisión. **Caso legítimo:** Un archivo de trabajo solicitado.

**Contexto, excepciones y polisemia:** Nombre, extensión o MIME no prueban malware; no ejecutar ni descargar archivos indiscriminadamente. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Un archivo de trabajo solicitado. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, use_mention_study, context_study.

### `synchronized_posts` — Publicaciones sincronizadas

**Familia/versión:** coordination / 1.0.0. **Capacidad:** heurística/contextual (señal). **Estado:** `existing_signal`.

**Descripción/señal:** Contenido coincidente de varios actores con contribución propia repetida. **Regla necesaria:** Prohibición o restricción afirmativa vigente de publicaciones sincronizadas, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Varios actores repiten el mismo texto de interrupción. **Caso legítimo:** Felicitaciones legítimas de varias personas.

**Contexto, excepciones y polisemia:** La simultaneidad es una señal; no equivale a acuerdo previo ni culpa colectiva. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** coordinated. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Felicitaciones legítimas de varias personas. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod.

### `mention_campaign` — Campañas de menciones

**Familia/versión:** coordination / 1.0.0. **Capacidad:** heurística/contextual (señal). **Estado:** `existing_signal`.

**Descripción/señal:** Menciones masivas y reiteración atribuible a cada actor. **Regla necesaria:** Prohibición o restricción afirmativa vigente de campañas de menciones, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Una campaña repetitiva satura destinatarios. **Caso legítimo:** Una convocatoria autorizada a una actividad.

**Contexto, excepciones y polisemia:** No compartir atribución entre actores ni castigar una participación única. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** mentions, coordinated. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Una convocatoria autorizada a una actividad. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod.

### `interruption_campaign` — Campañas de interrupción

**Familia/versión:** coordination / 1.0.0. **Capacidad:** heurística/contextual (señal). **Estado:** `existing_signal`.

**Descripción/señal:** Repetición distribuida con evidencia individual propia. **Regla necesaria:** Prohibición o restricción afirmativa vigente de campañas de interrupción, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Contenido idéntico se repite para interrumpir varios espacios. **Caso legítimo:** Un evento comunitario coordinado y permitido.

**Contexto, excepciones y polisemia:** «Raid» puede ser una actividad de juego; la coordinación por sí misma no es infracción. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** coordinated, cross_channel. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Un evento comunitario coordinado y permitido. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod.

### `brigading` — Brigading

**Familia/versión:** coordination / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Participación coordinada hostil acreditada con contexto legítimo. **Regla necesaria:** Prohibición o restricción afirmativa vigente de brigading, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Una convocatoria hostil verificable dirige acciones al servidor. **Caso legítimo:** Llegada normal de participantes desde una colaboración.

**Contexto, excepciones y polisemia:** No inferir intención por hora de ingreso, procedencia o pertenencia común; no reimplementar antirraid. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Llegada normal de participantes desde una colaboración. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines.

### `ban_evasion` — Evasión de sanciones

**Familia/versión:** coordination / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Correspondencia de identidad establecida por un mecanismo autorizado. **Regla necesaria:** Prohibición o restricción afirmativa vigente de evasión de sanciones, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Evasión acreditada por el equipo con evidencia suficiente. **Caso legítimo:** Dos miembros coinciden en estilo de escritura.

**Contexto, excepciones y polisemia:** No vincular cuentas por similitud, red, nacionalidad, avatar o huella invasiva. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Dos miembros coinciden en estilo de escritura. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines.

### `mass_mentions` — Menciones masivas

**Familia/versión:** features / 1.0.0. **Capacidad:** objetiva/determinista (señal). **Estado:** `existing_signal`.

**Descripción/señal:** Muchas menciones únicas de personas o roles en un mensaje. **Regla necesaria:** Prohibición o restricción afirmativa vigente de menciones masivas, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Un mensaje menciona numerosos destinatarios contra una regla. **Caso legítimo:** Una convocatoria autorizada a un equipo.

**Contexto, excepciones y polisemia:** La regla puede permitir menciones en un canal o a cierto personal; contar destinatarios únicos. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** mentions. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Una convocatoria autorizada a un equipo. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod.

### `broadcast_mentions` — Abuso de menciones generales

**Familia/versión:** features / 1.0.0. **Capacidad:** objetiva/determinista (señal). **Estado:** `existing_signal`.

**Descripción/señal:** Uso de @everyone o @here bajo una prohibición aplicable. **Regla necesaria:** Prohibición o restricción afirmativa vigente de abuso de menciones generales, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Una mención general no autorizada interrumpe a la comunidad. **Caso legítimo:** Aviso permitido de personal autorizado.

**Contexto, excepciones y polisemia:** No inferir abuso de una cita sin ping efectivo; usar el indicador de Discord y exenciones. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** mentions. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Aviso permitido de personal autorizado. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod.

### `directed_mentions` — Menciones insistentes

**Familia/versión:** features / 1.0.0. **Capacidad:** heurística/contextual (señal). **Estado:** `planned_signal`.

**Descripción/señal:** El mismo autor menciona reiteradamente al mismo destinatario. **Regla necesaria:** Prohibición o restricción afirmativa vigente de menciones insistentes, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Pings repetidos a una persona en una ventana breve. **Caso legítimo:** Dos respuestas que mencionan a un colaborador.

**Contexto, excepciones y polisemia:** No inferir rechazo ni acoso; la insistencia es señal provisional con contexto. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** GUILD_MESSAGES; MESSAGE_CONTENT; VIEW_CHANNEL; READ_MESSAGE_HISTORY. **Método:** directed_mentions. **Umbral:** Ventanas acotadas, umbrales documentados por mecanismo y sensibilidad; nunca cambian la prohibición. **Recursos:** Sin clasificador IA por mensaje; huellas en ventana de 90 s / 4096 eventos; imágenes solo si procede, hasta cuatro de 1 MiB / 4 Mpx.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Dos respuestas que mencionan a un colaborador. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** La medida acredita solo el patrón observable; una puntuación o coincidencia no prueba culpabilidad. **Automatización:** Solo observación provisional con regla y autorización guardadas; sin sanción automática. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_automod.

### `spoiler_abuse` — Abuso de spoilers

**Familia/versión:** features / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Uso contextual de spoilers que incumple una regla específica. **Regla necesaria:** Prohibición o restricción afirmativa vigente de abuso de spoilers, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Spoilers reiterados ocultan publicaciones contra una prohibición. **Caso legítimo:** Contenido oculto conforme a las reglas de una discusión.

**Contexto, excepciones y polisemia:** El formato spoiler es una función legítima y no demuestra intención de ocultar abuso. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Contenido oculto conforme a las reglas de una discusión. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines.

### `invisible_formatting` — Formatos invisibles engañosos

**Familia/versión:** features / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Secuencias de formato y contexto de engaño o saturación. **Regla necesaria:** Prohibición o restricción afirmativa vigente de formatos invisibles engañosos, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Formato engañoso acreditado que dificulta leer. **Caso legítimo:** Caracteres de unión válidos en una escritura.

**Contexto, excepciones y polisemia:** No tratar Unicode, escrituras regionales o accesibilidad como evasión por sí mismos. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Caracteres de unión válidos en una escritura. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines.

### `format_flood` — Saturación mediante formato

**Familia/versión:** features / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Repetición de formato que dificulta la lectura bajo regla expresa. **Regla necesaria:** Prohibición o restricción afirmativa vigente de saturación mediante formato, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Formato reiterado ocupa excesivamente un canal. **Caso legítimo:** Un bloque de código o fórmula útil.

**Contexto, excepciones y polisemia:** No equiparar código, documentación o accesibilidad con abuso. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Un bloque de código o fórmula útil. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines.

### `unauthorized_automation` — Automatización no autorizada

**Familia/versión:** features / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Identidad de aplicación y autorización administrativa verificables. **Regla necesaria:** Prohibición o restricción afirmativa vigente de automatización no autorizada, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Una aplicación conocida publica sin autorización. **Caso legítimo:** Un bot aprobado publica un recordatorio.

**Contexto, excepciones y polisemia:** Bots y webhooks están excluidos del detector de miembros; no inferir automatización por velocidad humana. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Un bot aprobado publica un recordatorio. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines.

### `reaction_spam` — Spam de reacciones

**Familia/versión:** features / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Eventos de reacción atribuibles a un actor con permisos y alcance legítimos. **Regla necesaria:** Prohibición o restricción afirmativa vigente de spam de reacciones, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Un actor satura reacciones contra una regla expresa. **Caso legítimo:** Reacciones de un juego permitido.

**Contexto, excepciones y polisemia:** El runtime actual no atribuye evidencia de reacción a su actor; no culpar al autor del mensaje original. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Reacciones de un juego permitido. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines.

### `component_spam` — Abuso de componentes

**Familia/versión:** features / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Interacciones que pertenecen al propio bot y tienen actor verificable. **Regla necesaria:** Prohibición o restricción afirmativa vigente de abuso de componentes, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Clics masivos no autorizados contra una regla aplicable. **Caso legítimo:** Un usuario reintenta un clic por un fallo de red.

**Contexto, excepciones y polisemia:** No inspeccionar componentes de otras aplicaciones ni confundir reintentos con abuso. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Un usuario reintenta un clic por un fallo de red. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines.

### `thread_misuse` — Uso indebido de hilos

**Familia/versión:** features / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Actividad de hilos accesibles y regla específica sobre su uso. **Regla necesaria:** Prohibición o restricción afirmativa vigente de uso indebido de hilos, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Creación repetitiva indebida de hilos acreditada. **Caso legítimo:** Un hilo legítimo de soporte.

**Contexto, excepciones y polisemia:** La ruta de mensajes actual no observa todos los eventos de hilos; no anunciar esa cobertura. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Un hilo legítimo de soporte. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines.

### `forum_misuse` — Uso indebido de foros

**Familia/versión:** features / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Publicaciones de foro accesibles y convenciones expresas. **Regla necesaria:** Prohibición o restricción afirmativa vigente de uso indebido de foros, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Publicaciones repetidas incumplen una convención del foro. **Caso legítimo:** Una nueva consulta correctamente etiquetada.

**Contexto, excepciones y polisemia:** La clasificación temática y los permisos requieren contexto; no ampliar el acceso a foros restringidos. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Una nueva consulta correctamente etiquetada. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines.

### `reply_misuse` — Abuso de respuestas

**Familia/versión:** features / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Respuestas reiteradas y dirigidas con contexto suficiente. **Regla necesaria:** Prohibición o restricción afirmativa vigente de abuso de respuestas, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Respuestas insistentes tras una negativa verificable. **Caso legítimo:** Conversación normal que utiliza respuestas.

**Contexto, excepciones y polisemia:** Una respuesta o cita no acredita hostigamiento ni intención. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Conversación normal que utiliza respuestas. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines.

### `edited_link_evasion` — Enlaces añadidos mediante edición

**Familia/versión:** features / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Cambio posterior de un mensaje y contexto de evasión acreditado. **Regla necesaria:** Prohibición o restricción afirmativa vigente de enlaces añadidos mediante edición, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Una edición añade promoción prohibida tras revisión. **Caso legítimo:** Corrección legítima de un enlace erróneo.

**Contexto, excepciones y polisemia:** El runtime inicial solo observa nuevos mensajes; no asumir cobertura de ediciones ni duplicar sanciones. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Corrección legítima de un enlace erróneo. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, edited_link_experience.

### `off_topic` — Contenido fuera de tema

**Familia/versión:** organization / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Tema del canal, regla y contexto de una publicación. **Regla necesaria:** Prohibición o restricción afirmativa vigente de contenido fuera de tema, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Desvío persistente acreditado contra una regla temática. **Caso legítimo:** Un ejemplo relacionado con la conversación.

**Contexto, excepciones y polisemia:** No usar sentimiento o listas de palabras como clasificador universal de tema. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Un ejemplo relacionado con la conversación. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, use_mention_study, context_study.

### `channel_conventions` — Convenciones de canales

**Familia/versión:** organization / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Convención explícita y verificable del espacio. **Regla necesaria:** Prohibición o restricción afirmativa vigente de convenciones de canales, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Una publicación omite una convención expresa y aplicable. **Caso legítimo:** Un formato alternativo autorizado por accesibilidad.

**Contexto, excepciones y polisemia:** Diferenciar reglas oficiales, preferencias del canal y opiniones de participantes. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Un formato alternativo autorizado por accesibilidad. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, use_mention_study, context_study.

### `ignored_staff_instruction` — Incumplimiento de indicaciones legítimas

**Familia/versión:** organization / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Instrucción auténtica de personal autorizado que desarrolla una regla. **Regla necesaria:** Prohibición o restricción afirmativa vigente de incumplimiento de indicaciones legítimas, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Una indicación vigente y válida se incumple repetidamente. **Caso legítimo:** Una petición de un miembro que se hace pasar por personal.

**Contexto, excepciones y polisemia:** No convertir cualquier mensaje de staff en nueva norma; verificar autor, alcance, vigencia y fuente. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Una petición de un miembro que se hace pasar por personal. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, use_mention_study, context_study.

### `requests_after_response` — Peticiones tras una respuesta

**Familia/versión:** organization / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Respuesta o negativa verificable y repetición posterior de la misma petición. **Regla necesaria:** Prohibición o restricción afirmativa vigente de peticiones tras una respuesta, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** La misma solicitud insiste tras una respuesta clara. **Caso legítimo:** Una aclaración legítima sobre una respuesta incompleta.

**Contexto, excepciones y polisemia:** Las huellas de texto no prueban comprensión, rechazo ni resolución de una consulta. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Una aclaración legítima sobre una respuesta incompleta. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines, use_mention_study, context_study.

### `age_restricted_placement` — Contenido en un espacio no autorizado

**Familia/versión:** restricted / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Etiqueta del canal y evidencia autorizada sobre el contenido. **Regla necesaria:** Prohibición o restricción afirmativa vigente de contenido en un espacio no autorizado, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** [Ejemplo sintético no gráfico] aparece en un espacio no autorizado. **Caso legítimo:** Contenido adulto permitido en un canal restringido y autorizado.

**Contexto, excepciones y polisemia:** La etiqueta NSFW no clasifica el contenido ni acredita la edad de nadie; no descargar medios para inferirla. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Contenido adulto permitido en un canal restringido y autorizado. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines.

### `private_message_harassment` — Hostigamiento por mensajes privados

**Familia/versión:** restricted / 1.0.0. **Capacidad:** no fiable para actuación autónoma. **Estado:** `review_only`.

**Descripción/señal:** Denuncia voluntaria y evidencia autorizada examinada por el equipo. **Regla necesaria:** Prohibición o restricción afirmativa vigente de hostigamiento por mensajes privados, con ámbito y excepciones verificables. La categoría no crea una norma.

**Posible caso sintético:** Una denuncia aporta evidencia pertinente para revisión humana. **Caso legítimo:** Un intercambio privado consentido.

**Contexto, excepciones y polisemia:** Custodio no lee ni monitoriza DMs de miembros; no inferir hechos de conversaciones inaccesibles. Además, se aplican protección del propietario/personal, exenciones y permisos explícitos de la regla. **Idiomas de interfaz/evaluación previstos:** es-419, en-US, pt-BR; no implica eficacia lingüística universal.

**Eventos/permisos:** Revisión administrativa de evidencia legítimamente accesible; eventos no implementados no se vigilan.. **Método:** review_only. **Umbral:** Sin umbral que pruebe intención o semántica; requiere revisión humana. **Recursos:** Sin análisis automático ni API por mensaje; consulta administrativa acotada.

**Privacidad:** Sin perfiles, DMs ni conversaciones completas en memoria; evidencia literal solo en Discord con ACL compatible y referencias mínimas en SQLite. **Falsos positivos:** Un intercambio privado consentido. **Falsos negativos:** Evasiones, idiomas no evaluados, señales fuera de ventana o eventos no accesibles. No se afirma exhaustividad.

**Confianza justificable:** No hay detector autónomo suficientemente verificado; abstención y revisión humana. **Automatización:** Ninguna; revisión humana. **Revisión humana:** requerida antes de atribuir una infracción o sancionar. **Fuentes:** discord_guidelines.

