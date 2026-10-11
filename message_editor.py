"""Editor visual de borradores; ninguna modificación persiste sin confirmación."""
import copy
import json
import discord
from discord import app_commands
import message_payload


class VisualModal(discord.ui.Modal):
    def __init__(self, editor, mode):
        super().__init__(title={'content': 'Contenido independiente', 'text': 'Texto del embed',
                               'images': 'Imágenes del embed', 'credits': 'Autor y pie', 'fields': 'Campos del embed'}[mode])
        self.editor, self.mode, self.version = editor, mode, editor.version
        embed = editor.draft['embeds'][editor.index] if editor.draft['embeds'] else {}
        definitions = {
            'content': [('content', 'Texto independiente', editor.draft.get('content', ''), 2000)],
            'text': [('title', 'Título', embed.get('title', ''), 256), ('description', 'Descripción', embed.get('description', ''), 4000),
                     ('url', 'Enlace HTTPS del título', embed.get('url', ''), 1000), ('color', 'Color HEX', f"{embed.get('color', 0x2B2D31):06X}", 6)],
            'images': [('image', 'Imagen HTTPS', embed.get('image', {}).get('url', ''), 1000),
                       ('thumbnail', 'Miniatura HTTPS', embed.get('thumbnail', {}).get('url', ''), 1000),
                       ('author_icon', 'Icono del autor HTTPS', embed.get('author', {}).get('icon_url', ''), 1000)],
            'credits': [('author', 'Nombre del autor', embed.get('author', {}).get('name', ''), 256),
                        ('author_url', 'Enlace del autor HTTPS', embed.get('author', {}).get('url', ''), 1000),
                        ('footer', 'Pie', embed.get('footer', {}).get('text', ''), 2048),
                        ('footer_icon', 'Icono del pie HTTPS', embed.get('footer', {}).get('icon_url', ''), 1000)],
            'fields': [('index', 'Número de campo (0 = añadir)', '0', 2), ('operation', 'Acción: guardar o eliminar', 'guardar', 8),
                       ('name', 'Nombre del campo', '', 256), ('value', 'Valor del campo', '', 1024), ('inline', 'En línea: si o no', 'no', 2)],
        }
        self.inputs = {}
        for key, label, value, limit in definitions[mode]:
            if len(value) > limit:
                raise ValueError('Este valor supera la capacidad del formulario de Discord. Edítelo mediante JSON para conservarlo completo.')
            item = discord.ui.TextInput(label=label, default=value, max_length=limit, required=False,
                                        style=discord.TextStyle.paragraph if key in ('content', 'description', 'value') else discord.TextStyle.short)
            self.inputs[key] = item
            self.add_item(item)

    async def on_submit(self, interaction):
        editor = self.editor
        if not await editor.interaction_check(interaction):
            return
        if editor.version != self.version:
            await interaction.response.send_message('El borrador cambió; abra nuevamente el formulario.', ephemeral=True)
            return
        draft = copy.deepcopy(editor.draft)
        values = {key: str(item).strip() for key, item in self.inputs.items()}
        embed = draft['embeds'][editor.index] if draft['embeds'] else {}
        try:
            if self.mode == 'content':
                draft['content'] = values['content']
            elif self.mode == 'text':
                embed.update(title=values['title'], description=values['description'], url=values['url'], color=int(values['color'].lstrip('#'), 16))
            elif self.mode == 'images':
                for key in ('image', 'thumbnail'):
                    if values[key]:
                        message_payload.url(values[key])
                        embed[key] = {'url': values[key]}
                    else:
                        embed.pop(key, None)
                if values['author_icon']:
                    if not embed.get('author', {}).get('name'):
                        raise ValueError('Defina primero el nombre del autor.')
                    message_payload.url(values['author_icon'])
                    embed['author']['icon_url'] = values['author_icon']
                elif embed.get('author'):
                    embed['author'].pop('icon_url', None)
            elif self.mode == 'credits':
                if values['author']:
                    embed.setdefault('author', {}).update(name=values['author'], url=values['author_url'])
                else:
                    embed.pop('author', None)
                if values['footer']:
                    embed['footer'] = {'text': values['footer'], 'icon_url': values['footer_icon']}
                else:
                    embed.pop('footer', None)
            else:
                index = int(values['index'])
                fields = embed.setdefault('fields', [])
                if not 0 <= index <= len(fields) or values['operation'] not in ('guardar', 'eliminar'):
                    raise ValueError('Índice o acción no válido.')
                if values['operation'] == 'eliminar':
                    if index == 0:
                        raise ValueError('Indique el número del campo que desea retirar.')
                    fields.pop(index - 1)
                else:
                    if values['inline'] not in ('si', 'no') or not values['name'] or not values['value']:
                        raise ValueError('El campo requiere nombre, valor y si/no para En línea.')
                    field = dict(name=values['name'], value=values['value'], inline=values['inline'] == 'si')
                    if index:
                        fields[index - 1] = field
                    else:
                        if len(fields) >= 25:
                            raise ValueError('Máximo de 25 campos por embed.')
                        fields.append(field)
            # Los embeds vacíos son solo borradores temporales, nunca publicaciones.
            nonempty = [x for x in draft['embeds'] if x]
            if nonempty or draft.get('content'):
                message_payload.validate(dict(draft, embeds=nonempty))
        except (ValueError, TypeError) as exc:
            await interaction.response.send_message(f'No se actualizó el borrador: {exc}', ephemeral=True)
            return
        editor.draft = draft
        editor.version += 1
        await interaction.response.edit_message(content=editor.summary(), embeds=[], view=editor)


