"""Componentes por plantilla: definiciones limitadas y ejecución confirmada."""
from heraldo_i18n import text as _t, guild_context as _i18n_context, use_guild as _i18n_guild
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
            details.append('privada' if action.get('efimera', True) else _t('text.6cf9a6ab18b23c'))
        lines.append(f"{index}. {action['tipo']}" + (' — ' + ', '.join(details) if details else _t('text.eebdf2d01065df')))
    return '\n'.join(lines)


def validate(data):
    if not isinstance(data, list) or len(data) > 4:
        raise ValueError(_t('text.eb4830a0a8596a'))
    result = copy.deepcopy(data)
    total = 0
    for component in result:
        if not isinstance(component, dict) or component.get('tipo') not in ('boton', 'menu'):
            raise ValueError(_t('text.1e3e6424c87f55'))
        if not isinstance(component.get('etiqueta'), str) or not 1 <= len(component['etiqueta']) <= 80:
            raise ValueError(_t('text.ba879cabd85994'))
        groups = [component] if component['tipo'] == 'boton' else component.get('opciones')
        if not isinstance(groups, list) or not 1 <= len(groups) <= 25:
            raise ValueError(_t('text.0bf3054ab3ce8e'))
        if component['tipo'] == 'menu':
            maximum = component.get('maximo', 1)
            if type(maximum) is not int or not 1 <= maximum <= min(5, len(groups)):
                raise ValueError(_t('text.02e38cb687867d'))
            labels = set()
            for option in groups:
                if not isinstance(option, dict) or not isinstance(option.get('etiqueta'), str) or not 1 <= len(option['etiqueta']) <= 100:
                    raise ValueError(_t('text.61c9c58de9a0f8'))
                if option['etiqueta'].casefold() in labels:
                    raise ValueError(_t('text.b74d6d6309ba55'))
                labels.add(option['etiqueta'].casefold())
        for group in groups:
            actions = group.get('acciones')
            if not isinstance(actions, list) or not 1 <= len(actions) <= 5:
                raise ValueError(_t('text.8cfd30ae1e6052'))
            total += len(actions)
            for action in actions:
                if not isinstance(action, dict) or action.get('tipo') not in KINDS:
                    raise ValueError(_t('text.065baaa035450c'))
                kind = action['tipo']
                if kind.endswith('_rol'):
                    if not isinstance(action.get('rol'), str) or not action['rol'].isdecimal():
                        raise ValueError(_t('text.2b4d865a348d86'))
                elif kind != 'eliminar':
                    if not isinstance(action.get('plantilla'), str) or not 1 <= len(action['plantilla']) <= 70:
                        raise ValueError(_t('text.f6202274f631b9'))
                if kind == 'canal' and (not isinstance(action.get('canal'), str) or not action['canal'].isdecimal()):
                    raise ValueError(_t('text.ac56220ddaf883'))
                if kind == 'respuesta' and type(action.get('efimera', True)) is not bool:
                    raise ValueError(_t('text.0182367407cd7b'))
            if any(x['tipo'] == 'eliminar' for x in actions[:-1]):
                raise ValueError(_t('text.f5145cb4f97494'))
    if total > 25:
        raise ValueError(_t('text.c3513e5ee82891'))
    return result


@_i18n_context
def build_view(template, guild_id):
    definitions = validate(template['componentes'])
    view = discord.ui.View(timeout=None)
    revision = template['componentes_revision']
    for index, definition in enumerate(definitions):
        custom_id = f'ehx:{guild_id}:{revision}:{index}'
        if definition['tipo'] == 'boton':
            button_style = (discord.ButtonStyle.danger
                            if any(action.get('tipo') == 'eliminar'
                                   for action in definition.get('acciones', []))
                            else discord.ButtonStyle.secondary)
            view.add_item(discord.ui.Button(
                label=definition['etiqueta'], custom_id=custom_id,
                style=button_style, row=index,
            ))
        else:
            view.add_item(discord.ui.Select(custom_id=custom_id, placeholder=definition['etiqueta'],
                min_values=1, max_values=definition.get('maximo', 1), row=index,
                options=[discord.SelectOption(label=x['etiqueta'], value=str(i)) for i, x in enumerate(definition['opciones'])]))
    if template.get('button_url') and template.get('button_label'):
        view.add_item(discord.ui.Button(label=template['button_label'], url=template['button_url'], row=4))
    return view


