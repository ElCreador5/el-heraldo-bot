# Modo Custodio — evolución autorizada y trazabilidad

Encargo integral recibido el 27/10/2026. Desarrollo exclusivamente en `Pruebas`;
Railway Test → Lab → worker. Sin producción, cambios de H-03 ni sanciones automáticas.

## Punto de partida comprobado

- HEAD remoto inicial: `9aa06fcdbcab9d249332842baee42aa9a634207a`.
- Se conservan las correcciones de `7eac8af` (interruptor global) y `9aa06fc` (sin Integraciones).
- Worker inicial: `9caeb22cfbb3580756e62cb25042a257060ac8dc`, deployment
  `a7f6d657-0de4-4a2a-82be-1fc811305318`, SUCCESS. Todavía no contiene los dos últimos fixes.
- `main`: `32c9f5dcc8505a3d6aacde76533d6b60dd88a542`; no se escribe ni se despliega.
- Volumen de worker `/data` conservado. Ninguna escritura de datos privados ni cambio del cron.
- Detección local, reglas auténticas, evidencia privada durable, revisión humana y cinco
  medidas centrales ya existen. No se reimplementan.
- La asignación por regla era manual y el panel compartía Detección/Exenciones.
  La IA solo devolvía una propuesta textual; no hay interpretación normativa estructurada guardada.
- Groq tiene variables presentes. No se han leído ni exportado sus valores.

## Secuencia y estado

| Etapa | Estado | Comprobación de salida |
| --- | --- | --- |
| Inventario y límites de seguridad | Comprobado | HEAD, arquitectura, Test y main contrastados. |
| Proveedor actual y transporte acotado | Implementación inicial | 51 pruebas focalizadas y 1012 componentes (dos omitidas) correctos; CI e inferencia auténtica por acreditar. |
| Investigación y fichas de conductas | En curso | Fuentes oficiales/estudios, ejemplos sintéticos, capacidad y límites por categoría. |
| Interpretación versionada y planificador | Pendiente | Sin detectores para saludos; excepciones/negaciones/contradicciones y revisión fresca. |
| Contexto y correcciones auditables | Pendiente | Ventanas y recursos acotados, aislamiento, revisiones y correcciones reversibles. |
| Detección y Exenciones independientes | Pendiente | Sin lista manual de detectores, navegación/guardado/ACK y tres idiomas. |
| Interruptor y disciplina/evidencias | Pendiente de ampliación | Estado justo antes de efectos, origen central y preservación de evidencia histórica. |
| Evaluación, CI, publicación y Lab | Pendiente | Métricas reproducibles, SHA exacto, SUCCESS y arranque; separar clics reales. |

El trabajo continúa entre etapas. Este documento es un checkpoint, no una aceptación final.

## Proveedor: fallo identificado y validación pendiente

La documentación oficial retira `llama-3.1-8b-instant` de Free/Developer el
16/08/2026 y recomienda `openai/gpt-oss-20b`. Se actualiza ese modelo fijo, sin
fallback a modelos Enterprise ni nuevas cuentas/contratos. El presupuesto anterior
de 280 tokens podía truncar la cita de reglas largas y el JSON; se ajusta de forma
acotada y se exige terminación completa. El lector de HTTP acumula fragmentos bajo
un límite de bytes, en vez de suponer que la primera lectura devuelve todo el cuerpo.

La sonda `tools/custodio_ai_health.py` hará una petición auténtica con una regla
sintética, sin Discord ni SQLite. Solo imprimirá modelo, estado, validación y latencia;
nunca claves, reglamentos ni razonamientos. Esto acredita proveedor/contrato si pasa,
pero no equivale a pulsar un botón en Discord. La ruta de interfaz conserva su
aceptación separada y no se atribuye un clic a una prueba con dobles.

Fuentes oficiales verificadas el 27/10/2026:

- [Retirada de modelos](https://console.groq.com/docs/deprecations#august-16-2026-llama318binstant-and-llama3370bversatile).
- [Modelos y acceso](https://console.groq.com/docs/models).
- [JSON Schema y límites de JSON Object](https://console.groq.com/docs/structured-outputs).
- [Contrato de Chat Completions](https://console.groq.com/docs/api-reference).
- [Cuotas y cabeceras del proveedor](https://console.groq.com/docs/rate-limits).

## Condiciones invariables

El reglamento es dato no confiable y autoridad del servidor, nunca instrucciones de
sistema. No se envían mensajes de miembros al proveedor. Una señal es provisional;
la IA no autoriza castigos. Categorías semánticas que no pueden comprobarse de forma
fiable permanecen en revisión humana. Propietario, personal, roles/canales exentos,
ACL y restricciones de edad se conservan antes del análisis y antes de efectos.

Guardar/Descartar y CAS se mantienen; Activar/Pausar solo guardan su estado.
Pausar no depende del proveedor ni de la lectura de reglas. Las revisiones antiguas
no pueden autorizar efectos nuevos. Evidencia literal en Discord e índices mínimos;
no se duplican conversaciones en SQLite/Supabase. Los nombres propios, comandos,
valores persistentes y textos personalizados no se traducen.

La aceptación final requiere pruebas reales diferenciadas de unitarias e integración.
No se declara 100 % ni se elimina el estado parcial de idiomas por un CI verde.