class VisualEditor(discord.ui.View):
    def __init__(self, host, guild_id, owner_id, template):
        super().__init__(timeout=900)
        self.host, self.guild_id, self.owner_id = host, guild_id, owner_id
        self.original = copy.deepcopy(template)
        content, embeds = message_payload.render(template)
        self.draft = {'content': content or '', 'embeds': copy.deepcopy(embeds)}
        for key in ('button_label', 'button_url'):
            if key in template:
                self.draft[key] = template[key]
        self.index, self.version = 0, 0
        selector = discord.ui.Select(placeholder='Seleccionar embed', row=0,
                                     options=[discord.SelectOption(label='Embed ' + str(i + 1), value=str(i)) for i in range(10)])
        selector.callback = self.select_embed
        self.add_item(selector)
        for label, mode, row in [('Contenido', 'content', 1), ('Texto y color', 'text', 1), ('Imágenes', 'images', 1),
                                 ('Autor y pie', 'credits', 1), ('Campos', 'fields', 1)]:
            button = discord.ui.Button(label=label, row=row)
            async def callback(interaction, mode=mode):
                if mode != 'content' and not self.draft['embeds']:
                    await interaction.response.send_message('Añada primero un embed.', ephemeral=True)
                    return
                try:
                    modal = VisualModal(self, mode)
                except ValueError as exc:
                    await interaction.response.send_message(str(exc), ephemeral=True)
                    return
                await interaction.response.send_modal(modal)
            button.callback = callback
            self.add_item(button)

    async def interaction_check(self, interaction):
        if self.is_finished():
            await interaction.response.send_message('El editor está cerrado. Abra un nuevo borrador.', ephemeral=True)
            return False
        return await self.host['configuration_access'](interaction, self.guild_id, self.owner_id)

    def summary(self):
        fields = self.draft['embeds'][self.index].get('fields', []) if self.draft['embeds'] else []
        return (f"Editor de **{discord.utils.escape_markdown(self.original['name'])}** · {len(self.draft['embeds'])} embeds. "
                f"Seleccionado: {self.index + 1 if self.draft['embeds'] else 'ninguno'}.\n"
                'Los cambios permanecen en el borrador hasta Guardar y confirmar.\n' +
                '\n'.join(f"Campo {i + 1}: {discord.utils.escape_markdown(x['name'])}" for i, x in enumerate(fields)))[:1900]

    async def select_embed(self, interaction):
        index = int(interaction.data['values'][0])
        if index >= len(self.draft['embeds']):
            await interaction.response.send_message('Ese embed no existe; use Añadir embed.', ephemeral=True)
            return
        self.index = index
        self.version += 1
        await interaction.response.edit_message(content=self.summary(), embeds=[], view=self)

    @discord.ui.button(label='Añadir embed', row=2)
    async def add_embed(self, interaction, button):
        if len(self.draft['embeds']) >= 10:
            await interaction.response.send_message('Máximo de diez embeds.', ephemeral=True)
            return
        self.draft['embeds'].append({})
        self.index = len(self.draft['embeds']) - 1
        self.version += 1
        await interaction.response.edit_message(content=self.summary(), embeds=[], view=self)

    @discord.ui.button(label='Retirar embed', row=2)
    async def remove_embed(self, interaction, button):
        if self.draft['embeds']:
            self.draft['embeds'].pop(self.index)
        self.index = max(0, min(self.index, len(self.draft['embeds']) - 1))
        self.version += 1
        await interaction.response.edit_message(content=self.summary(), embeds=[], view=self)

    @discord.ui.button(label='Vista previa', row=3)
    async def preview(self, interaction, button):
        try:
            payload = self.host['heraldo_template_payload'](self.draft, interaction.guild, interaction.user, interaction.channel)
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        payload.pop('view', None)
        await interaction.response.send_message(**payload, ephemeral=True)

    @discord.ui.button(label='Guardar', style=discord.ButtonStyle.success, row=3)
    async def save(self, interaction, button):
        try:
            message_payload.validate(self.draft)
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        templates = self.host['heraldo_template_list'](self.guild_id)
        current = next((x for x in templates if x['name'] == self.original['name']), None)
        if current != self.original:
            await interaction.response.send_message('La plantilla cambió; abra un nuevo editor para conservar los cambios concurrentes.', ephemeral=True)
            return
        for key in message_payload.VISUAL_KEYS:
            current.pop(key, None)
        current.update(copy.deepcopy(self.draft))
        await self.host['confirm_configuration'](interaction, self.guild_id,
            {'message_custom_templates': json.dumps(templates, ensure_ascii=False)})

    @discord.ui.button(label='Cancelar', row=3)
    async def cancel(self, interaction, button):
        self.stop()
        await interaction.response.edit_message(content='Borrador cerrado sin guardar.', embeds=[], view=None)


def install(host):
    @host['bot'].tree.command(name='editar_plantilla', description='Abre el editor visual de texto, embeds, campos e imágenes.')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def editor(interaction: discord.Interaction, plantilla: str):
        if not await host['configuration_access'](interaction):
            return
        template = next((x for x in host['heraldo_template_list'](interaction.guild.id) if x['name'].casefold() == plantilla.strip().casefold()), None)
        if template is None:
            await interaction.response.send_message('La plantilla no existe.', ephemeral=True)
            return
        view = VisualEditor(host, interaction.guild.id, interaction.user.id, template)
        await interaction.response.send_message(view.summary(), view=view, ephemeral=True)
