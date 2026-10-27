# Modo Custodio — implementación y verificación

Actualización: 27 de octubre de 2026. Desarrollo exclusivo en `Pruebas`; producción fuera de alcance.

## Estado

El núcleo de observación y la revisión administrativa están implementados y probados sin red. **No se declara aceptado en Discord ni preparado para activar sanciones automáticas.** La observación necesita guardar detectores por regla y pulsar Activar; no se enciende al desplegar, abrir un menú o cambiar un selector.

La primera fase de idiomas está validada automáticamente y desplegada; los recorridos de usuario siguen pendientes por el error de segundo factor de Discord. Esa limitación no bloquea el desarrollo seguro de Custodio. No se necesitan credenciales de una cuenta personal para consultar reglas con el bot autorizado.

| Función | Implementación y límites comprobados |
| --- | --- |
| Reglas auténticas | `custodio_source.py`: Screening activo, campos TERMS, huella de revisión por servidor, respuestas limitadas y fallos cerrados. Autorización Bot estable; no seguir redirecciones con credenciales. |
| Texto y enlaces | `custodio_detection.py`: repetición exacta, textos casi idénticos, enlaces repetidos, publicidad con enlace y llamada comercial, menciones masivas y saturación. Son indicadores provisionales vinculados por el administrador a una regla concreta. |
| Entre canales y miembros | Repetición de un mismo actor entre canales; patrón coordinado exige contribución propia repetida y varios actores. No se atribuye culpa colectiva. La actividad normal del canal aumenta el umbral de saturación. |
| Imágenes | SHA-256 y dHash con Pillow; imágenes poco informativas no se consideran similares por un hash trivial. Máximo cuatro imágenes de 1 MiB, cuatro millones de píxeles, una decodificación simultánea y ninguna copia en disco. |
| Memoria | Ventana de 90 segundos, 4096 señales como máximo y contadores separados por regla, incluidas las exenciones de sus mensajes previos. Huellas compartidas para el mismo mensaje sin unir historiales; limpieza aunque no lleguen mensajes. Revisiones y limitadores por servidor acotados. Acceso frecuente a SQLite fuera del bucle de interacciones. |
| Exenciones | Propietario y personal autorizado antes de analizar contenido; roles y canales globales y por regla. Bots, webhooks y canales trampa excluidos. Sin lectura de DMs. |
| Privacidad | El destino privado no puede ampliar la audiencia del origen. Un origen restringido por edad exige destino igualmente restringido; las exclusiones individuales impiden la copia automática. Se revalida antes de cada envío. |
| Evidencia NH | `heraldo_evidence.py`: autor, servidor/canal, instante nativo de Discord, copia literal, regla literal, observación y medida. Las descripciones mecánicas de adjuntos se rotulan como tales. Se dividen envíos a 6000 caracteres y diez embeds sin perder partes. |
| Persistencia | El texto permanece en Discord. Los índices y el ledger existentes guardan solo referencias, revisión, estado e identificadores mínimos. Reclamación durable antes del envío; un resultado incierto no se reenvía ni se presenta como completo. |
| Mensaje borrado | Eventos individuales y masivos retiran solo el enlace del original. La transcripción permanece. Recuperación de referencias tras reinicios y reconciliación limitada a los últimos 32 reportes por servidor, mediante rango indexado. No se inspecciona el historial completo. |
| Revisión | Botón Revisar recuperable tras reiniciar mediante el evento de interacción. Solo propietario o administrador; confirmación individual, permisos, jerarquía, regla fresca y evidencia completa. Descartar no ejecuta. |
| Cinco medidas | Solo reportar, Warn, Temp Ban, Expulsar y Ban. `custodio_discipline.py` utiliza las funciones centrales, no un sistema disciplinario paralelo. Cualquier llamada automática se rechaza en esta etapa. |
| Advertencias | Límite compartido con el bot; treinta días sin reincidencia de la misma conducta de Custodio. El historial se conserva. Una medida cumplida cierra solo las advertencias de esa conducta; no cierra advertencias manuales ajenas. DM amable tras advertencia registrada. |
| Condenas | Se respeta el escalado central de Advertencias cuando el administrador ya configuró Condenas. Custodio no añade una sexta sanción ni cambia condenas existentes. |
| Temp Ban | Duración guardada por regla, expediente antes de la petición remota y reloj actualizado tras confirmación. El expirador existente confirma el desbaneo, conserva casos ante fallos y no levanta un baneo posterior con otra razón. Una petición incierta no se repite ni se da por cumplida antes de confirmarse. |
| Ban permanente | Duración explícita cero al motor compartido; no hereda accidentalmente el valor temporal predeterminado de Test. Sin purga implícita. |
| Interfaz | Detección y Exenciones operativas; selectores recordados, guardar/descartar y CAS. Activar/Pausar guardan únicamente su estado y conservan otros borradores. Reglas largas completas por páginas. Volver retorna al submenú anterior y conserva los borradores de Detección, Exenciones y Acciones; una revisión nueva invalida el borrador anterior. Sensibilidad se guarda con un clic y CAS; los guardados en curso bloquean ediciones y navegación hasta terminar. Español, inglés y portugués brasileño. |

