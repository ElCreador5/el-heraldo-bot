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
