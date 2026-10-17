# H-03: auditoría de producción y preparación de respaldos previos

Auditoría: 2026-10-17, 22:25 UTC (18:25 America/Santo_Domingo).
Activación: **BLOQUEADA por recuperación independiente de clave sin verificar**.

## Estado comprobado

| Elemento | Evidencia actual |
| --- | --- |
| main | c6a5c1642d84b776e522473d62cf92c60e018cb3 |
| Pruebas, base del candidato | 13b08382e16880d432b486082c1525a36946093a |
| Railway producción | El Heraldo, entorno El Paraíso; Online, 1 réplica, sin cambios pendientes |
| Despliegue actual | b2426f15-4826-4e22-9cd1-90ff3573d41b, SUCCESS; main, creado 2026-10-17 13:20:57 UTC |
| Persistencia declarada por Railway | heraldo-data, 500 MB, /data, servicio productivo |
| Variables productivas configuradas | DB_PATH, DISCORD_TOKEN, MESSAGE_CONTENT_INTENT; sin H-03 habilitado |
| Inicio / disponibilidad | python bot.py; sleepApplication=true; checkSuites=false |
| Cron diario existente | Railway Test: heraldo-h03-lab-cron, 15 6 * * *, volumen propio; SQLite sintética |
| Supabase | Proyecto ACTIVE_HEALTHY; bucket heraldo-sqlite-backups privado |
| Última copia real productiva | 2026-10-13 22:09:20 UTC / 18:09:20 Santo Domingo; una generación de 100609 bytes |
| Copias Lab | Cuatro generaciones; última 2026-10-16 06:18:09 UTC |

La consulta de Storage leyó únicamente metadatos agregados. No descargó SQLite,
claves ni manifiestos. La extensión .h03e acredita el nombre esperado, no permite
comprobar el ciphertext ni la integridad de su contenido. La restauración del
13/10 consta en un informe histórico de Codex local; **no se repitió hoy**.
No hay evidencia de respaldos diarios reales de producción. La ausencia de logs
H03 en la consulta y la configuración sin secretos son coherentes con ese estado.

Se recuperaron AGENTS.md y los siete documentos solicitados desde el SHA de
Pruebas y se inspeccionaron los cuatro módulos H-03 en ambas ramas: los módulos
eran idénticos antes de este trabajo. La documentación de octubre 14 contiene
SHA históricos distintos: no se usaron como estado actual. Git fetch y lectura
de los commits remotos confirmaron las dos revisiones de la tabla.

## Clave, aislamiento y límites de acceso

La documentación vigente indica que la clave original fue importada a una nota
privada de Bitwarden, pero su recuperación desde sesión/dispositivo independiente
y el descifrado desde esa copia quedaron aplazados hasta noviembre. No existe
evidencia posterior suficiente que cierre ese requisito. No se tocó, regeneró,
volvió a importar ni transportó la clave. No es seguro rotarla para sortear la
carencia: la generación existente requiere conservar su clave original.

El conector Railway permite leer configuración y nombres de variables, pero no
ejecutar en el contenedor ni recuperar valores secretos con esta conexión OAuth.
No hay CLI Railway autenticada en este entorno. Por tanto, el plano de control
confirma la asignación del volumen, **no una lectura real de SQLite desde aquí**.

Las políticas actuales de Storage son INSERT y SELECT para una misma identidad
técnica restringida al bucket, sin UPDATE ni DELETE. No restringen las carpetas
Lab/producción: el aislamiento de identidades/prefijos en el servidor es todavía
insuficiente para activar producción. Preparar identidad productiva propia y
políticas por prefijo conservando acceso de recuperación a generaciones antiguas.
No modificar a ciegas la cuenta existente ni borrar objetos para separar entornos.

## Código preparado, sin integración productiva

Rama temporal Codex derivada de Pruebas, destinada a PR contra Pruebas:
codex/h03-production-gate-20261017. La excepción de AGENTS.md permite este flujo;
no se publica directamente en Pruebas ni se fusiona en main en esta sesión.

- backup_job.py amplía H-03 con purpose=preupdate, request_id de 32 hex y SHA
  exacto de origen/candidato. Cada actualización crea una nueva generación,
  workspace y recibo; no consume ni bloquea la copia diaria del mismo día.
- sqlite_recovery.py incluye esa operación en el manifiesto que ya cifra y
  autentica AES-256-GCM. Un recibo local manipulado no permite usar una copia
  diaria antigua como autorización: se comprueba de nuevo el manifiesto remoto.
- preupdate_gate.py descarga y autentica otra vez el objeto, valida SHA,
  integridad/FK, entorno, esquema, recuentos y contenido mediante restauración
  a archivo nuevo. Rechaza candidato/origen distintos, recibos futuros o de más
  de 15 minutos desde inicio, procesos de más de 10 minutos y resultados inciertos.
- guarded_update conserva el lock hasta terminar el controlador confiable,
  reserva durablemente una autorización de un solo uso antes de invocarlo y exige
  confirmación explícita de finalización (True). Un error, muerte o resultado no
  confirmado requiere reconciliación; no se reintenta ni borra el recibo.
- Ambos propósitos usan la raíz productiva única /data/.heraldo-h03-daily y su
  flock; no se puede elegir otra raíz en producción para eludir concurrencia.
