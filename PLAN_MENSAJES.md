# Plan de integración: /setup → Mensajes (referencia Sapphire)

## Referencia y alcance
- Fuente: https://docs.sapph.xyz/#/messages
- Componentes: https://docs.sapph.xyz/#/guides/guide-to-components
- El objetivo es paridad de experiencia y funcionalidades, sin replicar material propietario de Sapphire.
- Mantener español formal, sin emojis decorativos, configuraciones aisladas por servidor y permisos comprobados por interacción.

## Fase 1: Navegación y conservación de editores (implementada en rama)
- [x] Entrada Mensajes en menú principal de /setup.
- [x] Centralización de accesos a verificaciones, sugerencias, honeypot, condenas y logs.
- [x] Almacenamiento de plantillas por servidor.

## Fase 2: Plantillas (parcialmente implementada)
- [x] Crear, editar, borrar, previsualizar y publicar embeds con título, descripción, imagen HTTPS y enlace.
- [x] Vincular botón de rol o menú de roles a una plantilla.
- [ ] Contenido de texto independiente del embed, varios embeds, miniaturas, pies, autores y campos.
- [ ] Editor JSON Raw con validación de esquema.
- [ ] Variables dinámicas por contexto; impedir menciones automáticas no deseadas.
- [ ] Edición de publicaciones existentes mediante enlace/ID con verificación de autoría.
- [ ] Vista previa de todos los componentes y experiencia de navegación uniforme.

## Fase 3: Componentes (parcialmente implementada)
- [x] Botones de rol (añadir, quitar, alternar), con comprobaciones de jerarquía y permisos.
- [x] Menú de selección de roles y reconstrucción de acciones después de reiniciar.
- [ ] Editor independiente de cada menú/opción y varias acciones secuenciales con resultado visible.
- [ ] Mensaje al usuario (público o efímero), mensaje en canal, mensaje directo.
- [ ] Editar o eliminar mensaje, usando autorización y prevención de abuso.
- [ ] Más opciones de rol, selección múltiple y mantener selección.
- [ ] Política de acciones privilegiadas, rate limits, límites de componentes y auditoría.

## Fase 4: Kits (parcialmente implementada)
- [x] Exportación JSON de plantillas sin secretos ni acciones de permisos.
- [x] Importación manual de JSON con comprobación de tipos y límites.
- [ ] Importación de archivo de kits grandes, enlace/ID seguro, vista previa de diferencias.
- [ ] Confirmación explícita antes de reemplazo, versionado y restauración.
- [ ] Portabilidad de valores visuales y compatibilidad por versión.

## Fase 5: Uso y automatizaciones (pendiente)
- [ ] Enviar y editar mediante comando.
- [ ] Programación puntual/recurrente con zona horaria configurada.
- [ ] Auto-respuestas por palabra clave con controles anti-spam.
- [ ] Mensajes fijados al final (sticky) sin duplicados ni bucles.
- [ ] Mensajes por webhook con validación de destino y credenciales seguras.

## Fase 6: Mensajes predeterminados (pendiente)
- [ ] Catálogo completo de mensajes de El Heraldo, por clave estable y origen.
- [ ] Preview / Visual / Raw / Variables y restauración por evento.
- [ ] Migrar solo textos editables; no permitir alterar identificadores internos ni evidencia, permisos o estados reales.
- [ ] Cuando un campo no sea aplicable a un caso de condena, omitirlo.

## Calidad y despliegue (no verificados)
- [ ] Ejecutar `python -m py_compile bot.py`.
- [ ] Ejecutar `python -m unittest test_regressions.py` y ampliar casos.
- [ ] Pruebas reales en servidor de prueba: botones, desplegables, mensajes efímeros, roles y reconexión.
- [ ] Probar roles superiores, rol administrado, falta de permisos, eliminación de plantilla, reinicios y varios servidores.
- [ ] Revisar permisos antes de publicar y logs de error.
- [ ] Aprobar PR, fusionar y desplegar solo tras completar verificaciones.

## Problemas conocidos en la rama actual
- El panel de importación sustituye las plantillas actuales sin confirmación; requiere paso de confirmación antes de producción.
- El componente de menú comparte el catálogo de roles del servidor, aún sin editor individual de opciones.
- Se requiere ejecutar pruebas de sintaxis y servidor; la conexión de GitHub no ejecuta automáticamente código Python.
