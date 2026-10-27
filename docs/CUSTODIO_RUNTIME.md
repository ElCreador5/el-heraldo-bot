# Modo Custodio — configuración y verificación

Estado vigente: 27/10/2026, exclusivamente `Pruebas` y worker de Lab. Informe técnico único, versiones, cobertura y límites: [CUSTODIO_EVOLUTION.md](CUSTODIO_EVOLUTION.md). **La aceptación interactiva en Discord sigue pendiente; no se habilitan sanciones automáticas.**

## Recorrido administrativo

1. En Heraldo's Lab, abrir `/setup → AutoMod → Modo Custodio`. El panel muestra el estado global guardado. La sensibilidad es un borrador hasta Guardar cambios.
2. Reglas del servidor consulta Screening auténtico y muestra cada texto completo por páginas. Consultar no guarda, no activa observación y no llama a IA.
3. Detección → Analizar reglas solicita interpretación ocasional. El panel informa progreso y distingue reglas con señales, cobertura parcial, ambigüedad, revisión humana, sin prohibición y no disponibles.
4. Revisar interpretación muestra texto completo, prohibiciones/obligaciones/permisos, categorías, mecanismos derivados, alcance, excepciones y límites. No existe lista de detectores para construir manualmente.
5. Corregir interpretación permite suspender una propuesta por interpretación incorrecta, conducta permitida, excepción, falso positivo, ambigüedad o deshabilitación. Aplicar al borrador no persiste; la nota propia permanece intacta. Restaurar revierte la corrección de la misma revisión. Guardar cambios en Detección aprueba explícitamente el plan; Descartar recupera lo guardado.
6. Exenciones es independiente: roles y canales globales o por regla. Los selectores solo preparan cambios, Guardar los aplica y Descartar los abandona. El propietario y personal autorizado siempre están protegidos.
7. Reportes permite utilizar/crear el canal privado mediante su confirmación específica. Deben cumplirse permisos y compatibilidad de audiencia, incluidas restricciones de edad. Crear el canal no activa Custodio.
8. Activar/Pausar existe solo en el panel principal. Activar requiere interpretación aprobada, reglas vigentes, señales locales, canal privado válido e intent de contenido. Pausar funciona sin red ni proveedor. Ambos guardan solo su estado y conservan borradores ajenos.

Volver conserva el borrador y retorna al submenú anterior. Los guardados usan control de concurrencia; una sesión antigua no sobrescribe cambios de otra. Al cambiar las reglas se requiere revisar/aprobar la nueva interpretación. Las exenciones globales se conservan al aprobar otra revisión; las de una regla modificada deben revisarse de nuevo, no se copian por número a una norma distinta.

## Observación provisional

El motor no llama IA por mensaje. Usa 16 mecanismos locales para 24 categorías de la [taxonomía](CUSTODIO_TAXONOMIA.md); las otras 49 son de revisión humana. Una coincidencia es una señal revisable, nunca una determinación de culpa. No se evalúan DMs ni contenido de propietario, moderadores, bots, webhooks, canales trampa o ámbitos exentos.

Historial acotado: huellas de 90 s / 4096 eventos; ventanas separadas por regla/servidor, contribución propia y sensibilidad. Las menciones de respuesta automáticas no equivalen a pings explícitos. Citas y código se excluyen del análisis textual sin alterar la copia literal. Imágenes acotadas y sin archivos en disco. No se abren enlaces externos para determinar fraude.

La configuración y el interruptor se revalidan antes de cada envío de evidencia. Si se pausa entre partes, las ya publicadas permanecen y el ledger queda pendiente de revisión, sin repetición automática. El reporte contiene origen, autor, canal, fecha nativa Discord, texto exacto, regla, señal y medida. El texto se conserva únicamente en Discord; SQLite guarda referencias y metadatos mínimos. Borrar el original retira su vínculo, no la copia. Las referencias sobreviven a reinicios; reconciliación histórica limitada a 32 reportes por servidor.

## Revisión y disciplina compartida

Revisar en un reporte completo recupera las cinco medidas guardadas: Solo reportar, Warn, Temp Ban, Expulsar y Ban. Se exige propietario/administrador actual, regla fresca, evidencia completa, permisos y jerarquía; Confirmar autoriza solo la medida mostrada y Descartar no actúa. La pausa de observación no bloquea consultas ni revisiones manuales históricas.

Los casos y advertencias utilizan el sistema central, sin disciplina paralela. El origen Custodio/manual aparece en expediente, listas y registros. Las notas administrativas y el origen se conservan tras edición/cierre. Las advertencias comparten límite e historial y renuevan treinta días sin reincidencia de esa conducta. Llegar al límite no ejecuta escalado automático desde Custodio. Las condenas y configuraciones centrales previas se conservan y requieren su propia autorización.

Temp Ban registra duración explícita y caducidad antes de la operación, confirma el desbaneo y preserva un baneo posterior ajeno. Un resultado incierto no se repite. Ban permanente no hereda el valor temporal predeterminado de Test. No existe purga implícita.

## Verificación disponible

Pruebas aisladas de paneles, modales, callbacks, tres idiomas, reglas auténticas con transporte simulado, excepciones, cuotas, caché, cambios de revisión, concurrencia, privacidad, reinicio, entrega parcial y disciplina central. [Corpus reproducible y métricas](CUSTODIO_EVALUATION.json): 417 escenarios sintéticos, 1251 ejecuciones, falsos negativos conocidos conservados y abstención explícita para categorías sin detector fiable. No representa eficacia en usuarios reales.

Proveedor real: Groq `openai/gpt-oss-20b`, inferencia sintética validada en d99b298 ([recibo](CUSTODIO_PROVIDER_DEPLOYMENT.json)). La sonda del análisis de reglas auténticas solo emite metadatos y no guarda/activa nada. El estado exacto del nuevo deployment se registra en el informe tras comprobar SUCCESS, Gateway y sincronización de comandos.

Pendiente en Discord Test: recorrido autenticado de los paneles en tres idiomas, eventos de un participante voluntario no exento, pausa durante entrega, borrado del original y revisión individual de Warn/Temp Ban con consentimiento. No se ejecutaron sanciones sobre miembros reales. No se modifica producción, main ni H-03; no se cambian volúmenes o credenciales.
