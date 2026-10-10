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

## Laboratorio de calidad (2026-10-09)
- Preparar verificaciones offline ejecutadas por GitHub Actions antes de incorporar cambios a `Pruebas`.
- Separar rigurosamente resultados CI, despliegues Railway y pruebas reales de Discord; no declarar paridad funcional sin las tres evidencias pertinentes.
- Nunca ejecutar interacciones destructivas en miembros reales ni automatizar cuentas personales; un futuro bot de pruebas auxiliar requerirá autorización, aislamiento y alcance explícitos.

## Etapa 1 autorizada — 2026-10-09 (America/Santo_Domingo)
- La reconciliación incorpora el historial de `main@6f9f9ee` al desarrollo conservando las funciones de `Pruebas@b8480b8`. Los conflictos no justifican eliminar Mensajes ni las confirmaciones de restauración de Logs.
- Preparar la integración en el PR #6; fusionar con un commit de merge (no squash ni rebase) para conservar la ascendencia de `main` y resolver la divergencia histórica.
- CI valida Python 3.11, 3.12 y 3.13 con `discord.py==2.7.1` en `requirements-ci.txt`. Las dependencias transitivas no están bloqueadas; no afirmar reproducibilidad completa. `requirements.txt` y el runtime de Railway permanecen sin cambio en esta etapa.
- La preparación y publicación del PR no acredita pruebas Discord. La fusión hacia `Pruebas` puede activar Railway y debe tratarse como integración en laboratorio; `main` y producción requieren autorización independiente.

## Seguridad y formatos — 2026-10-10
- Las acciones públicas de roles no deben conceder permisos administrativos (administrador, gestión de servidor/roles/canales/webhooks, expulsión, baneo o moderación), ni permitir eludir una condena activa. Se revalida al ejecutar para detectar cambios posteriores del rol.
- Una evidencia parcial no acredita copia íntegra ni permite purgar su mensaje de origen. No usar el canal de condenados como archivo alternativo.
- Kits v2 contienen únicamente valores visuales; se admiten v1 y v2, se excluyen acciones y vínculos privilegiados. Los reemplazos son optativos, confirmados y sujetos a comprobación de cambios concurrentes.
- Las variables son una lista cerrada, no expresiones ejecutables; se validan límites después de expandirlas y se deshabilitan menciones automáticas.
- La autorización vigente permite desarrollar y preparar el laboratorio; no autoriza modificaciones en main ni producción. Las funciones todavía pendientes no se consideran completadas por aprobar pruebas offline.

### Recuperación de ingresos — 2026-10-10
- Los trabajos conocidos de Join Roles se almacenan antes de esperar; el reinicio no reinicia el contador. La ejecución consulta estado actual y no debe otorgar roles durante una condena.
- Los formularios migrados adjuntan el cambio propuesto y anterior; las publicaciones asociadas se sincronizan únicamente después del guardado confirmado.

### Programación de Mensajes — 2026-10-10
- Se valida la zona horaria al crear y se rechazan horas locales inexistentes o ambiguas. Repetición diaria/semanal conserva la hora local; durante un salto de primavera, una futura hora inexistente se normaliza a la hora real posterior al salto.
- Ante incertidumbre de envío se pausa esa programación para revisión; no se garantiza entrega exactamente una vez entre SQLite y Discord. Crear otra exige revisar el canal. La plantilla se resuelve al ejecutar, por lo que sus modificaciones confirmadas afectan futuros envíos.
- Los diseños explícitos de Mensajes no reciben el formato global automático, para conservar texto independiente, pies propios y límites validados. El resto de las respuestas mantiene el comportamiento previo.