class ActionConfirm(discord.ui.View):
    @_i18n_context
    def __init__(self, host, guild_id, owner_id, message, template, actions):
        super().__init__(timeout=120)
        self.host, self.guild_id, self.owner_id, self.message = host, guild_id, owner_id, message
        self.template, self.actions = copy.deepcopy(template), copy.deepcopy(actions)
        self.finished = False
        # Al menos una eliminación convierte la confirmación en destructiva.
        self.execute.style = (
            discord.ButtonStyle.danger
            if any(action.get('tipo') == 'eliminar' for action in self.actions)
            else discord.ButtonStyle.success
        )

    @_i18n_context
    async def interaction_check(self, interaction):
        if interaction.guild_id != self.guild_id or interaction.user.id != self.owner_id:
            await interaction.response.send_message(_t('text.6e60507ee5f38c'), ephemeral=True)
            return False
        return True

    @discord.ui.button(label=_t('text.87137c3dca5f56'), style=discord.ButtonStyle.success)
    @_i18n_context
    async def execute(self, interaction, button):
        if not await self.interaction_check(interaction):
            return
        if self.finished:
            await interaction.response.send_message(_t('text.6f5c8804bdb7ae'), ephemeral=True)
            return
        self.finished = True
        self.stop()
        await interaction.response.defer(ephemeral=True)
        results = []
        host, guild = self.host, interaction.guild
        current = next((x for x in host['heraldo_template_list'](guild.id)
                        if x.get('componentes_revision') == self.template.get('componentes_revision')), None)
        if current != self.template:
            await interaction.edit_original_response(content=_t('text.118a5ce2b6bc9d'), view=None)
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
            await interaction.edit_original_response(content=_t('text.f388f44e6d62a2'), view=None)
            return
        for action in self.actions:
            try:
                member = await guild.fetch_member(interaction.user.id)
                author = await guild.fetch_member(self.template['componentes_autor'])
                if not author.guild_permissions.manage_guild:
                    raise ValueError(_t('text.d200e1f465cbf7'))
                if host['condemnation_get'](guild.id, member.id):
                    raise ValueError(_t('text.67f69ea98c8267'))
                kind = action['tipo']
                if kind.endswith('_rol'):
                    role = guild.get_role(int(action['rol']))
                    if (not role or not guild.me or not guild.me.guild_permissions.manage_roles or not role.is_assignable() or role.is_default() or role.managed
                            or not host['self_service_role_safe'](role) or not author.guild_permissions.manage_roles
                            or (author.id != guild.owner_id and role >= author.top_role)):
                        raise ValueError(_t('text.ca5761f6cd4b22'))
                    if kind == 'añadir_rol' or (kind == 'alternar_rol' and role not in member.roles):
                        await member.add_roles(role, reason=_t('text.359a11ae7409b2'))
                    else:
                        await member.remove_roles(role, reason=_t('text.359a11ae7409b2'))
                else:
                    channel = guild.get_channel(int(action['canal'])) if kind == 'canal' else self.message.channel
                    public = kind in ('canal', 'editar', 'eliminar') or (kind == 'respuesta' and not action.get('efimera', True))
                    if public:
                        permissions = channel.permissions_for(member) if channel else discord.Permissions.none()
                        if not permissions.view_channel or not permissions.manage_messages or not permissions.send_messages:
                            raise ValueError(_t('text.16893088b5d310'))
                        author_permissions = channel.permissions_for(author)
                        if not author_permissions.view_channel or not author_permissions.send_messages or not author_permissions.manage_messages:
                            raise ValueError(_t('text.c33448e4e03d1c'))
                    if kind == 'eliminar':
                        original = await self.message.channel.fetch_message(self.message.id)
                        if original.author.id != guild.me.id:
                            raise ValueError(_t('text.575de0be0ddfe3'))
                        await original.delete()
                    else:
                        target = next((x for x in host['heraldo_template_list'](guild.id) if x['name'] == action['plantilla']), None)
                        if target is None:
                            raise ValueError(_t('text.65123fff45c529'))
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
                                raise ValueError(_t('text.575de0be0ddfe3'))
                            await original.edit(**payload)
                results.append(_t('text.35ff0bd37b6a1a', p0=f'{kind}'))
                outcome = 'ok'
            except (discord.HTTPException, ValueError) as exc:
                results.append(f"{action['tipo']}: " + (str(exc) if isinstance(exc, ValueError) else _t('text.a55a1399883f80')))
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

    @discord.ui.button(label=_t('text.bb9dbb406dcbd5'), style=discord.ButtonStyle.danger)
    @_i18n_context
    async def cancel(self, interaction, button):
        if not await self.interaction_check(interaction):
            return
        if self.finished:
            await interaction.response.send_message(_t('text.101414bee36ff4'), ephemeral=True)
            return
        self.finished = True
        self.stop()
        await interaction.response.edit_message(content=_t('text.736800d384588d'), view=None)


