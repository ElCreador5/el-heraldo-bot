# Modo Custodio — informe de implementación y comprobación

Encargo integral del 27/10/2026. Alcance autorizado: `Pruebas`, Railway Test → Lab → worker. Las comprobaciones interactivas pendientes se distinguen de las pruebas automáticas. No se declara aceptación integral ni eficacia universal.

## Versiones y conservación

- HEAD inicial remoto: `9aa06fcdbcab9d249332842baee42aa9a634207a`.
- Se preservan `7eac8af` (interruptor global) y `9aa06fc` (retirada de Integraciones).
- [d99b298](https://github.com/ElCreador5/el-heraldo-bot/commit/d99b2989ba83f00a2ec07786887c2d4ec97ffb2b): modelo Groq vigente, respuesta completa y acotada, esquema estricto y sonda sintética.
- [409f360](https://github.com/ElCreador5/el-heraldo-bot/commit/409f36023f7147a83a728e1bcb8b704cfdab5e18): 73 fichas, fuentes públicas, pruebas de la taxonomía y recibo del proveedor real.
- La publicación del planificador y el SHA desplegado se registran tras su verificación; no se atribuye un despliegue al árbol local.
- `main` comprobado: `32c9f5dcc8505a3d6aacde76533d6b60dd88a542`. No se escribe ni despliega.
- Se conserva `/data` de worker; no se ejecutan migraciones, borrados ni restauraciones. No se leen valores de credenciales ni se cambia configuración privada.
- H-03 conserva servicio, volumen, horario, build, variables y fuente. No se tocan archivos vigilados por su cron, incluidos `requirements*.txt`.

## Taxonomía y fuentes

[73 fichas completas](CUSTODIO_TAXONOMIA.md), versión 1.0.0, sin límite comercial de categorías. Cada ficha tiene ID estable, definición neutral, ejemplos positivos/legítimos sintéticos, señales, contexto, polisemia, excepciones, idiomas, eventos, permisos, relación normativa, mecanismo, recursos, privacidad, FP/FN, certeza y fuentes.

24 categorías disponen de una o más señales locales; se comparten 16 mecanismos. Las otras 49 requieren revisión humana y no se presentan como detectores implementados. Amenazas, discriminación, acoso semántico, identidad y fraude no se clasifican mediante palabras aisladas. Una señal mecánica tampoco prueba culpabilidad.

Fuentes: [Discord Guidelines](https://discord.com/guidelines), [AutoMod oficial](https://docs.discord.com/developers/resources/auto-moderation), [política de hostigamiento](https://discord.com/safety/bullying-harassment-threats-policy-explainer), estudios primarios de [contexto](https://aclanthology.org/2024.lrec-main.740/) y [uso/mención y contradiscurso](https://aclanthology.org/2024.naacl-long.331/). Experiencias públicas de moderación en Reddit son ilustrativas, no evaluaciones de eficacia. No se obtuvieron pruebas adicionales suficientes de X/Instagram; no se inventan consultas. No se recopilaron conversaciones privadas ni perfiles.

## Arquitectura final

1. `custodio_source.py` obtiene las reglas auténticas de Screening mediante Bot autorizado, verifica su habilitación y calcula una revisión que incluye el servidor. Los fallos y cambios de revisión invalidan la autorización de efectos nuevos.
2. `custodio_rule_analysis.py` realiza análisis ocasional por acción administrativa. El proveedor recibe únicamente reglas y esquema, sin mensajes de miembros, DMs ni herramientas. Agrupa hasta cuatro reglas por petición, con límites de bytes/tiempo y presupuesto compartido; no reintenta un 429 o respuesta malformada.
3. `custodio_interpretation.py` verifica números, revisión, texto íntegro, citas literales, categorías conocidas, sentido normativo, canales/roles auténticos, excepciones, condiciones y referencias. Un saludo no llama al proveedor ni crea detectores. Negaciones, contradicciones, instrucciones al modelo, condiciones no ejecutables y excepciones sin resolver se abstienen.
4. Los mecanismos se derivan del registro interno por categoría; la IA no propone acciones, sanciones ni umbrales. No se exige al administrador construir una lista manual.
5. `custodio_interpretation_v1` guarda hashes, spans e interpretación estructurada en la configuración existente. No copia las reglas ni conversaciones en SQLite. La propuesta queda sin aprobar hasta Guardar, con CAS conjunto del plan y la política. Las notas propias del administrador permanecen literales.
6. Correcciones por servidor/revisión/regla: interpretación incorrecta, conducta permitida, excepción legítima, falso positivo, ambigüedad o deshabilitación. Suspender es seguro y reversible dentro de la misma revisión. El registro guarda autor, momento, motivo, revisión y hash, hasta 32 correcciones; no hay entrenamiento con conversaciones. Una revisión nueva no hereda automáticamente la corrección de una regla distinta.
7. Caché por servidor/revisión/taxonomía/modelo/contexto, hasta 32 entradas y una hora. Los mensajes no invocan IA. Presupuesto por proceso: 7500 tokens estimados/65 s, hasta 256 solicitudes/día, máximo 240 s por análisis; los límites reales de la cuenta pueden ser inferiores y prevalece el 429. Reiniciar el proceso reinicia este presupuesto local, nunca la cuota real del proveedor.

La validación literal y los controles conservadores no demuestran comprensión semántica perfecta. El administrador revisa el alcance y la propuesta antes de guardar. Las condiciones semánticas complejas y referencias cruzadas no resueltas se muestran pendientes de aclaración, sin vigilancia ficticia.

## Detección, contexto y recursos

Mecanismos: repetición, similitud textual, enlaces repetidos, menciones masivas, ráfagas, repetición entre canales, imágenes exactas/similares, coordinación con contribución propia, promoción con enlace, saturación de caracteres/emojis, menciones insistentes explícitas, stickers repetidos, ráfagas de adjuntos y destinos Markdown distintos de su etiqueta. Esta última señal no determina phishing; no descarga ni abre la URL.

Las citas y bloques de código se excluyen de los patrones textuales sin modificar la evidencia literal. Una celebración aislada no es saturación. Las menciones automáticas de respuestas no cuentan como pings dirigidos. Las campañas exigen participación propia repetida; la actividad ajena no se atribuye a un miembro con una sola entrada.

Memoria: 90 s / 4096 eventos, sin transcripciones persistentes; cachés de 32 servidores y limitadores de 2048 entradas. Texto hasta 4000 caracteres, enlaces/mentions/adjuntos acotados. Imágenes: cuatro de 1 MiB / 4 Mpx, decodificación en un semáforo, sin archivos temporales ni descargas ajenas a adjuntos Discord. Se conservan sensibilidad y umbrales previos; los seis mecanismos nuevos tienen umbrales explícitos en `custodio_detection.py` y corpus reproducible.

No se observa DMs, webhooks, bots, propietario, personal autorizado o canales trampa. Exenciones globales y por regla, ámbito interpretado, permisos, audiencia y restricciones de edad se aplican antes de leer/descargar señales y antes de publicar. La revisión por regla impide que un mensaje exento contribuya a otro umbral por accidente.

## Interfaz y tres idiomas

Detección muestra estado global guardado, total, categorías vigilables/parciales, ambiguas/contradictorias, revisión humana, sin prohibición, deshabilitadas, no disponibles, revisión y fecha nativa Discord. Analizar, Revisar, Corregir, Guardar, Descartar y Volver actualizan el mismo panel con ACK temprano y bloqueo de concurrencia.

La revisión muestra texto completo por páginas, sentido normativo, categorías, mecanismos, alcance, citas de prohibiciones/obligaciones/permisos, excepciones, condiciones, referencias y limitaciones. Las notas no se traducen. Exenciones tiene sus propios selectores globales/por regla y Guardar/Descartar; no contiene detectores ni activación.

Solo el panel principal dispone de Activar/Pausar. Guardan únicamente `custodio_observe_policy_v1.enabled`, sin arrastrar otros borradores. Activar requiere plan aprobado vigente, canal privado e intents guardados. Pausar funciona sin Groq, red ni Screening. Las revisiones históricas, consultas y herramientas manuales centrales siguen disponibles.

3322 claves de catálogo revisadas y compatibles en es-419/en-US/pt-BR; 3292 referencias reales en código, auditoría estática sin literales pendientes. Esos recuentos no acreditan todos los recorridos reales. Se conservan advertencias parciales de idiomas con el texto del encargo inicial, identificadores/comandos y footer `El Heraldo's Labs 🧪`.

## Disciplina central y evidencia NH

Custodio utiliza Advertencias, expedientes, Condenas y expiradores centrales; no crea disciplina paralela. Las cinco medidas se conservan: Solo reportar, Warn, Temp Ban, Expulsar y Ban. Todas requieren revisión administrativa explícita y revalidación de permisos, jerarquía, regla fresca y evidencia completa. Cualquier solicitud `automatic=True` se rechaza.

Una advertencia comparte límite e historial y renueva treinta días sin reincidencia de esa conducta. Alcanzar el límite NO llama al escalado automático desde Custodio. Una condena adicional o cualquier otra medida central requiere su autorización independiente; las configuraciones previas de otros módulos no se alteran. Los expedientes y listas muestran origen Custodio/manual/otros módulos. El origen y el estado interno sobreviven a edición de notas y cierre; las notas personalizadas se muestran intactas. Una medida cumplida cierra solo advertencias de la misma conducta.

La evidencia privada contiene origen, autor, servidor/canal, fecha nativa Discord, cita literal, regla literal, señal y medida. Se divide sin truncar; la audiencia del destino no puede ampliar la del origen. Un ledger durable reclama antes del primer envío, con referencias mínimas. Se revalida el estado global y la configuración antes de cada parte. Si se pausa en medio, el resultado queda pendiente de revisión y no se reenvía como completo después de reiniciar.

Eliminar el original retira solo su enlace; conserva la transcripción y referencia del reporte. La reconciliación histórica está acotada y no depende de activar la observación. No se borran evidencias anteriores ni se afirma haber migrado todos los archivos históricos ajenos al módulo.

## Pruebas y medición

- Local: 1064 componentes (1062 correctos, dos omisiones históricas) y 39 regresiones raíz correctas. Tras la suite, 14 focalizadas verifican también la nueva exclusión de menciones implícitas de respuestas. CI comprobará el árbol publicado exacto.
- Las nuevas pruebas ejecutan paneles, modales, callbacks, permisos, borradores, CAS, navegación, estado global, correcciones, separación de canales/servidores, proveedor malformado, cuota, caché, fuente revisada, inyección, concurrencia, reinicio, entrega parcial y medidas centrales con Discord aislado.
- El primer intento completo encontró una prueba heredada que exigía el import del adaptador textual anterior. Se sustituyó por un recorrido ejecutable con proveedor ausente, sin HTTP ni guardado; la suite repetida pasó.
- Compilación, gramática Python 3.11, `pip check`, catálogo/variables/markup y auditoría de textos correctos. La matriz CI incluye 3.11/3.12/3.13 y UX. El fallo histórico de Issue 23 es `Production baseline changed; reconcile before preparing candidate`, confirmado en el job 122401267853; no se cambia producción para resolverlo.
- Corpus [fuente sintética](../data/custodio_evaluation_cases.json), evaluador `python tools/evaluate_custodio.py --output docs/CUSTODIO_EVALUATION.json` y [resultados completos](CUSTODIO_EVALUATION.json): 417 escenarios × tres sensibilidades = 1251 ejecuciones; 216 TP, 0 FP, 513 TN, 81 FN conocidos fuera de ventana y 441 abstenciones humanas. Desglose por categoría/idioma/sensibilidad. Precisión y recall son nulos cuando no corresponde medirlos; no se concede precisión ficticia a categorías humanas.
- Medición local del evaluador: 1514 ms con tracemalloc, pico trazado 1726929 bytes. No representa CPU/RAM ni capacidad de Railway. Las cifras del corpus no se extrapolan a personas, servidores o lenguas no evaluadas. Incluye actividad legítima de varios autores, citas, ejemplos, saludos y evasiones deliberadas.

## Groq y Railway: comprobado frente a pendiente

Ya comprobado: `d99b298` en worker de Lab, deployment `e92901b8-b417-4a48-9120-c727d18718cd`, SUCCESS. Groq `openai/gpt-oss-20b` realizó inferencia real sobre una regla sintética en 428 ms; JSON Schema y cita validados. [Recibo](CUSTODIO_PROVIDER_DEPLOYMENT.json). CI Lab 40562341587 y Mensajes 40562341644 SUCCESS. El modelo anterior gratuito estaba retirado; se corrigieron modelo, tokens insuficientes, lectura HTTP fragmentada y rechazo de respuestas truncadas.

La nueva sonda `tools/custodio_analysis_health.py` solo opera en proyecto/entorno Lab exactos, lee reglas auténticas con Bot autorizado y valida el motor completo sin SQLite, mensajes o activación. Solo imprime revisión, recuentos y metadatos. Su resultado y el nuevo deployment se añadirán aquí tras observarlos; un éxito de esta sonda no acredita el clic de Discord.

## Aceptación real pendiente

La sesión de usuario de Discord no permitió completar recorridos: error de segundo factor y después conexión WebSocket no operativa. No se reinician intentos de autenticación ni se extraen tokens de usuario. El uso del bot autorizado permite verificar reglas y proveedor por separado.

Recorrido exacto al disponer de sesión operativa: **Heraldo's Lab → `/setup` → AutoMod → Modo Custodio → Detección → Analizar reglas → Revisar interpretación**. Comprobar en los tres idiomas categorías/ámbitos/límites y ausencia de selector manual; Guardar debe aprobar, Descartar no escribir, Volver regresar al submenú anterior. En Exenciones, seleccionar no debe guardar. Activar/Pausar aparecen únicamente en el panel principal.

Para observar eventos reales hace falta un miembro voluntario sin permisos/roles exentos: el propietario y moderadores están protegidos. Verificar mensajes sintéticos autorizados, reporte privado provisional, pausa, borrado del original y conservación de copia. Warn/Temp Ban reales requieren participante voluntario y confirmación individual; no se ejecutaron sanciones sobre miembros reales.

Pendientes: aceptación interactiva autenticada, observaciones con participante voluntario, medidas controladas y capacidad real bajo carga de Railway. Las 49 categorías humanas y eventos no implementados (DM, reacciones ajenas, hilos/foros y evasión por ediciones) siguen limitados. Rollback: volver a fijar el worker a d99b298 sin borrar `/data`; los campos nuevos son metadatos ignorados por la versión anterior. No se modifica main, producción ni H-03 para revertir.
