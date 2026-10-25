"""Editor visual de borradores; ninguna modificación persiste sin confirmación."""
from heraldo_i18n import text as _t, guild_context as _i18n_context, use_guild as _i18n_guild
from heraldo_i18n import join_text as _i18n_join
import copy
import json
import discord
from discord import app_commands
import message_payload
import heraldo_i18n as i18n


class VisualModal(discord.ui.Modal):
    @_i18n_context
    def __init__(self, editor, mode):
        super().__init__(title={'content': _t('text.a10c78601af04a'), 'text': _t('text.1a49ed51c50a6f'),
                               'images': _t('text.71d017d8384c17'), 'credits': _t('text.86a60bd3aabf98'), 'fields': _t('text.98f6dac6bbe46a')}[mode])
        self.editor, self.mode, self.version = editor, mode, editor.version
        embed = editor.draft['embeds'][editor.index] if editor.draft['embeds'] else {}
        selected_field = (embed.get('fields', [])[editor.field_index - 1]
                          if 0 < editor.field_index <= len(embed.get('fields', [])) else {})
        definitions = {
            'content': [('content', _t('text.2af18bc47fdcc8'), editor.draft.get('content', ''), 2000)],
            'text': [('title', _t('text.4c08a5d5feb22c'), embed.get('title', ''), 256), ('description', _t('text.ee00b96fff266f'), embed.get('description', ''), 4000),
                     ('url', _t('text.628b6182d20eba'), embed.get('url', ''), 1000), ('color', _t('text.17b81affec39bc'), f"{embed.get('color', 0x2B2D31):06X}", 6)],
            'images': [('image', _t('text.2bb535d06d59f9'), embed.get('image', {}).get('url', ''), 1000),
                       ('thumbnail', _t('text.39c2b035901685'), embed.get('thumbnail', {}).get('url', ''), 1000),
                       ('author_icon', _t('text.a7aeb79a9f6bde'), embed.get('author', {}).get('icon_url', ''), 1000)],
            'credits': [('author', _t('text.37dddb486c6741'), embed.get('author', {}).get('name', ''), 256),
                        ('author_url', _t('text.801c2531e88aa7'), embed.get('author', {}).get('url', ''), 1000),
                        ('footer', _t('text.5c9659bd1a6daf'), embed.get('footer', {}).get('text', ''), 2048),
                        ('footer_icon', _t('text.083d323517a055'), embed.get('footer', {}).get('icon_url', ''), 1000)],
            'fields': [('index', _t('text.2f547c9fe60a66'), str(editor.field_index), 2), ('operation', _t('text.1a90bc956b06dd'), _t('common.save'), 8),
                       ('name', _t('text.fcc24033edcb78'), selected_field.get('name', ''), 256),
                       ('value', _t('text.fa541673012fd3'), selected_field.get('value', ''), 1024),
                       ('inline', _t('text.c7d12de4dd5a5b'), _t('common.yes') if selected_field.get('inline') else _t('common.no'), 3)],
        }
        self.inputs = {}
        for key, label, value, limit in definitions[mode]:
            if len(value) > limit:
                raise ValueError(_t('text.b130526bb37dff'))
            hint = (
                _t('footer.editor_hint') if key == 'footer'
                else _t('text.d3d84b188cf4c8') if key == 'footer_icon'
                else None
            )
            item = discord.ui.TextInput(label=label, default=value, max_length=limit, required=False,
                                        placeholder=hint,
                                        style=discord.TextStyle.paragraph if key in ('content', 'description', 'value') else discord.TextStyle.short)
            self.inputs[key] = item
            self.add_item(item)

    @_i18n_context
    async def on_submit(self, interaction):
        editor = self.editor
        if not await editor.interaction_check(interaction):
            return
        if editor.version != self.version:
            await interaction.response.send_message(_t('text.158db49caeebb6'), ephemeral=True)
            return
        draft = copy.deepcopy(editor.draft)
        values = {key: str(item).strip() for key, item in self.inputs.items()}
        if 'inline' in values:
            values['inline'] = i18n.bool_input(values['inline'])
        if 'operation' in values:
            values['operation'] = i18n.canonical_fixed(values['operation'])
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
                        raise ValueError(_t('text.85b1ec7553bac3'))
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
                    raise ValueError(_t('text.48aefa12061825'))
                if values['operation'] == 'eliminar':
                    if index == 0:
                        raise ValueError(_t('text.11805e170d1ecc'))
                    fields.pop(index - 1)
                else:
                    if values['inline'] not in ('si', 'no', 'nao', 'não', 'sim', 'yes') or not values['name'] or not values['value']:
                        raise ValueError(_t('text.864115752117d5'))
                    field = dict(name=values['name'], value=values['value'], inline=values['inline'] == 'si')
                    if index:
                        fields[index - 1] = field
                    else:
                        if len(fields) >= 25:
                            raise ValueError(_t('text.cc1dc4b4f4a27c'))
                        fields.append(field)
            # Los embeds vacíos son solo borradores temporales, nunca publicaciones.
            nonempty = [x for x in draft['embeds'] if x]
            if nonempty or draft.get('content'):
                message_payload.validate(dict(draft, embeds=nonempty))
        except (ValueError, TypeError) as exc:
            await interaction.response.send_message(_t('text.8c719ec79a2dd1', p0=f'{exc}'), ephemeral=True)
            return
        editor.draft = draft
        editor.version += 1
        editor.update_selectors()
        await interaction.response.edit_message(content=editor.summary(), embeds=[], view=editor)


