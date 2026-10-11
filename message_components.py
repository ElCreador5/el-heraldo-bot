"""Componentes por plantilla: definiciones limitadas y ejecución confirmada."""
import copy
import json
import time
import uuid
import discord
from discord import app_commands

KINDS = {'añadir_rol', 'quitar_rol', 'alternar_rol', 'respuesta', 'dm', 'canal', 'editar', 'eliminar'}


def describe_actions(actions):
    lines = []
    for index, action in enumerate(actions, 1):
        details = [f"{key}: {action[key]}" for key in ('rol', 'plantilla', 'canal') if key in action]
        if action['tipo'] == 'respuesta':
            details.append('privada' if action.get('efimera', True) else 'pública')
        lines.append(f"{index}. {action['tipo']}" + (' — ' + ', '.join(details) if details else ' — mensaje original del bot'))
    return '\n'.join(lines)


def validate(data):
    if not isinstance(data, list) or len(data) > 4:
        raise ValueError('Se admiten hasta cuatro componentes por plantilla.')
    result = copy.deepcopy(data)
    total = 0
    for component in result:
        if not isinstance(component, dict) or component.get('tipo') not in ('boton', 'menu'):
            raise ValueError('Cada componente requiere tipo boton o menu.')
        if not isinstance(component.get('etiqueta'), str) or not 1 <= len(component['etiqueta']) <= 80:
            raise ValueError('La etiqueta debe tener entre 1 y 80 caracteres.')
        groups = [component] if component['tipo'] == 'boton' else component.get('opciones')
        if not isinstance(groups, list) or not 1 <= len(groups) <= 25:
            raise ValueError('El menú requiere entre 1 y 25 opciones.')
        if component['tipo'] == 'menu':
            maximum = component.get('maximo', 1)
            if type(maximum) is not int or not 1 <= maximum <= min(5, len(groups)):
                raise ValueError('La selección máxima debe estar entre 1 y 5 opciones disponibles.')
            labels = set()
            for option in groups:
                if not isinstance(option, dict) or not isinstance(option.get('etiqueta'), str) or not 1 <= len(option['etiqueta']) <= 100:
                    raise ValueError('Cada opción requiere una etiqueta de hasta 100 caracteres.')
                if option['etiqueta'].casefold() in labels:
                    raise ValueError('Las etiquetas de las opciones no pueden repetirse.')
                labels.add(option['etiqueta'].casefold())
        for group in groups:
            actions = group.get('acciones')
            if not isinstance(actions, list) or not 1 <= len(actions) <= 5:
                raise ValueError('Cada botón u opción requiere entre 1 y 5 acciones.')
            total += len(actions)
            for action in actions:
                if not isinstance(action, dict) or action.get('tipo') not in KINDS:
                    raise ValueError('Acción no admitida.')
                kind = action['tipo']
                if kind.endswith('_rol'):
                    if not isinstance(action.get('rol'), str) or not action['rol'].isdecimal():
                        raise ValueError('Los roles se indican mediante su ID como texto.')
                elif kind != 'eliminar':
                    if not isinstance(action.get('plantilla'), str) or not 1 <= len(action['plantilla']) <= 70:
                        raise ValueError('La acción requiere el nombre de una plantilla guardada.')
                if kind == 'canal' and (not isinstance(action.get('canal'), str) or not action['canal'].isdecimal()):
                    raise ValueError('La acción canal requiere un ID de canal como texto.')
                if kind == 'respuesta' and type(action.get('efimera', True)) is not bool:
                    raise ValueError('efimera debe ser booleano.')
            if any(x['tipo'] == 'eliminar' for x in actions[:-1]):
                raise ValueError('Eliminar debe ser la última acción de una opción.')
    if total > 25:
        raise ValueError('La plantilla admite hasta 25 acciones en total.')
    return result


def build_view(template, guild_id):
    definitions = validate(template['componentes'])
    view = discord.ui.View(timeout=None)
    revision = template['componentes_revision']
    for index, definition in enumerate(definitions):
        custom_id = f'ehx:{guild_id}:{revision}:{index}'
        if definition['tipo'] == 'boton':
            view.add_item(discord.ui.Button(label=definition['etiqueta'], custom_id=custom_id, row=index))
        else:
            view.add_item(discord.ui.Select(custom_id=custom_id, placeholder=definition['etiqueta'],
                min_values=1, max_values=definition.get('maximo', 1), row=index,
                options=[discord.SelectOption(label=x['etiqueta'], value=str(i)) for i, x in enumerate(definition['opciones'])]))
    if template.get('button_url') and template.get('button_label'):
        view.add_item(discord.ui.Button(label=template['button_label'], url=template['button_url'], row=4))
    return view


