# Internacionalización de El Heraldo — cobertura real

Revisión de `Pruebas`, 25 de octubre de 2026 (República Dominicana). Base de trabajo: `b7b177b3abd422bee9b1fc4605de175eac15e4a7`. `main` y producción no se modifican.

## Estado

**Integración transversal implementada y verificada automáticamente; aceptación integral PENDIENTE.** No se acredita el 100 % ni se retiran las advertencias de desarrollo.

- Catálogo común: **3000 claves** en `es-419`, `en-US` y `pt-BR`, con paridad de variables comprobada.
- **397 claves con revisión explícita** de textos/control o heredadas del catálogo manual. **2603 claves** continúan en la cola editorial, disponible en `locales/editorial_status.json`.
- `tools/i18n_audit.py` descubre claves realmente referenciadas y literales nuevos. Exenciones técnicas revisadas: **152**, con archivo, ámbito, texto y motivo. No son traducciones pendientes: incluyen SQL, parsers, nombres reales, marcas, contratos HTTP/GraphQL, CLI de mantenimiento y datos sintéticos.
- Las propuestas iniciales se generaron localmente; **no equivalen a revisión profesional completa**. El bot no carga modelos ni consulta servicios de traducción en ejecución. Dependencias de Railway sin cambios.

## Módulos integrados

| Área | Integración y comprobación |
| --- | --- |
| `/setup`, Idioma y `/language` | Selector, etiquetas, descripciones, placeholder y panel por servidor. IDs originales y preferencia SQLite compartida. |
| AutoMod y Honeypot | Paneles, borradores, confirmaciones, avisos y errores; exclusión de operaciones y ACK conservados. |
| Moderación, condenas y advertencias | Casos, sanciones, botones, registros y mensajes privados; clasificadores de títulos por procedencia canónica. |
| Verificación de edad y personalidad | Paneles, modales, plantillas predeterminadas, recuperación y expulsiones; variante para elección bloqueada. |
| Protección antirraid | Configuración, avisos, resúmenes y acciones administrativas. |
| Roles de ingreso y por reacción | Paneles y formularios; entradas traducidas normalizadas a valores internos históricos. |
| Registros, expedientes y evidencias | Etiquetas y mensajes; citas literales, razones personalizadas y nombres reales conservados. |
| Mensajes, plantillas, automatizaciones y componentes | Editores, errores, ayudas, guardado y salidas automáticas; contenido del administrador intacto. |
| Modo Custodio | Subpaneles, acciones por reglas/tipos, informes y ayudas de configuración. |
| DMs y tareas automáticas | Contexto de servidor por evento/fila persistida; los formularios de salida conservan el servidor de origen. |

## Contratos preservados

- Los selectores no guardan. Guardar confirma la configuración reversible; los efectos sensibles conservan sus confirmaciones.
- Navegación anterior, permisos, distribución de botones y pie `El Heraldo's Labs 🧪` con icono real.
- No se usa `interaction.locale`. Los contextos se restauran incluso con errores y tareas concurrentes.
- Los nombres de comandos, IDs, claves, recursos y contratos internos conservan su identidad. Los mensajes personalizados no se traducen, aunque coincidan con un texto predeterminado.
- Sin cambios en sentencias SQL de `bot.py`, esquema, datos persistidos, secretos, volumen ni reglas de sanción.

## Pruebas

- 27 pruebas específicas: catálogos, variables, referencias reales, nuevos literales, preferencias compartidas, aislamiento, guardado/descartar, permisos, DMs, contexto concurrente y serialización real.
- Matriz: nueve módulos principales × tres idiomas, con comprobación de que abrirlos no escribe SQLite. Modales, evidencia literal y formularios persistentes de DM ejecutados sin Gateway.
- Suite `tests`: 935 pruebas; dos omisiones existentes. Regresiones de raíz: 39 pruebas. Compilación, gramática Python 3.11, `pip check` y `git diff --check`.
- Las pruebas AST históricas usan `tests/i18n_source_helpers.py` para recuperar únicamente la presentación española. **Las pruebas nuevas de i18n examinan y ejecutan el código real**, sin esa adaptación.
- CI incorpora auditoría y pruebas de idioma. El resultado remoto del commit y el recibo Railway se registran después de publicarlo.

## Pendientes que impiden declarar 100 %

1. Revisar editorialmente la cola completa de traducciones, especialmente mensajes extensos y formulaciones poco habituales. La paridad de claves no demuestra fidelidad semántica.
2. Acreditar los recorridos profundos y la aceptación visual/interactiva en Discord Test. Las pruebas sin Gateway no acreditan clics reales del cliente.
3. Los esquemas globales existentes de comandos nativos (descripciones y opciones de registro) siguen en español; no se introduce el idioma personal del usuario para simular preferencia por servidor.
4. Las plantillas guardadas se respetan como contenido configurado. No se reclasifican ni reescriben automáticamente textos heredados sin procedencia fiable.

Mientras estos puntos sigan abiertos, inglés y portugués brasileño permanecen habilitados con las advertencias exactas solicitadas, en sus respectivos idiomas.

## Publicación

Destino autorizado: proyecto Railway Test, entorno Lab, servicio `worker`. Se fija el commit validado y se conserva `/data`. No se crea otro servicio ni se modifica producción. El recibo se añade tras verificar despliegue, arranque y Gateway.