## IA manual: impedimento real y alternativa

`custodio_ai_runtime.py` implementa una llamada manual acotada a Groq, modelo `openai/gpt-oss-20b` (sustituto vigente del anterior modelo gratuito retirado), endpoint fijo, un único texto de regla y salida JSON validada. No recibe mensajes, perfiles ni herramientas. La cita debe coincidir exactamente con la regla; toda interpretación es una propuesta y no modifica acciones. El adaptador y sus controles se probaron con transporte aislado, **no mediante una inferencia real**.

Lectura de metadatos del 27/10: el worker ya dispone de los nombres `CUSTODIO_AI_FREE_PROVIDER` y `CUSTODIO_GROQ_API_KEY`; no se leyeron sus valores. La presencia de ambas variables no acredita una inferencia válida. No se han creado cuentas, contratado servicios, añadido secretos ni generado solicitudes facturables. Sin configuración, el botón informa de que se necesita revisión humana.

Recursos observados en Lab: 0,512 GB de RAM y 1 vCPU; el bot utiliza aproximadamente 0,160 GB, con pico observado de 0,298 GB. El fabricante publica 434 MB de pico para LFM2.5-350M Q4 en su benchmark; sumarlo al proceso existente no demuestra un margen seguro en este servicio. No se carga un modelo local sin una medición propia que demuestre viabilidad. Esto no equivale a afirmar que ningún modelo pequeño pueda ejecutarse.

Alternativa segura actual: interpretación humana y revisión individual de reportes. Para probar inferencia gratuita, el propietario puede configurar en **Railway Test → Lab → worker → Variables** `CUSTODIO_AI_FREE_PROVIDER=groq` y la clave de una cuenta gratuita en `CUSTODIO_GROQ_API_KEY`; no debe enviarla por chat. Después debe ejecutarse una inferencia real antes de aceptar la IA. Ninguna de estas variables afecta H-03.

Fuentes primarias consultadas:

