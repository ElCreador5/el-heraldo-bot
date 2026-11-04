"""Textos en español para los paneles trasladados selectivamente a producción."""
import contextlib
DEFAULT_LOCALE = "es-419"
COPY = {'setup.command_panels.0431b91d103e553b': 'Embeds guardados · Seleccionado: **{name}**', 'setup.command_panels.07bc1bb22be369da': 'Selecciona un embed primero.', 'setup.command_panels.16b4767d4dab390d': 'Selecciona un rol o miembro para eximir.', 'setup.command_panels.1f79528b4202efaf': 'Nombre del embed', 'setup.command_panels.2d0559112e6cc3e6': 'Servidor no válido.', 'setup.command_panels.2d8f7575782917c1': 'Selecciona un rol o miembro.', 'setup.command_panels.2eba946b2e1ee4b6': 'Editar', 'setup.command_panels.309d6636fc507d9c': 'Seleccionar miembro', 'setup.command_panels.30fa2af415be15d8': '¿Eliminar el embed **{name}**?', 'setup.command_panels.34aea5df170fb68e': 'Honeypot no está pausado.', 'setup.command_panels.34fa2f8a42f7faba': 'Todavía no hay activaciones registradas.', 'setup.command_panels.3fe5ff266fc3ceac': 'Crear', 'setup.command_panels.4c08a5d5feb22ce2': 'Título', 'setup.command_panels.4f9fc6fa30d68389': 'Selecciona un embed guardado', 'setup.command_panels.514552f5e299dc08': '¿Retirar la exención de {target}?', 'setup.command_panels.55310704fe331dd9': 'Selecciona el canal para publicar el embed.', 'setup.command_panels.5685e1faf0b38db2': 'Reanudar', 'setup.command_panels.58ce15cf794ffeec': 'Historial de Honeypot', 'setup.command_panels.6e5af853ff2b7184': 'Retirar exento', 'setup.command_panels.7200d89ca4e980bc': 'Ese embed ya no existe.', 'setup.command_panels.734a0ccc7e94c08c': 'Seleccionar rol', 'setup.command_panels.89368b9efc84fd80': 'Este panel pertenece a otra persona.', 'setup.command_panels.921330c4fc13d798': 'Canal: <#{channel}> · Acción: {action}', 'setup.command_panels.98e5acddb6c46a24': 'Estado', 'setup.command_panels.995c071dfaee74ce': 'Historial', 'setup.command_panels.a0fa1571a0f31a07': 'Panel de Honeypot: configuración, historial y exenciones.', 'setup.command_panels.ab26ae7bca362195': 'Volver', 'setup.command_panels.ac95cb30997bf12e': 'Administrador de embeds. Crea, selecciona, edita y envía manualmente desde aquí.', 'setup.command_panels.ade1d68cb1da4a40': 'Nombre no válido.', 'setup.command_panels.b1bfce419aba730f': 'Añadir exento', 'setup.command_panels.b3714638af061456': 'Disponible solo en servidores.', 'setup.command_panels.b4bb6c6db58f7c78': 'Confirmar eliminación', 'setup.command_panels.b5cfc01de602841d': 'Eliminación cancelada.', 'setup.command_panels.b853e5d5c8434dd8': 'Activaciones totales: {count}', 'setup.command_panels.bb507137e3631379': 'Configuración', 'setup.command_panels.be0999a4268c9788': 'Panel cerrado.', 'setup.command_panels.bfd4d4976e84d705': 'Ya existe un embed con ese nombre.', 'setup.command_panels.c1c85b2e96cd397e': 'Terminar y liberar', 'setup.command_panels.c2331660ed48ae57': 'Crear embed', 'setup.command_panels.c9894cf002f90bd0': 'Eliminar', 'setup.command_panels.confirm_send': 'Confirmar envío', 'setup.command_panels.create_review': 'Revisa el embed **{name}** y confirma para guardarlo.', 'setup.command_panels.d2502f6a21b56077': 'Terminar raid', 'setup.command_panels.d92c888e6c513411': '¿Eximir a {target}?', 'setup.command_panels.e1d12d1a29a77b00': 'Enviar', 'setup.command_panels.eda23027fb8ea533': 'Protección anti-raid: configuración, estado y control manual.', 'setup.command_panels.ee00b96fff266fe2': 'Descripción', 'setup.command_panels.embeds_hub': 'Administrador de embeds. Selecciona un mensaje o crea uno nuevo.', 'setup.command_panels.f2cdbbed31f9c0bc': 'Iniciar raid', 'setup.command_panels.f8251e3c1e21a29b': 'Embed eliminado.', 'setup.command_panels.honeypot': 'Panel de Honeypot: configuración, historial y exenciones.', 'setup.command_panels.manual_raid': 'Activación manual por {user}', 'setup.command_panels.name_exists': 'Ya existe un embed con ese nombre. Elige otro nombre.', 'setup.command_panels.raid_confirm_end': '¿Finalizar el modo raid y restaurar las invitaciones que pausó El Heraldo?', 'setup.command_panels.raid_confirm_release': '¿Finalizar el modo raid y liberar las condenas asociadas a este raid?', 'setup.command_panels.raid_confirm_start': '¿Activar ahora el modo raid con la configuración guardada?', 'setup.command_panels.raid_unavailable': 'El estado del modo raid no permite esta acción. Actualiza el panel.', 'setup.command_panels.send_review': 'Revisa el embed para {channel}. Solo se publica al confirmar el envío.', 'setup.commands.choose_module': 'Módulo del bot', 'setup.commands.choose_type': 'Tipo de comando', 'setup.commands.close': 'Cerrar', 'setup.commands.empty': 'No hay comandos con estos filtros.', 'setup.commands.help.action': 'Ejecuta una operación concreta.', 'setup.commands.help.administration': 'Mantenimiento y recuperación del servidor.', 'setup.commands.help.configuration': 'Abre un panel para administrar un módulo.', 'setup.commands.help.consultation': 'Consulta información sin modificar datos.', 'setup.commands.invalid': 'Selecciona una opción válida.', 'setup.commands.module.all': 'Todos los módulos', 'setup.commands.module.announcements': 'Anuncios', 'setup.commands.module.automod': 'AutoMod', 'setup.commands.module.general': 'General', 'setup.commands.module.logging': 'Registros', 'setup.commands.module.messages': 'Mensajes', 'setup.commands.module.moderation': 'Moderación', 'setup.commands.module.roles': 'Roles', 'setup.commands.module.structure': 'Estructura del servidor', 'setup.commands.module.verification': 'Verificación', 'setup.commands.title': 'El Heraldo · {category}', 'setup.commands.type.action': 'Acciones', 'setup.commands.type.administration': 'Administración', 'setup.commands.type.configuration': 'Configuración', 'setup.commands.type.consultation': 'Consultas', 'setup.structure.choose': 'Frecuencia del respaldo de estructura', 'setup.structure.closed': 'Panel cerrado.', 'setup.structure.confirm': 'Confirma el horario mostrado para guardar. Volver conserva el borrador.', 'setup.structure.confirm_button': 'Confirmar cambios', 'setup.structure.conflict': 'La configuración o su programación cambió en otra sesión. Abre nuevamente el panel.', 'setup.structure.draft': 'Borrador: {mode}\nHora local: {hour}:00 · Día semanal: {weekday} (0 lunes–6 domingo)\nDía del mes: {monthday} · Intervalo: {interval} minutos.\nLa selección solo se guarda al confirmar.', 'setup.structure.expired': 'Este borrador ya cambió o está cerrado. Abre nuevamente el panel.', 'setup.structure.help.daily': 'Una copia al día a la hora local elegida.', 'setup.structure.help.interval': 'Repite la copia cada cierto número de minutos.', 'setup.structure.help.monthly': 'Una copia cada mes en el día y hora elegidos.', 'setup.structure.help.off': 'No sincroniza automáticamente la estructura.', 'setup.structure.help.weekly': 'Una copia en el día semanal y hora elegidos.', 'setup.structure.hour': 'Hora local (0–23)', 'setup.structure.interval': 'Intervalo en minutos (1–43200)', 'setup.structure.invalid': 'Revisa los valores y sus intervalos permitidos.', 'setup.structure.mode.daily': 'Diaria', 'setup.structure.mode.interval': 'Por intervalo', 'setup.structure.mode.monthly': 'Mensual', 'setup.structure.mode.off': 'Desactivado', 'setup.structure.mode.weekly': 'Semanal', 'setup.structure.module_description': 'Respaldo de roles, canales y permisos del servidor', 'setup.structure.module_label': 'Estructura del servidor', 'setup.structure.monthday': 'Día del mes (1–28)', 'setup.structure.schedule': 'Editar horario', 'setup.structure.title': '**Respaldo de estructura: roles, canales y permisos**', 'setup.structure.unsaved': 'Hay cambios pendientes. Guárdalos o descártalos antes de volver.', 'setup.structure.weekday': 'Día semanal (0 lunes–6 domingo)', 'text.08e419babf38d0': 'Esta propuesta ya se resolvió.', 'text.14bdfaf2face3a': 'Guardar cambios', 'text.27a254b7d1a5b1': 'Error: No pude encontrar ese canal.', 'text.3682162eb7d367': '*(embed vacío: usa ✏️ Contenido para escribirlo)*', 'text.3ef181ed6e0a1e': 'La configuración seleccionada ya está guardada. No hay cambios pendientes.', 'text.50e5928d81367b': 'Elige el canal de destino…', 'text.58dfe5d6f9dce5': 'Cambio cancelado. No se guardó la exención.', 'text.7c37f6a003372a': 'El rol seleccionado ya no existe.', 'text.80ca383e9c8d3e': 'Descartar cambios', 'text.ab26ae7bca3621': 'Volver', 'text.aeccae342e4bd0': 'Cerrar', 'text.bb9dbb406dcbd5': 'Cancelar', 'text.c090afeb021325': 'Exención retirada.', 'text.d099457cd0e5b2': 'No se pudo comprobar la pertenencia del miembro.', 'text.d767fd87be203e': 'Exención guardada.', 'text.da10e9d8927c80': '**El Heraldo · Moderación**\n\nConfigura las funciones de moderación disponibles.'}

