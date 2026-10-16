## Semántica uniforme de controles — 2026-10-16

Para Mensajes y /setup se acuerda: rojo para eliminación, descarte y sanción; verde para guardar/publicar/activar; azul para editar o preparar opciones sin guardar; gris para cancelar, volver o vista previa. Es prioritario que el color represente la acción efectiva, no solo el texto: un botón que abre un modal es azul aunque permita preparar algo positivo; una confirmación de eliminación es roja aunque diga «Confirmar». Los botones externos Discord usan estilo link propio. Lote de colores implementado en Pruebas (`c32141eb`, CI 3.11–3.13 SUCCESS), Discord real pendiente. **Petición funcional pendiente, no ejecutada aquí:** sustituir «Revisar programación» por «Guardar cambios», introducir «Descartar cambios» con reversión y reemplazar «3. Configurar condición» por un nombre específico del modo; después extender guardado explícito sin revisión redundante a otros editores. La nota anterior sobre «Revisar» corresponde al comportamiento heredado, no a la nueva intención aprobada.

## Calidad editorial y claridad de los controles — 2026-10-15

Toda pantalla administrativa debe usar español correcto, explicar el efecto concreto de cada acción y evitar mensajes contradictorios. Preferir descripciones humanas a JSON, saltos de línea visibles y estados precisos. Separar «Revisar», «Confirmar» y «Cancelar»; los selectores y formularios no guardan por sí mismos. Se aplicó al programador de embeds en Pruebas, con verificación real pendiente; ampliar el estándar progresivamente a los demás editores.

## Nombres naturales de embeds personalizados — 2026-10-15

En Pruebas, /embed admite nombres Unicode legibles con espacios, tildes y emojis, máximo 64 caracteres. Identificador canónico en crear, editar, enviar, borrar y autocompletar; no cambia publicaciones previas. Pendiente validación interactiva de Discord y CI. Los demás editores no se consideran terminados por este ajuste.

## Patrón de claridad para editores de /setup — 2026-10-15

En `Pruebas` se reorganizó el editor de Reportes: elección de reacción y acción contiguas; `Configurar condiciones` sustituye a `Regla`, con explicación de número de personas distintas, duración de sanción y purga de mensajes. Las opciones irrelevantes no aparecen en el modal. `Sanciones y límite` permite habilitar/deshabilitar tipos de sanción y elegir la acción al máximo WARN con confirmación. Este es el patrón aprobado para extender progresivamente a otros editores (etapas claras, etiquetas específicas, menús para opciones cerradas, vista previa y cancelación sin persistencia), no una afirmación de que todos los paneles ya estén modernizados. Pendiente auditoría y aceptación Discord de los demás editores.

## Uniformidad adicional de editores — 2026-10-15

En Pruebas, Miembro de la Semana → Horario y Moderation → Reportes sustituyen entradas textuales de opciones cerradas por selectores, manteniendo parámetros personalizados y la confirmación antes de guardar. Es una mejora transversal de /setup, distinta de la finalización del editor visual de Mensajes. Pendiente probar ambos editores en Discord y extender el mismo criterio a otros módulos con opciones conocidas, sin sustituir campos de texto libre.

# Plan de integración: /setup → Mensajes (referencia Sapphire)

## Estado vigente para revisión — 2026-10-10

Esta tabla sustituye las casillas históricas que se conservan debajo como registro de etapas. No acredita pruebas interactivas ni paridad completa con Sapphire.

| Área | Implementado en PR #7 | Pendiente |
| --- | --- | --- |
| Plantillas | Texto, hasta diez embeds, variables, JSON, editor visual de campos/autor/pie/imágenes y confirmación | Navegación uniforme y validación Discord |
| Componentes | Botones/menús independientes, selección múltiple, multiacción confirmada, permisos y auditoría | Editor visual de acciones y selección persistente por miembro |
| Kits | v1/v2, archivo, reemplazo confirmado, portabilidad visual | Enlace/ID seguro y comparación por campo |
| Automatizaciones | Programación, autorespuestas, sticky y webhook propio | Recorrido real y reinicios |
| Predeterminados | Estudios de cinco familias y editor de Logs; formularios Honeypot confirmados | Catálogo completo y Raw/restauración uniforme |

Ver `REVISION_PR7.md` para límites, ejemplo JSON y recorrido de aceptación. Revisión de código preparada; no es una declaración de alcance total completado.

## Registro histórico de etapas

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

### Programación implementada y límites — 2026-10-10
- Programación puntual, diaria y semanal con zona IANA, propuestas confirmadas, listado de estado y retirada: implementada mediante /programar_mensaje. Estado SQLite y permisos comprobados en ejecución; pendiente ensayo real.
- Recuperación conservadora: envíos inciertos requieren revisión; los vencimientos durante desconexión se agrupan en una publicación, sin ráfagas de recuperación.
- Texto independiente validado también frente al hook global; pies/embeds explícitos no se alteran tras su validación.
- Las casillas históricas anteriores describen etapas previas. Autorespuestas, sticky, webhooks y componentes multiacción continúan pendientes. La documentación Sapphire no devolvió contenido legible mediante consulta web; no se ha verificado paridad completa con esa referencia.
- Verificación del lote más reciente: 78 pruebas offline aprobadas, compilación y dependencias correctas; CI nueva e interacciones todavía pendientes.

### Fase 5 ampliada — 2026-10-10
- Implementadas autorespuestas literales por canal con configuración confirmada y límites persistentes.
- Implementado sticky por canal con conservación del estado y reposición limitada por actividad; al retirar se conserva la publicación final.
- Implementado envío manual confirmado por webhook propio del bot, sin persistir credenciales. Los componentes interactivos de roles usan publicación directa del bot.
- Estas funciones tienen regresiones offline, pero no pruebas reales Discord. Continúan pendientes componentes multiacción, menús independientes, editor visual completo y catálogo general. No afirmar paridad completa con Sapphire.


## Auditoría y propuestas de catálogo — 2026-10-11
PR #12 separa visualmente mensajes oficiales de personalizados; esa modificación ya estaba implementada y no se repite. La auditoría local añade cobertura de navegación real, corrigiendo su invocación. La propuesta de nombres fijos Condena/Perdón/Verificación/Advertencia y editor uniforme está documentada en audit/PROPUESTAS_Y_PLAN_REAL.md para decisión del propietario; no implica migración ni eliminación de plantillas guardadas. La cobertura actual y vacíos se consultan en audit/MATRIZ_COBERTURA.md.

## Continuación del editor visual — 2026-10-12
Rama temporal Codex `codex/h03-recuperacion-20261012`: selector de embeds limitado a los existentes; selector de hasta 25 campos con nombre, valor e inline precargados en el modal. La selección mantiene borrador/versión y no guarda automáticamente. Cambiar embed invalida formularios anteriores, retirar embed reconstruye selectores y permisos revocados bloquean el modal. Cuatro regresiones nuevas y suites de Mensajes/Reaction Roles previas correctas, sin prueba Discord real. No se completaron editor visual de acciones, importación segura por enlace/ID, comparación por campo ni catálogo uniforme; permanecen pendientes.
