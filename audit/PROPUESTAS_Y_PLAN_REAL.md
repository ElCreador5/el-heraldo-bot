# Propuestas de producto y plan supervisado

Estas propuestas no cambian configuraciones existentes. El propietario decide su adopción; ChatGPT puede coordinarlas a partir de este archivo compartido.

## Simplificación propuesta

1. **Entrada directa a secciones:** conservar la intención de PR #12, con el fallo técnico del selector corregido. Una elección abre el panel; no repetir «Configurar».
2. **Mensajes oficiales con nombres fijos:** presentar Condena, Perdón, Verificación, Bienvenida de verificación, Advertencia, Sugerencias, Honeypot y Registros. Mostrar las plantillas libres en Mensajes personalizados. Usar alias visuales hacia las claves actuales, sin renombrar ni borrar datos persistidos. Perdón/Advertencia requieren primero identificar propiedades hoy compartidas o codificadas.
3. **Editor común:** elegir mensaje → editar → vista previa → Guardar/Cancelar. Imágenes, colores y campos avanzados en un panel secundario. JSON como opción avanzada, nunca requisito del recorrido básico.
4. **Reportes:** elegir Reportar/Condenar/Aislar/Expulsar/Banear en un selector; mostrar por separado umbral, duración y eliminación de contenido. Decisión requerida: impedir purga en «Solo reportar» o cambiar el nombre para revelar ese efecto. No modificar silenciosamente reglas guardadas.
5. **Confirmaciones privadas:** mantener el resumen y resultado de configuración en el panel efímero del administrador. Conservar un log administrativo cuando corresponda; no publicar un aviso adicional al canal de uso. Diferenciarlo de tarjetas de sanción y avisos de seguridad.
6. **Expedientes:** mantener el código estable; mostrar «Condena» o «Advertencia» como título y código en un campo discreto. No cambiar referencias de casos existentes. Quitar solo formato técnico que no aporte trazabilidad.
7. **Navegación y lenguaje:** uniformar Atrás, Vista previa, Guardar cambios y Cancelar; español formal. No retirar emojis funcionales de Reaction Roles o reportes. Nombres ingleses, pies históricos y textos personalizados requieren tratamiento compatible.

## Laboratorio antes del servidor real

Usar el recorrido REVISION_PR7.md actualizado con la matriz de esta auditoría. Reservar a intervención humana solamente: ejecución slash desde cuenta de prueba, clic/select/modal, reacción de un participante, DM abierto/cerrado y valoración visual. Se preparan los valores y se registra el resultado, sin automatizar su cuenta. Toda prueba de moderación requiere participante de prueba y captura previa de roles; no elegir personas por inactividad.

Los ensayos automatizados locales pueden simular permisos, HTTP, duplicados, concurrencia y SQLite. Las consultas Railway confirman estado de despliegue y arranque; no simulan clics Discord. No enviar payloads de interacción falsificados ni usar credenciales de usuario.

## Plan para el servidor real (no autorizado)

- Pendientes del propietario: nombre/ID del servidor, autorización explícita para conectar El Heraldo Test, responsable local y participantes voluntarios. No se conecta ni activa nada por defecto.
- Antes de conectar: verificar aplicación y credenciales de Test, base/volumen separados de producción, permisos mínimos y respaldo restaurable. Crear una propuesta de canales/roles de prueba y alcance para aprobación.
- Primera etapa: observación autorizada y pruebas de configuración sin sanciones ni purgas. No registrar texto de conversaciones; guardar únicamente resultado técnico agregado y errores necesarios.
- Segunda etapa, solo con autorización específica: asignar/quitar un rol ordinario de prueba a participantes consentidos, condena reversible sin purga y posterior perdón. Capturar estado previo, comprobar restauración exacta y detener si falla.
- Excluir expulsiones/baneos experimentales, borrado de contenido real, purgas masivas y cambios a roles de producción. No habilitar automatismos de seguridad globales durante el ensayo.
- Condiciones de parada: destino inesperado, permiso excesivo, notificación duplicada, rol no restaurado, incertidumbre de envío o dato privado en registros. Pausar la función de prueba y conservar el estado necesario para recuperación.
- Cierre: verificar roles originales, desactivar reglas de prueba, acordar retención mínima y retirar recursos solo tras confirmar que no contienen información necesaria.

Producción requiere otra aprobación explícita, separada de este plan y de la integración de laboratorio.
