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
- [x] Editor JSON Raw con validación de esquema básica.
- [ ] Variables dinámicas por contexto; impedir menciones automáticas no deseadas.
- [x] Edición de publicaciones existentes mediante enlace con verificación de autoría del bot y confirmación explícita.
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
- [x] Importación manual de JSON con comprobación de tipos, límites y detección de conflictos (sin sobrescritura).
- [ ] Importación de archivo de kits grandes, enlace/ID seguro, vista previa de diferencias.
- [ ] Versionado, importación de kits grandes y restauración opcional bajo confirmación.
- [ ] Portabilidad de valores visuales y compatibilidad por versión.

## Fase 5: Uso y automatizaciones (pendiente)
- [x] Enviar mediante /sendtemplate, con autocompletado y comprobación de permisos.
- [x] Editar publicaciones existentes mediante /edittemplate, solo mensajes propios y con confirmación del administrador.
- [ ] Programación puntual/recurrente con zona horaria configurada.
- [ ] Auto-respuestas por palabra clave con controles anti-spam.
- [ ] Mensajes fijados al final (sticky) sin duplicados ni bucles.
- [ ] Mensajes por webhook con validación de destino y credenciales seguras.

## Fase 6: Mensajes predeterminados (pendiente)
- [ ] Catálogo completo de mensajes de El Heraldo, por clave estable y origen.
- [ ] Preview / Visual / Raw / Variables y restauración por evento.
- [ ] Migrar solo textos editables; no permitir alterar identificadores internos ni evidencia, permisos o estados reales.
- [ ] Cuando un campo no sea aplicable a un caso de condena, omitirlo.

## Confirmación obligatoria de administrador
- [x] Los modales de plantilla, JSON, componente de rol, vinculación y kits generan un borrador pendiente y solo persisten tras botón de confirmación.
- [x] Eliminar plantilla exige una confirmación separada.
- [x] Cancelar descarta la propuesta sin alterar la configuración guardada.
- [x] Publicar mensajes sigue siendo una acción explícita del administrador; guardar no publica ni edita mensajes ya enviados.
- [ ] Comprobar en servidor de pruebas las confirmaciones, caducidad y cambios concurrentes.

## Calidad y despliegue (verificación automatizada parcial)
- [x] Ejecutar `python -m py_compile bot.py` (etapa 1, 2026-10-09; ver registro de pruebas).
- [ ] Ejecutar `python -m unittest test_regressions.py` y ampliar casos.
- [ ] Pruebas reales en servidor de prueba: botones, desplegables, mensajes efímeros, roles y reconexión.
- [ ] Probar roles superiores, rol administrado, falta de permisos, eliminación de plantilla, reinicios y varios servidores.
- [ ] Revisar permisos antes de publicar y logs de error.
- [ ] Aprobar PR, fusionar y desplegar solo tras completar verificaciones.

## Problemas conocidos en la rama actual
- La importación actual no reemplaza plantillas; rechaza los nombres repetidos. Todavía necesita un flujo de revisión de diferencias.
- El componente de menú comparte el catálogo de roles del servidor, aún sin editor individual de opciones.
- Sintaxis y regresiones existentes verificadas en la etapa 1; las ampliaciones de cobertura y las pruebas interactivas siguen pendientes. Consultar `PRUEBAS_DISCORD.md` para entorno y alcance.

## Avance real — 2026-10-10
- Fase 2: texto independiente, múltiples embeds y propiedades avanzadas disponibles por JSON/kit; variables usuario, usuario_id, servidor, servidor_id, canal y fecha; preview desactiva acciones. Falta editor visual completo y navegación uniforme.
- Fase 3: se refuerzan jerarquía, política de roles administrativos, condenas activas, concurrencia y frecuencia. Menús independientes, acciones secuenciales, mensajería y auditoría por acción siguen pendientes.
- Fase 4: kit v2, compatibilidad v1, archivo JSON mediante /importkit (128 KiB), resumen de nombres añadidos/reemplazados y confirmación con rechazo de borradores obsoletos. Falta comparación detallada por campo e importación segura por enlace/ID.
- Fases 5 y 6 siguen pendientes salvo envío/edición manual previamente existentes. No se declara paridad con Sapphire.
- Verificación offline del lote: 64 pruebas aprobadas; validación interactiva y CI remoto del lote pendientes.