- [Discord: Guild y limitación de Membership Screening](https://docs.discord.com/developers/resources/guild). El canal oficial `rules_channel_id` tiene contrato público, pero no es un sustituto silencioso del objeto Screening ni garantiza el mismo texto. Se conserva la fuente exacta y se falla cerrado si Discord la rechaza.
- [Groq: modelos](https://console.groq.com/docs/models) y [contrato de Chat Completions](https://console.groq.com/docs/api-reference#chat-create).
- [Railway: plan Free](https://docs.railway.com/pricing/plans).
- [Liquid AI: benchmark LFM2.5-350M](https://www.liquid.ai/blog/lfm2-5-350m-no-size-left-behind).

## Comprobaciones realizadas

- Suite completa local: 1004 pruebas de componentes, 1002 aprobadas y dos omisiones históricas; 39 regresiones de raíz aprobadas. Total: **1041 aprobadas**, dos omitidas.
- 52 pruebas nuevas cubren detectores, ámbitos, memoria, política por revisión, callbacks reales, duración, exenciones, privacidad, reportes concurrentes, entrega parcial/timeout, reinicios, eliminación, cinco medidas centrales, advertencias compartidas, expiración real del adaptador con transporte aislado y revisiones administrativas.
- Matriz de los nuevos paneles en los tres idiomas, reglas de longitud máxima, 25 roles/canales y límites reales de componentes. Gramática Python 3.11, compilación, auditoría de catálogo y `pip check` correctos.
- Los dobles de Discord y del proveedor de IA están identificados como aislados. Ninguna sanción sobre miembros reales acredita estas pruebas.
- Primer lote `1ddd2cd2bbc9efbb460523c968cd80944c49f166`: CI Lab [40516525314](https://github.com/ElCreador5/el-heraldo-bot/actions/runs/40516525314) SUCCESS (3.11/3.12/3.13 y UX), Mensajes [40516525547](https://github.com/ElCreador5/el-heraldo-bot/actions/runs/40516525547) SUCCESS; worker deployment `a71a6d8f-fd85-45fb-9961-7706f262091b` SUCCESS. Sonda real de lectura: doce reglas oficiales, revisión `f2ada923edd532c667c9b6f1ede92ff6157ca3e730d21d08572ddb910e35d8eb`. Gateway conectado, dos autopruebas de setup y dos sincronizaciones de 51 comandos correctas. El candidato productivo sigue fallando por su referencia base histórica; no se altera main.
- La revisión final de aislamiento por regla y navegación se publica tras estas regresiones; su CI y despliegue exactos se añadirán al recibo.
- Medición local reproducida con mensajes de hasta 3900 caracteres y dieciséis reglas: aproximadamente 65,7 ms por mensaje antes de reutilizar huellas y 4,3 ms después (veinte mensajes, sin red). No es una medición de capacidad ni latencia de Railway.

## Protección de H-03 y publicación

El cron vigila `/requirements*.txt`; se preservaron esos archivos. Pillow se declara en `custodio_image_deps.in`, se instala en CI y se instalará exclusivamente mediante el build de worker. No se cambian las variables, horarios, volúmenes ni fuente del servicio de respaldos. No se modifica `main` ni producción.

## Aceptación pendiente y continuidad

1. Confirmar CI y despliegue del SHA exacto en worker de Lab; comprobar la lectura real de Screening con la sonda de metadatos y el arranque.
2. En el Discord habitual del propietario: **Heraldo's Lab → `/setup` → AutoMod → Modo Custodio**. Abrir Reglas del servidor y recorrer una regla larga con Anterior/Siguiente. En Detección seleccionar una regla y un detector, comprobar que elegir no guarda, guardar y reabrir; comprobar Exenciones y Descartar. Crear Reportes solo mediante su confirmación si no existe.
3. La detección necesita un miembro voluntario sin roles exentos: el propietario y los moderadores están protegidos. Comprobar texto idéntico, casi idéntico, enlaces, imágenes, actividad normal, reglas modificadas, permisos revocados y reinicio. Debe aparecer una observación provisional privada, sin sanción automática. Borrar su original debe conservar la copia y retirar el enlace.
4. En un reporte completo, Revisar muestra la medida de esa regla. Descartar no actúa; Confirmar autoriza solo esa medida. Warn y Temp Ban reales requieren participante de pruebas voluntario. Comprobar desbaneo confirmado, expediente e historial; no ensayar sobre miembros productivos.
5. La IA requiere inferencia real con proveedor gratuito; hasta entonces se mantiene revisión humana. La activación sancionadora automática y la aceptación de producción continúan bloqueadas.
6. Continuar la adopción universal del formato NH en los archivos/expedientes heredados: este lote aporta el componente común, reportes de Custodio y referencias mínimas en sus casos. No afirma haber migrado todos los registros históricos ni haber retirado las transcripciones de todos los flujos antiguos. No borrar evidencias previas.