class ActionConfirm(discord.ui.View):
    def __init__(self, host, guild_id, owner_id, message, template, actions):
        super().__init__(timeout=120)
        self.host, self.guild_id, self.owner_id, self.message = host, guild_id, owner_id, message
        self.template, self.actions = copy.deepcopy(template), copy.deepcopy(actions)
        self.finished = False

    async def interaction_check(self, interaction):
        if interaction.guild_id != self.guild_id or interaction.user.id != self.owner_id:
            await interaction.response.send_message('Esta confirmación no le pertenece.', ephemeral=True)
            return False
        return True

    @discord.ui.button(label='Confirmar acciones', style=discord.ButtonStyle.primary)
    async def execute(self, interaction, button):
        if not await self.interaction_check(interaction):
            return
        if self.finished:
            await interaction.response.send_message('Esta propuesta ya fue resuelta.', ephemeral=True)
            return
        self.finished = True
        self.stop()
        await interaction.response.defer(ephemeral=True)
        results = []
        host, guild = self.host, interaction.guild
        current = next((x for x in host['heraldo_template_list'](guild.id)
                        if x.get('componentes_revision') == self.template.get('componentes_revision')), None)
        if current != self.template:
            await interaction.edit_original_response(content='La configuración cambió; vuelva a abrir el componente.', view=None)
            return
        conn = host['db_connect']()
        try:
            conn.execute('CREATE TABLE IF NOT EXISTS message_action_rate (guild_id INTEGER,user_id INTEGER,until_at REAL,PRIMARY KEY(guild_id,user_id))')
            claimed = conn.execute('''INSERT INTO message_action_rate VALUES (?,?,?) ON CONFLICT(guild_id,user_id)
                DO UPDATE SET until_at=excluded.until_at WHERE message_action_rate.until_at <= ?''',
                (guild.id, interaction.user.id, time.time() + 15, time.time())).rowcount
        finally:
            conn.close()
        if not claimed:
            await interaction.edit_original_response(content='Espere quince segundos antes de ejecutar más acciones.', view=None)
            return
        for action in self.actions:
            try:
                member = await guild.fetch_member(interaction.user.id)
                author = await guild.fetch_member(self.template['componentes_autor'])
                if not author.guild_permissions.manage_guild:
                    raise ValueError('El autor de la configuración ya no tiene permisos.')
                if host['condemnation_get'](guild.id, member.id):
                    raise ValueError('No se ejecutan componentes durante una condena activa.')
                kind = action['tipo']
                if kind.endswith('_rol'):
                    role = guild.get_role(int(action['rol']))
                    if (not role or not guild.me or not guild.me.guild_permissions.manage_roles or not role.is_assignable() or role.is_default() or role.managed
                            or not host['self_service_role_safe'](role) or not author.guild_permissions.manage_roles
                            or (author.id != guild.owner_id and role >= author.top_role)):
                        raise ValueError('El rol ya no está autorizado o supera la jerarquía disponible.')
                    if kind == 'añadir_rol' or (kind == 'alternar_rol' and role not in member.roles):
                        await member.add_roles(role, reason='Componente confirmado de Mensajes')
                    else:
                        await member.remove_roles(role, reason='Componente confirmado de Mensajes')
                else:
                    channel = guild.get_channel(int(action['canal'])) if kind == 'canal' else self.message.channel
                    public = kind in ('canal', 'editar', 'eliminar') or (kind == 'respuesta' and not action.get('efimera', True))
                    if public:
                        permissions = channel.permissions_for(member) if channel else discord.Permissions.none()
                        if not permissions.view_channel or not permissions.manage_messages or not permissions.send_messages:
                            raise ValueError('La acción pública requiere acceso y Administrar mensajes en el destino.')
                        author_permissions = channel.permissions_for(author)
                        if not author_permissions.view_channel or not author_permissions.send_messages or not author_permissions.manage_messages:
                            raise ValueError('El autor de la configuración perdió los permisos del canal de destino.')
                    if kind == 'eliminar':
                        original = await self.message.channel.fetch_message(self.message.id)
                        if original.author.id != guild.me.id:
                            raise ValueError('Solo se modifica el mensaje original del bot.')
                        await original.delete()
                    else:
                        target = next((x for x in host['heraldo_template_list'](guild.id) if x['name'] == action['plantilla']), None)
                        if target is None:
                            raise ValueError('La plantilla de respuesta ya no existe.')
                        payload = host['heraldo_template_payload'](target, guild, member, channel)
                        payload['view'] = None  # Evita cadenas recursivas de componentes.
                        if kind == 'dm':
                            await member.send(**payload)
                        elif kind == 'respuesta':
                            if action.get('efimera', True):
                                payload.pop('view', None)
                                await interaction.followup.send(**payload, ephemeral=True)
                            else:
                                await channel.send(**payload)
                        elif kind == 'canal':
                            await channel.send(**payload)
                        elif kind == 'editar':
                            original = await self.message.channel.fetch_message(self.message.id)
                            if original.author.id != guild.me.id:
                                raise ValueError('Solo se modifica el mensaje original del bot.')
                            await original.edit(**payload)
                results.append(f'{kind}: completada')
                outcome = 'ok'
            except (discord.HTTPException, ValueError) as exc:
                results.append(f"{action['tipo']}: " + (str(exc) if isinstance(exc, ValueError) else 'Discord rechazó la acción.'))
                outcome = 'error'
            conn = host['db_connect']()
            try:
                conn.execute('''CREATE TABLE IF NOT EXISTS message_action_audit (
                    guild_id INTEGER,user_id INTEGER,kind TEXT,outcome TEXT,created_at REAL)''')
                conn.execute('INSERT INTO message_action_audit VALUES (?,?,?,?,?)',
                             (guild.id, interaction.user.id, action['tipo'], outcome, time.time()))
                conn.execute('DELETE FROM message_action_audit WHERE created_at < ?', (time.time() - 30 * 86400,))
            finally:
                conn.close()
            if outcome != 'ok':
                break  # Resultado parcial explícito; no ejecutar dependencias de una acción fallida.
        await interaction.edit_original_response(content='\n'.join(results)[:1900], view=None,
                                                  allowed_mentions=discord.AllowedMentions.none())

    @discord.ui.button(label='Cancelar', style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        if not await self.interaction_check(interaction):
            return
        if self.finished:
            await interaction.response.send_message('La ejecución ya fue iniciada o resuelta.', ephemeral=True)
            return
        self.finished = True
        self.stop()
        await interaction.response.edit_message(content='Acciones canceladas.', view=None)


def install(host):
    @host['bot'].listen('on_interaction')
    async def dispatch(interaction):
        data = interaction.data or {}
        custom_id = str(data.get('custom_id', ''))
        if not custom_id.startswith('ehx:') or interaction.response.is_done():
            return
        try:
            _, guild_id, revision, index = custom_id.split(':')
            if not interaction.guild or int(guild_id) != interaction.guild.id or interaction.message.author.id != host['bot'].user.id:
                raise ValueError('Componente fuera de su contexto autorizado.')
            template = next((x for x in host['heraldo_template_list'](int(guild_id)) if x.get('componentes_revision') == revision), None)
            if template is None:
                raise ValueError('Este componente fue reemplazado. Solicite una publicación actualizada.')
            components = validate(template['componentes'])
            if not index.isdecimal():
                raise ValueError('Índice no válido.')
            component = components[int(index)]
            if component['tipo'] == 'boton':
                actions = component['acciones']
            else:
                selected = data.get('values', [])
                if not 1 <= len(selected) <= component.get('maximo', 1) or len(set(selected)) != len(selected) or any(not str(x).isdecimal() for x in selected):
                    raise ValueError('Selección no válida.')
                actions = [a for value in selected for a in component['opciones'][int(value)]['acciones']]
            summary = describe_actions(actions)
            # Mantener todos los destinos visibles incluso en una selección extensa.
            import io
            attachment = discord.File(io.BytesIO(summary.encode('utf-8')), filename='acciones.txt')
            try:
                await interaction.response.send_message('Revise las acciones y sus destinos en el archivo adjunto antes de confirmarlas.\n' + discord.utils.escape_markdown(summary)[:1500],
                    file=attachment, allowed_mentions=discord.AllowedMentions.none(),
                    view=ActionConfirm(host, int(guild_id), interaction.user.id, interaction.message, template, actions), ephemeral=True)
            finally:
                attachment.close()
        except (ValueError, IndexError, KeyError, TypeError):
            await interaction.response.send_message('Componente no disponible o selección no válida. Publique de nuevo la plantilla.', ephemeral=True)

    @host['bot'].tree.command(name='componentes_mensaje', description='Configura botones y menús independientes mediante un archivo JSON confirmado.')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def configure(interaction: discord.Interaction, plantilla: str, archivo: discord.Attachment):
        if not await host['configuration_access'](interaction):
            return
        if archivo.size > 32768 or not archivo.filename.lower().endswith('.json'):
            await interaction.response.send_message('Adjunte un JSON de hasta 32 KiB.', ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        try:
            raw = await archivo.read()
            if len(raw) > 32768:
                raise ValueError('Archivo demasiado grande.')
            definitions = validate(json.loads(raw.decode('utf-8-sig')))
            templates = host['heraldo_template_list'](interaction.guild.id)
            target = next((x for x in templates if x['name'].casefold() == plantilla.strip().casefold()), None)
            if target is None:
                raise ValueError('La plantilla no existe.')
            target.update(componentes=definitions, componentes_revision=uuid.uuid4().hex[:16], componentes_autor=interaction.user.id,
                          role_component='', role_component_mode='ninguno')
            changes = {'message_custom_templates': json.dumps(templates, ensure_ascii=False)}
            view = host['ConfigurationConfirmView'](interaction.guild.id, interaction.user.id, changes)
            await interaction.followup.send('Confirme los componentes de la plantilla. Las publicaciones anteriores quedan obsoletas; debe publicar la nueva versión. '
                'Las acciones públicas exigen Administrar mensajes al usuario que las ejecute; las acciones de roles se revalidan por jerarquía.',
                view=view, ephemeral=True)
        except (ValueError, UnicodeError, discord.HTTPException) as exc:
            await interaction.followup.send(str(exc) if isinstance(exc, ValueError) else 'No se pudo leer el archivo.', ephemeral=True)