- Se verifican identidad de proyecto/entorno/servicio, nombre y ruta de volumen
  documentados por Railway, montaje real con ismount/mountinfo, DB_PATH y revisión
  desplegada. No se asume que exista RAILWAY_VOLUME_ID. Pre-deploy sin volumen
  queda bloqueado; no se configura allí ningún respaldo productivo.
- El diario conserva 06:15 UTC / 02:15 Santo Domingo, inactivo sin configuración.
  Generaciones anteriores, descargas, restauraciones y recibos se conservan.
  No se alteró bot.py, esquema funcional, condenas, roles, moderación o mensajes.

**Límite importante:** son primitivas verificadas, todavía no una barrera
obligatoria operativa. El CLI prepare/verify no publica ni concede permiso a
una publicación posterior fuera de guarded_update. El controlador que publique
debe comprobar sus refs actuales y desplegar exactamente el candidato autorizado.
Un callback remoto asíncrono/que solo encole el despliegue no satisface el contrato.
La escritura normal del bot no se congela durante una copia online.

## Protección de main y despliegues pendiente

El ruleset activo Protección de main exige PR y python-checks con rama
actualizada, sin bypass actors. No exige una comprobación H-03 ni aprobación de
revisor (required_approving_review_count=0). Railway source.checkSuites=false.
La lectura del endpoint clásico de branch protection devolvió 403; el ruleset
completo sí pudo leerse. No se escribió ninguna regla ni configuración.

Después de cerrar recuperación y antes de publicar el candidato:

1. Establecer un controlador protegido y ejecutor autenticado capaz de ordenar
   una ejecución dentro del servicio dueño de /data, sin iniciar Discord otra vez.
   No ejecutar código no revisado de un PR con secretos productivos.
2. Generar el candidato final con base main fijada y comprobar su contenido final;
   ligar el respaldo a ese SHA. Si cambia main o el candidato/resultado de merge,
   invalidar la autorización y crear una nueva copia. No reutilizar el recibo diario.
3. Exigir una comprobación H-03 del controlador y revisión en las reglas de main,
   sin vías de bypass, y canalizar también redeploys y cambios de configuración
   por el controlador. Un check verde en GitHub por sí solo no protege una acción
   directa desde Railway. Restringir accesos directos o adoptar otra barrera de
   ejecución validada antes de afirmar que cada despliegue está protegido.
4. Comprobar realmente rechazos por objeto inaccesible, clave incorrecta,
   restauración fallida, recibo vencido y SHA cambiado, tanto antes de main como
   antes del despliegue. Sin esas pruebas, la barrera no se declara activa.

## Secuencia de activación y recuperación

Intervención manual indispensable: con Codex local en un entorno privado,
recuperar la clave original desde la segunda custodia independiente, descargar
la copia productiva y descifrar/restaurar a un destino nuevo y aislado. Conservar
una constancia saneada del resultado y fecha, sin clave, objetos, hashes privados
ni contenidos. Esta sesión no puede realizar ese paso por el propietario.

Después: configurar secretos propios mediante canales privados, verificar cuota
y acceso al volumen, producir una instantánea NUEVA real previa a cualquier
cambio productivo y repetir descarga/restauración. Incorporar únicamente H-03
revisado; cerrar el controlador obligatorio. Mantener disponible el proceso que
ejecuta el diario, resolviendo sleepApplication=true bajo ese mismo respaldo
previo. Activar el horario 06:15 UTC y observar la primera ejecución real completa,
el recibo y la generación externa nueva. Verificar alertas en el monitor existente,
sin crear monitores duplicados. **No hay una próxima ejecución productiva
confirmada mientras estos requisitos sigan pendientes.**

Recuperación: recuperar credenciales y clave desde custodia independiente;
descargar la generación elegida a directorio privado, autenticar GCM y validar
SQLite/FK/esquema; restaurar primero a archivo nuevo sin Gateway. Para reinstalar
en producción hace falta autorización separada, detener todos los escritores,
conservar base/WAL/SHM originales y seguir RESPALDOS_RECUPERACION.md con versión
compatible. Reconciliar acciones Discord posteriores antes de arrancar. Un
respaldo SQLite no contiene adjuntos/evidencias externos de Discord.

Conservación sin borrado: el volumen de 500 MB y Storage Free son finitos; H-03
bloquea cuando no hay espacio y requiere supervisión de crecimiento. Supabase
Free puede pausarse; no constituye otro destino independiente adicional.

## Validación y entrega

Pruebas nuevas: tests/test_preupdate_gate.py; SQLite y AES-GCM reales sintéticos,
transporte HTTP y controlador de publicación simulados. Cubren independencia de
generaciones, montaje ausente, prefijos/origen, integridad/FK, manipulación de
ciphertext, copia diaria disfrazada, fallo de descarga/restauración, expiración,
bloqueo concurrente, consumo durable y resultados inciertos. No son un ensayo
actual contra Supabase real ni contra la SQLite productiva.

Regresiones locales finales: 482 tests/ + 39 raíz = **521 aprobadas** en Python
3.12 (22 nuevas específicas). Compilación, pip check y git diff --check correctos.
CI del commit y estado de revisión: consultar la PR de esta rama temporal.

Railway y Supabase: solo lecturas; sin variables, políticas, objetos o servicios
creados/modificados. Main y producción: sin commits, fusiones o despliegues de
esta sesión. No se inició ningún bot ni prueba real Discord. Honeypot permanece
aplazado hasta que ambos respaldos estén operativos y verificados; no se prepara
una fusión total de Pruebas.