def text(key, **values):
    return COPY[key].format(**values)

def translate(locale, key, **values):
    return text(key, **values)

def guild_context(function):
    return function

def use_guild(guild_id):
    return contextlib.nullcontext()

def variants(key):
    return frozenset([COPY[key]])

COPY["setup.access_denied"] = "Acceso denegado. Se requiere Gestionar servidor y una sesión propia en este servidor."

# Promoción selectiva: estructura del servidor y formato de fecha/hora.
COPY.update({
  "setup.datetime.date_choice": "Formato de fecha",
  "setup.datetime.preview": "Hora configurada: {clock}. Este formato se aplica a los horarios y formularios del bot.",
  "setup.datetime.time_choice": "Formato de hora",
  "setup.datetime.time12": "12 horas (6:30 p. m.)",
  "setup.datetime.time24": "24 horas (18:30)",
  "setup.structure.choose": "Frecuencia del respaldo de estructura",
  "setup.structure.clock": "Hora exacta (ej. 6:15 p. m. o 18:15)",
  "setup.structure.closed": "Panel cerrado.",
  "setup.structure.confirm": "Confirma el horario mostrado para guardar. Volver conserva el borrador.",
  "setup.structure.confirm_button": "Confirmar cambios",
  "setup.structure.conflict": "La configuración o su programación cambió en otra sesión. Abre nuevamente el panel.",
  "setup.structure.detail.daily": "Hora exacta: {clock} (hora RD).",
  "setup.structure.detail.legacy": "Esta frecuencia antigua ya no puede configurarse. Selecciona Diaria, Semanal o Mensual, y guarda los cambios.",
  "setup.structure.detail.monthly": "Día del mes: {monthday} · Hora exacta: {clock} (hora RD).",
  "setup.structure.detail.off": "Sin respaldo automático programado.",
  "setup.structure.detail.weekly": "Día: {weekday} · Hora exacta: {clock} (hora RD).",
  "setup.structure.draft": "**Borrador:** {mode}\n{details}\nLa selección solo se guarda al confirmar.",
  "setup.structure.expired": "Este borrador ya cambió o está cerrado. Abre nuevamente el panel.",
  "setup.structure.help.daily": "Una copia al día a la hora local elegida.",
  "setup.structure.help.interval": "Repite la copia cada cierto número de minutos.",
  "setup.structure.help.legacy_interval": "Solo lectura; sustituir por diaria, semanal o mensual.",
  "setup.structure.help.monthly": "Una copia cada mes en el día y hora elegidos.",
  "setup.structure.help.off": "No sincroniza automáticamente la estructura.",
  "setup.structure.help.weekly": "Una copia en el día semanal y hora elegidos.",
  "setup.structure.hour": "Hora local (0–23)",
  "setup.structure.interval": "Intervalo en minutos (1–43200)",
  "setup.structure.invalid": "Revisa el día y la hora. Usa una hora válida en formato de 12 o 24 horas.",
  "setup.structure.legacy_active": "**Programación anterior detectada.** El respaldo por intervalo existente sigue activo hasta que confirmes una frecuencia nueva. No se modificarán datos sin tu confirmación.",
  "setup.structure.mode.daily": "Diaria",
  "setup.structure.mode.interval": "Por intervalo",
  "setup.structure.mode.legacy_interval": "Anterior (cambiar frecuencia)",
  "setup.structure.mode.monthly": "Mensual",
  "setup.structure.mode.off": "Desactivado",
  "setup.structure.mode.weekly": "Semanal",
  "setup.structure.module_description": "Respaldo de roles, canales y permisos del servidor",
  "setup.structure.module_label": "Estructura del servidor",
  "setup.structure.monthday": "Día del mes (1–28)",
  "setup.structure.schedule": "Editar día y hora",
  "setup.structure.select_frequency": "Selecciona primero una frecuencia diaria, semanal o mensual.",
  "setup.structure.sync": "Sincronizar ahora",
  "setup.structure.sync_confirm": "¿Sincronizar manualmente la plantilla del servidor? El enlace se enviará únicamente al propietario por mensaje privado. No modifica la programación ni guarda el borrador.",
  "setup.structure.sync_dm_failed": "Plantilla sincronizada, pero Discord no permitió enviar el enlace al propietario por privado.",
  "setup.structure.sync_do": "Confirmar sincronización",
  "setup.structure.sync_error": "No se pudo sincronizar la plantilla: {error}",
  "setup.structure.sync_sent": "Plantilla sincronizada. El enlace se envió por mensaje privado al propietario del servidor.",
  "setup.structure.sync_unsaved": "Antes de sincronizar, guarda o descarta los cambios pendientes de programación.",
  "setup.structure.title": "**Respaldo de estructura: roles, canales y permisos**",
  "setup.structure.unsaved": "Hay cambios pendientes. Guárdalos o descártalos antes de volver.",
  "setup.structure.weekday": "Día semanal (0 lunes–6 domingo)",
  "setup.structure.weekday_name": "Día de la semana",
  "setup.structure.weekday.0": "Lunes",
  "setup.structure.weekday.1": "Martes",
  "setup.structure.weekday.2": "Miércoles",
  "setup.structure.weekday.3": "Jueves",
  "setup.structure.weekday.4": "Viernes",
  "setup.structure.weekday.5": "Sábado",
  "setup.structure.weekday.6": "Domingo"
})