class VisualEditor(discord.ui.View):
    @_i18n_context
    def __init__(self, host, guild_id, owner_id, template):
        super().__init__(timeout=900)
        self.host, self.guild_id, self.owner_id = host, guild_id, owner_id
        self.original = copy.deepcopy(template)
        content, embeds = message_payload.render(template)
        self.draft = {'content': content or '', 'embeds': copy.deepcopy(embeds)}
        for key in ('button_label', 'button_url'):
            if key in template:
                self.draft[key] = template[key]
        self.index, self.version, self.field_index = 0, 0, 0
        selector = discord.ui.Select(placeholder=_t('text.0a5fb3b3e0ba96'), row=0,
                                     options=[discord.SelectOption(label=_t('text.3dac673d45228d'), value='0')])
        selector.callback = self.select_embed
        self.embed_selector = selector
        self.add_item(selector)
        fields = discord.ui.Select(placeholder=_t('text.06ddaed0073161'), row=4,
                                   options=[discord.SelectOption(label=_t('text.f51e578c9df821'), value='0')])
        fields.callback = self.select_field
        self.field_selector = fields
        self.add_item(fields)
        self.update_selectors()
        for label, mode, row in [(_t('text.197c7a8551b91c'), 'content', 1), (_t('text.9b36da865f666c'), 'text', 1), (_t('text.98f60447c34ede'), 'images', 1),
                                 (_t('text.86a60bd3aabf98'), 'credits', 1), (_t('text.96343972fec90d'), 'fields', 1)]:
            button = discord.ui.Button(label=label, style=discord.ButtonStyle.primary, row=row)
            @_i18n_context
            async def callback(interaction, mode=mode):
                if mode != 'content' and not self.draft['embeds']:
                    await interaction.response.send_message(_t('text.5a6fee43da1ffd'), ephemeral=True)
                    return
                try:
                    modal = VisualModal(self, mode)
                except ValueError as exc:
                    await interaction.response.send_message(str(exc), ephemeral=True)
                    return
                await interaction.response.send_modal(modal)
            button.callback = callback
            self.add_item(button)

    @_i18n_context
    async def interaction_check(self, interaction):
        if self.is_finished():
            await interaction.response.send_message(_t('text.31a01241abf57a'), ephemeral=True)
            return False
        return await self.host['configuration_access'](interaction, self.guild_id, self.owner_id)

    @_i18n_context
    def summary(self):
        fields = self.draft['embeds'][self.index].get('fields', []) if self.draft['embeds'] else []
        return (_t('text.80a8aaa3381b15', p0=f"{discord.utils.escape_markdown(self.original['name'])}", p1=f"{len(self.draft['embeds'])}", p2=f"{(self.index + 1 if self.draft['embeds'] else _t('text.3f695d04348e0b'))}") +
                _i18n_join('\n', (_t('text.a677a44e56fbba', p0=f'{i + 1}', p1=f"{discord.utils.escape_markdown(x['name'])}") for i, x in enumerate(fields))))[:1900]

    @_i18n_context
    def update_selectors(self):
        embeds = self.draft['embeds']
        self.embed_selector.options = [discord.SelectOption(
            label=_t('text.34e10addc25a59') + str(i + 1), value=str(i), default=i == self.index)
            for i in range(len(embeds))] or [discord.SelectOption(label=_t('text.3dac673d45228d'), value='0')]
        self.embed_selector.disabled = not embeds
        fields = embeds[self.index].get('fields', []) if embeds else []
        self.field_index = min(self.field_index, len(fields))
        # Discord admite 25 opciones; "Añadir" queda en el formulario con índice 0.
        self.field_selector.options = [discord.SelectOption(
            label=f"{i + 1}. {field['name']}"[:100], value=str(i + 1), default=self.field_index == i + 1)
            for i, field in enumerate(fields)] or [discord.SelectOption(label=_t('text.f51e578c9df821'), value='0')]
        self.field_selector.disabled = not fields

    @_i18n_context
    async def select_field(self, interaction):
        try:
            index = int(interaction.data['values'][0])
            fields = self.draft['embeds'][self.index].get('fields', [])
            if not 1 <= index <= len(fields):
                raise ValueError()
        except (ValueError, IndexError, KeyError):
            await interaction.response.send_message(_t('text.5fdbd87a88aeb1'), ephemeral=True)
            return
        self.field_index = index
        self.version += 1
        self.update_selectors()
        await interaction.response.edit_message(content=self.summary(), embeds=[], view=self)

    @_i18n_context
    async def select_embed(self, interaction):
        try:
            index = int(interaction.data['values'][0])
            if not 0 <= index < len(self.draft['embeds']):
                raise ValueError()
        except (ValueError, KeyError, IndexError):
            await interaction.response.send_message(_t('text.794c5f6e5f5fab'), ephemeral=True)
            return
        self.index = index
        self.field_index = 0
        self.version += 1
        self.update_selectors()
        await interaction.response.edit_message(content=self.summary(), embeds=[], view=self)

    @discord.ui.button(label=_t('text.2be661d5366d4e'), style=discord.ButtonStyle.primary, row=2)
    @_i18n_context
    async def add_embed(self, interaction, button):
        if len(self.draft['embeds']) >= 10:
            await interaction.response.send_message(_t('text.75cc44c1047e85'), ephemeral=True)
            return
        self.draft['embeds'].append({})
        self.index = len(self.draft['embeds']) - 1
        self.field_index = 0
        self.version += 1
        self.update_selectors()
        await interaction.response.edit_message(content=self.summary(), embeds=[], view=self)

    @discord.ui.button(label=_t('text.d296d5069681c7'), style=discord.ButtonStyle.danger, row=2)
    @_i18n_context
    async def remove_embed(self, interaction, button):
        if self.draft['embeds']:
            self.draft['embeds'].pop(self.index)
        self.index = max(0, min(self.index, len(self.draft['embeds']) - 1))
        self.field_index = 0
        self.version += 1
        self.update_selectors()
        await interaction.response.edit_message(content=self.summary(), embeds=[], view=self)

    @discord.ui.button(label=_t('text.c5341f198fc2f4'), style=discord.ButtonStyle.secondary, row=3)
    @_i18n_context
    async def preview(self, interaction, button):
        try:
            payload = self.host['heraldo_template_payload'](self.draft, interaction.guild, interaction.user, interaction.channel)
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        payload.pop('view', None)
        await interaction.response.send_message(**payload, ephemeral=True)

    @discord.ui.button(label=_t('text.13e51a210f45ed'), style=discord.ButtonStyle.success, row=3)
    @_i18n_context
    async def save(self, interaction, button):
        try:
            message_payload.validate(self.draft)
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        templates = self.host['heraldo_template_list'](self.guild_id)
        current = next((x for x in templates if x['name'] == self.original['name']), None)
        if current != self.original:
            await interaction.response.send_message(_t('text.87d106ca9e473d'), ephemeral=True)
            return
        for key in message_payload.VISUAL_KEYS:
            current.pop(key, None)
        current.update(copy.deepcopy(self.draft))
        await self.host['confirm_configuration'](interaction, self.guild_id,
            {'message_custom_templates': json.dumps(templates, ensure_ascii=False)})

    @discord.ui.button(label=_t('text.bb9dbb406dcbd5'), style=discord.ButtonStyle.danger, row=3)
    @_i18n_context
    async def cancel(self, interaction, button):
        self.stop()
        await interaction.response.edit_message(content=_t('text.a4caacc49d7458'), embeds=[], view=None)


def install(host):
    @host['bot'].tree.command(name='editar_plantilla', description='Abre el editor visual de texto, embeds, campos e imágenes.')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @_i18n_context
    async def editor(interaction: discord.Interaction, plantilla: str):
        if not await host['configuration_access'](interaction):
            return
        template = next((x for x in host['heraldo_template_list'](interaction.guild.id) if x['name'].casefold() == plantilla.strip().casefold()), None)
        if template is None:
            await interaction.response.send_message(_t('text.14ab3a6c676705'), ephemeral=True)
            return
        view = VisualEditor(host, interaction.guild.id, interaction.user.id, template)
        await interaction.response.send_message(view.summary(), view=view, ephemeral=True)