def install(host):
    @host['bot'].listen('on_interaction')
    @_i18n_context
    async def dispatch(interaction):
        data = interaction.data or {}
        custom_id = str(data.get('custom_id', ''))
        if not custom_id.startswith('ehx:') or interaction.response.is_done():
            return
        try:
            _, guild_id, revision, index = custom_id.split(':')
            if not interaction.guild or int(guild_id) != interaction.guild.id or interaction.message.author.id != host['bot'].user.id:
                raise ValueError(_t('text.64ffd28a1efb16'))
            template = next((x for x in host['heraldo_template_list'](int(guild_id)) if x.get('componentes_revision') == revision), None)
            if template is None:
                raise ValueError(_t('text.42e3ce125f6f85'))
            components = validate(template['componentes'])
            if not index.isdecimal():
                raise ValueError(_t('text.0c4c3f54958d1a'))
            component = components[int(index)]
            if component['tipo'] == 'boton':
                actions = component['acciones']
            else:
                selected = data.get('values', [])
                if not 1 <= len(selected) <= component.get('maximo', 1) or len(set(selected)) != len(selected) or any(not str(x).isdecimal() for x in selected):
                    raise ValueError(_t('text.ec9f4e312a8669'))
                actions = [a for value in selected for a in component['opciones'][int(value)]['acciones']]
            summary = describe_actions(actions)
            # Mantener todos los destinos visibles incluso en una selección extensa.
            import io
            attachment = discord.File(io.BytesIO(summary.encode('utf-8')), filename='acciones.txt')
            try:
                await interaction.response.send_message(_t('text.dcc973de6bc090') + discord.utils.escape_markdown(summary)[:1500],
                    file=attachment, allowed_mentions=discord.AllowedMentions.none(),
                    view=ActionConfirm(host, int(guild_id), interaction.user.id, interaction.message, template, actions), ephemeral=True)
            finally:
                attachment.close()
        except (ValueError, IndexError, KeyError, TypeError):
            await interaction.response.send_message(_t('text.f4cae71ef067c6'), ephemeral=True)

    @host['bot'].tree.command(name='componentes_mensaje', description='Configura botones y menús independientes mediante un archivo JSON confirmado.')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @_i18n_context
    async def configure(interaction: discord.Interaction, plantilla: str, archivo: discord.Attachment):
        if not await host['configuration_access'](interaction):
            return
        if archivo.size > 32768 or not archivo.filename.lower().endswith('.json'):
            await interaction.response.send_message(_t('text.e29d0f134d8364'), ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        try:
            raw = await archivo.read()
            if len(raw) > 32768:
                raise ValueError(_t('text.e35a4ecd141701'))
            definitions = validate(json.loads(raw.decode('utf-8-sig')))
            templates = host['heraldo_template_list'](interaction.guild.id)
            target = next((x for x in templates if x['name'].casefold() == plantilla.strip().casefold()), None)
            if target is None:
                raise ValueError(_t('text.14ab3a6c676705'))
            target.update(componentes=definitions, componentes_revision=uuid.uuid4().hex[:16], componentes_autor=interaction.user.id,
                          role_component='', role_component_mode='ninguno')
            changes = {'message_custom_templates': json.dumps(templates, ensure_ascii=False)}
            view = host['ConfigurationConfirmView'](interaction.guild.id, interaction.user.id, changes)
            await interaction.followup.send(_t('text.124db6774d63c7'),
                view=view, ephemeral=True)
        except (ValueError, UnicodeError, discord.HTTPException) as exc:
            await interaction.followup.send(str(exc) if isinstance(exc, ValueError) else _t('text.7a566c98ff312a'), ephemeral=True)
