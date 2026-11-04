"""Panel nativo para conexiones de roles; la navegación conserva el borrador.

Una conexión tiene un rol principal, grupos AND/OR y condiciones tiene/no tiene.
No necesita un panel web. Las selecciones no escriben en SQLite.
"""
from __future__ import annotations

import copy
import inspect

import discord

import role_connections as engine
from panel_navigation import dismiss_panel

LABELS = {
    "es-419": {
        "title": "Conexiones de roles", "main_role": "Rol principal", "empty": "No hay conexiones guardadas.",
        "create": "Nueva conexión", "sync": "Sincronizar miembros",
        "choose": "Selecciona una conexión para editar", "target": "Elige el rol principal",
        "group": "Elige el grupo de condiciones", "condition": "Elige una condición para editar",
        "edit_group": "Editar grupo", "new_group": "Añadir grupo",
        "group_operator": "Entre grupos", "group_and": "AND entre grupos",
        "group_or": "OR entre grupos", "group_mode": "Condiciones del grupo",
        "add_condition": "Añadir condición", "delete_group": "Eliminar grupo",
        "save_condition": "Aplicar condición", "delete_condition": "Quitar condición",
        "has": "Tiene el rol", "lacks": "No tiene el rol",
        "condition_role": "Selecciona el rol de la condición",
        "save": "Guardar cambios", "discard": "Descartar cambios",
        "delete": "Eliminar conexión", "pause": "Pausar", "resume": "Activar",
        "back": "Volver", "close": "Cerrar", "confirm_save": "Confirmar guardado",
        "confirm_delete": "Confirmar eliminación", "confirm_sync": "Confirmar sincronización",
        "cancel": "Cancelar", "error": "No se pudo completar la operación.",
        "missing_role": "Debes seleccionar roles existentes.",
        "invalid_groups": "Crea al menos un grupo con una condición válida.",
        "invalid_conditions": "Completa las condiciones y comprueba sus operadores.",
        "unsafe_target": "El rol principal no puede ser administrado de forma segura por El Heraldo.",
        "circular_rule": "Las conexiones no pueden depender circularmente unas de otras.",
        "duplicate_target": "Ese rol principal ya tiene una conexión.",
        "stale_rule": "La conexión cambió en otra sesión. Abre nuevamente el editor.",
        "rule_limit": "Alcanzaste el límite de conexiones.",
        "invalid_name": "El rol principal debe tener un nombre válido.",
        "duplicate_condition": "La condición ya existe en este grupo.",
        "contradictory_condition": "La condición contradice otra del mismo grupo.",
        "saved": "Conexión guardada. Sincroniza miembros existentes cuando lo necesites.",
        "deleted": "Conexión eliminada. Los roles existentes no se retiran al borrarla.",
        "changed": "Estado actualizado. Sincroniza para aplicarlo a miembros existentes.",
        "synced": "Miembros revisados: {checked}. Roles agregados: {added}. Roles retirados: {removed}.",
        "sync_partial": "Se alcanzó el máximo de 1000 miembros por revisión. El resto requiere una sincronización adicional.",
        "sync_info": "Se revisarán todos los miembros. Esto puede agregar o retirar roles según las conexiones activas.",
        "delete_info": "Esta acción borra la regla, pero conserva los roles ya otorgados.",
        "save_info": "La regla comenzará a funcionar cuando cambien los roles de los miembros. La sincronización de miembros existentes es una acción separada.",
        "instructions": "Elige un rol principal y configura condiciones. AND exige todas; OR exige al menos una.",
        "draft": "Cambios sin guardar",
        "no_group_delete": "Debe existir al menos un grupo.",
        "no_condition": "Selecciona el rol de esta condición.",
        "no_target": "Selecciona el rol principal.",
        "disabled": "Pausada", "enabled": "Activa",
        "group_status": "Grupo {n} — {mode} ({count}/10)",
        "no_connection": "No se encontró la conexión.", "not_applicable": "No hay reglas activas.",
        "limit_groups": "Máximo de cinco grupos.",
        "limit_conditions": "Máximo de diez condiciones por grupo.",
    },
    "en-US": {
        "title": "Role connections", "main_role": "Main role", "empty": "No saved connections.",
        "create": "New connection", "sync": "Sync members",
        "choose": "Select a connection to edit", "target": "Choose the main role",
        "group": "Choose the condition group", "condition": "Choose a condition to edit",
        "edit_group": "Edit group", "new_group": "Add group",
        "group_operator": "Between groups", "group_and": "AND between groups",
        "group_or": "OR between groups", "group_mode": "Group conditions",
        "add_condition": "Add condition", "delete_group": "Delete group",
        "save_condition": "Apply condition", "delete_condition": "Remove condition",
        "has": "Has role", "lacks": "Does not have role",
        "condition_role": "Choose condition role",
        "save": "Save changes", "discard": "Discard changes",
        "delete": "Delete connection", "pause": "Pause", "resume": "Activate",
        "back": "Back", "close": "Close", "confirm_save": "Confirm save",
        "confirm_delete": "Confirm deletion", "confirm_sync": "Confirm sync",
        "cancel": "Cancel", "error": "Unable to complete the operation.",
        "missing_role": "Select existing roles.",
        "invalid_groups": "Create at least one group with a valid condition.",
        "invalid_conditions": "Complete the conditions and check the operators.",
        "unsafe_target": "El Heraldo cannot safely manage the main role.",
        "circular_rule": "Role connections cannot have circular dependencies.",
        "duplicate_target": "That main role already has a connection.",
        "stale_rule": "Another session changed this connection. Reopen the editor.",
        "rule_limit": "Connection limit reached.",
        "invalid_name": "The main role needs a valid name.",
        "duplicate_condition": "This condition already exists in the group.",
        "contradictory_condition": "This condition contradicts another in the group.",
        "saved": "Connection saved. Sync existing members if needed.",
        "deleted": "Connection deleted. Existing member roles are not removed.",
        "changed": "Status updated. Sync to apply it to existing members.",
        "synced": "Members checked: {checked}. Roles added: {added}. Roles removed: {removed}.",
        "sync_partial": "The 1000-member review limit was reached. Additional members require another sync.",
        "sync_info": "All server members will be reviewed. Roles may be added or removed according to active connections.",
        "delete_info": "This deletes the rule but keeps previously assigned roles.",
        "save_info": "The rule runs when member roles change. Existing members require a separate sync.",
        "instructions": "Choose a main role and conditions. AND means all; OR means at least one.",
        "draft": "Unsaved changes",
        "no_group_delete": "At least one group is required.",
        "no_condition": "Choose a role for this condition.",
        "no_target": "Choose the main role.",
        "disabled": "Paused", "enabled": "Active",
        "group_status": "Group {n} — {mode} ({count}/10)",
        "no_connection": "Connection not found.", "not_applicable": "No active rules.",
        "limit_groups": "Maximum of five groups.",
        "limit_conditions": "Maximum of ten conditions per group.",
    },
    "pt-BR": {
        "title": "Conexões de cargos", "main_role": "Cargo principal", "empty": "Não há conexões salvas.",
        "create": "Nova conexão", "sync": "Sincronizar membros",
        "choose": "Selecione uma conexão para editar", "target": "Escolha o cargo principal",
        "group": "Escolha o grupo de condições", "condition": "Escolha uma condição para editar",
        "edit_group": "Editar grupo", "new_group": "Adicionar grupo",
        "group_operator": "Entre grupos", "group_and": "AND entre grupos",
        "group_or": "OR entre grupos", "group_mode": "Condições do grupo",
        "add_condition": "Adicionar condição", "delete_group": "Excluir grupo",
        "save_condition": "Aplicar condição", "delete_condition": "Remover condição",
        "has": "Tem o cargo", "lacks": "Não tem o cargo",
        "condition_role": "Escolha o cargo da condição",
        "save": "Salvar alterações", "discard": "Descartar alterações",
        "delete": "Excluir conexão", "pause": "Pausar", "resume": "Ativar",
        "back": "Voltar", "close": "Fechar", "confirm_save": "Confirmar gravação",
        "confirm_delete": "Confirmar exclusão", "confirm_sync": "Confirmar sincronização",
        "cancel": "Cancelar", "error": "Não foi possível concluir a operação.",
        "missing_role": "Selecione cargos existentes.",
        "invalid_groups": "Crie ao menos um grupo com uma condição válida.",
        "invalid_conditions": "Preencha as condições e confira os operadores.",
        "unsafe_target": "El Heraldo não pode gerenciar o cargo principal com segurança.",
        "circular_rule": "As conexões não podem ter dependências circulares.",
        "duplicate_target": "Esse cargo principal já tem uma conexão.",
        "stale_rule": "Outra sessão alterou a conexão. Abra o editor novamente.",
        "rule_limit": "Limite de conexões atingido.",
        "invalid_name": "O cargo principal precisa de um nome válido.",
        "duplicate_condition": "A condição já existe neste grupo.",
        "contradictory_condition": "Esta condição contradiz outra no grupo.",
        "saved": "Conexão salva. Sincronize os membros existentes se necessário.",
        "deleted": "Conexão excluída. Os cargos existentes foram preservados.",
        "changed": "Estado atualizado. Sincronize para aplicar aos membros existentes.",
        "synced": "Membros revisados: {checked}. Cargos adicionados: {added}. Cargos removidos: {removed}.",
        "sync_partial": "Limite de 1000 membros atingido. Outros membros precisam de outra sincronização.",
        "sync_info": "Todos os membros serão revisados. Cargos poderão ser adicionados ou removidos conforme as conexões ativas.",
        "delete_info": "A regra será excluída, mas os cargos já concedidos permanecerão.",
        "save_info": "A regra será executada quando os cargos mudarem. Membros existentes precisam de sincronização separada.",
        "instructions": "Selecione um cargo principal e condições. AND exige todas; OR exige ao menos uma.",
        "draft": "Alterações não salvas",
        "no_group_delete": "É necessário pelo menos um grupo.",
        "no_condition": "Selecione o cargo da condição.",
        "no_target": "Escolha o cargo principal.",
        "disabled": "Pausada", "enabled": "Ativa",
        "group_status": "Grupo {n} — {mode} ({count}/10)",
        "no_connection": "Conexão não encontrada.", "not_applicable": "Não há regras ativas.",
        "limit_groups": "Máximo de cinco grupos.",
        "limit_conditions": "Máximo de dez condições por grupo.",
    },
}


class Context:
    def __init__(self, host, guild_id, owner_id):
        self.host, self.guild_id, self.owner_id = host, guild_id, owner_id

    def t(self, key, **kwargs):
        lang = self.host["guild_language"](self.guild_id)
        return LABELS.get(lang, LABELS["es-419"])[key].format(**kwargs)

    def rules(self):
        return engine.list_rules(self.host["db_connect"], self.guild_id)

    def protected(self):
        host = self.host
        gid = self.guild_id
        result = set(host["get_eval_role_ids"](gid))
        for name in ("get_verify_role_id", "get_sin_verificado_role_id",
                     "get_tentado_role_id"):
            try:
                value = int(host[name](gid) or 0)
                if value:
                    result.add(value)
            except (KeyError, ValueError, TypeError):
                pass
        try:
            role_id = int(host["condemnation_role_id"](None, gid) or 0)
            if role_id:
                result.add(role_id)
        except (KeyError, ValueError, TypeError):
            pass
        return result

    def blocked(self, member):
        if self.host["condemnation_get"](member.guild.id, member.id) is not None:
            return True
        condemned = int(self.host["condemnation_role_id"](None, member.guild.id) or 0)
        return bool(condemned and any(r.id == condemned for r in member.roles))


def _role(guild, role_id):
    role = guild.get_role(int(role_id or 0))
    return role.mention if role else f"<@&{role_id}>" if role_id else "—"


def _option_role(guild, role_id):
    role = guild.get_role(int(role_id or 0))
    return str(role.name) if role else str(role_id or "—")


def _format_groups(ctx, guild, groups, mode):
    output = []
    for index, group in enumerate(groups, 1):
        expressions = [
            (ctx.t("has") if c["op"] == "has" else ctx.t("lacks"))
            + " " + _role(guild, c.get("role_id"))
            for c in group["conditions"]
        ]
        output.append(
            f"**{index}. {group['mode'].upper()}**: "
            + (f" {group['mode'].upper()} ".join(expressions) if expressions else "—")
        )
    return f"\n**{ctx.t('group_operator')}: {mode.upper()}**\n" + "\n".join(output)


def new_draft(rule=None):
    if rule is None:
        return {
            "rule_id": None, "revision": None, "target_role_id": None, "name": "",
            "groups": [{"mode": "all", "conditions": []}],
            "groups_mode": "any", "group_index": 0,
        }
    return {
        "rule_id": rule.rule_id, "revision": rule.revision,
        "target_role_id": rule.target_role_id, "name": rule.name,
        "groups": copy.deepcopy(list(rule.groups)), "groups_mode": rule.groups_mode,
        "group_index": 0,
    }


async def _error(interaction, message):
    sender = interaction.followup.send if interaction.response.is_done() else interaction.response.send_message
    await sender(message, ephemeral=True)


async def _render(interaction, view):
    if interaction.response.is_done():
        await interaction.edit_original_response(content=view.summary(interaction.guild), embed=None, view=view)
    else:
        await interaction.response.edit_message(content=view.summary(interaction.guild), embed=None, view=view)


class Base(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=900)
        self.ctx = ctx
        self.guild_id = ctx.guild_id
        self.owner_id = ctx.owner_id

    async def interaction_check(self, interaction):
        return await self.ctx.host["configuration_access"](
            interaction, self.guild_id, self.owner_id
        )

    def button(self, key, callback, *, row, style=discord.ButtonStyle.primary, disabled=False):
        item = discord.ui.Button(label=self.ctx.t(key), row=row, style=style, disabled=disabled)
        item.callback = callback
        self.add_item(item)

    def navigation(self, back, *, row):
        self.button("back", back, row=row, style=discord.ButtonStyle.secondary)
        self.button("close", self.close, row=row, style=discord.ButtonStyle.danger)

    async def close(self, interaction):
        self.stop()
        await dismiss_panel(interaction)

    async def on_error(self, interaction, error, item):
        print(f"ROLE_CONNECTIONS status=INTERACTION_FAILED guild={self.guild_id} "
              f"error={type(error).__name__}", flush=True)
        await _error(interaction, self.ctx.t("error"))


class ConnectionsList(Base):
    def __init__(self, ctx):
        super().__init__(ctx)
        rules = ctx.rules()
        if rules:
            selector = discord.ui.Select(
                placeholder=ctx.t("choose"), row=0, min_values=1, max_values=1,
                options=[
                    discord.SelectOption(
                        label=r.name[:100], value=r.rule_id,
                        description=_option_role(ctx.host["bot"].get_guild(ctx.guild_id),
                                                 r.target_role_id)[:100],
                    ) for r in rules[:25]
                ]
            )

            async def selected(interaction):
                rule = engine.get_rule(ctx.host["db_connect"], ctx.guild_id,
                                       selector.values[0])
                if rule is None:
                    return await _error(interaction, ctx.t("no_connection"))
                await _render(interaction, ConnectionEditor(ctx, new_draft(rule)))

            selector.callback = selected
            self.add_item(selector)
            actions_row = 1
        else:
            actions_row = 0
        self.button("create", self.create, row=actions_row)
        self.button("sync", self.sync, row=actions_row, style=discord.ButtonStyle.secondary)
        self.navigation(self.back, row=actions_row+1)

    def summary(self, guild):
        rules = self.ctx.rules()
        output = [f"**{self.ctx.t('title')}**", self.ctx.t("instructions"), ""]
        if not rules:
            output.append(self.ctx.t("empty"))
        for index, rule in enumerate(rules, 1):
            output.append(
                f"**{index}. {_role(guild, rule.target_role_id)} · "
                f"{self.ctx.t('enabled' if rule.enabled else 'disabled')}**"
                f" · {len(rule.groups)} {self.ctx.t('group_mode').lower()}"
            )
        output.append(f"\n{len(rules)}/{engine.MAX_RULES}")
        return "\n".join(output)[:3900]

    async def create(self, interaction):
        await _render(interaction, ConnectionEditor(self.ctx, new_draft()))

    async def sync(self, interaction):
        await _render(interaction, Confirmation(self.ctx, "sync", None))

    async def back(self, interaction):
        host = self.ctx.host
        view = host["HeraldoSetupView"](self.guild_id, self.owner_id)
        content = host["heraldo_setup_home_content"](self.guild_id)
        if interaction.response.is_done():
            await interaction.edit_original_response(content=content, embed=None, view=view)
        else:
            await interaction.response.edit_message(content=content, embed=None, view=view)


class ConnectionEditor(Base):
    def __init__(self, ctx, draft):
        super().__init__(ctx)
        self.draft = draft
        guild = ctx.host["bot"].get_guild(ctx.guild_id)
        self.target = discord.ui.RoleSelect(
            placeholder=ctx.t("target") + (
                f": {_option_role(guild, draft['target_role_id'])}"
                if draft["target_role_id"] else ""),
            row=0, min_values=1, max_values=1,
        )
        if (draft["rule_id"] is not None and draft["target_role_id"]
                and "default_values" in inspect.signature(discord.ui.RoleSelect).parameters
                and guild is not None and guild.get_role(draft["target_role_id"]) is not None):
            self.target.default_values = [guild.get_role(draft["target_role_id"])]

        async def target_changed(interaction):
            role = self.target.values[0]
            self.draft["target_role_id"] = role.id
            if self.draft["rule_id"] is None:
                self.draft["name"] = role.name
            await _render(interaction, ConnectionEditor(ctx, self.draft))

        self.target.callback = target_changed
        self.add_item(self.target)

        opts = []
        for i, group in enumerate(draft["groups"]):
            opts.append(discord.SelectOption(
                label=ctx.t("group_status", n=i+1,
                            mode=group["mode"].upper(), count=len(group["conditions"])),
                value=str(i), default=i == draft["group_index"],
            ))
        select = discord.ui.Select(placeholder=ctx.t("group"), row=1, options=opts)

        async def picked(interaction):
            self.draft["group_index"] = int(select.values[0])
            await _render(interaction, ConnectionEditor(ctx, self.draft))

        select.callback = picked
        self.add_item(select)
        self.button("edit_group", self.edit_group, row=2)
        self.button("new_group", self.new_group, row=2)
        self.button("group_operator", self.toggle_group_mode, row=2,
                    style=discord.ButtonStyle.secondary)
        self.button("save", self.save, row=3, style=discord.ButtonStyle.success)
        self.button("discard", self.discard, row=3, style=discord.ButtonStyle.danger)
        if draft["rule_id"]:
            self.button("delete", self.delete, row=3, style=discord.ButtonStyle.danger)
            self.button("pause" if self._is_enabled() else "resume",
                        self.toggle_enabled, row=3, style=discord.ButtonStyle.secondary)
        self.navigation(self.back, row=4)

    def _is_enabled(self):
        rule = engine.get_rule(self.ctx.host["db_connect"], self.guild_id,
                               self.draft["rule_id"])
        return bool(rule is not None and rule.enabled)

    def summary(self, guild):
        rule_name = self.draft["name"] or self.ctx.t("title")
        return (
            f"**{self.ctx.t('title')} · {discord.utils.escape_markdown(rule_name)}**\n"
            f"**{self.ctx.t('main_role')}:** {_role(guild, self.draft['target_role_id'])}"
            f"{_format_groups(self.ctx, guild, self.draft['groups'], self.draft['groups_mode'])}"
            f"\n\n*{self.ctx.t('draft')}*"
        )[:3900]

    async def edit_group(self, interaction):
        await _render(interaction, GroupEditor(self.ctx, self.draft))

    async def new_group(self, interaction):
        if len(self.draft["groups"]) >= engine.MAX_GROUPS:
            return await _error(interaction, self.ctx.t("limit_groups"))
        self.draft["groups"].append({"mode": "all", "conditions": []})
        self.draft["group_index"] = len(self.draft["groups"]) - 1
        await _render(interaction, GroupEditor(self.ctx, self.draft))

    async def toggle_group_mode(self, interaction):
        self.draft["groups_mode"] = ("any" if self.draft["groups_mode"] == "all" else "all")
        await _render(interaction, ConnectionEditor(self.ctx, self.draft))

    async def save(self, interaction):
        if self.draft["target_role_id"] is None:
            return await _error(interaction, self.ctx.t("no_target"))
        try:
            engine.validate_groups(
                self.draft["groups"], self.draft["groups_mode"], self.draft["target_role_id"]
            )
        except ValueError as exc:
            return await _error(interaction, self.ctx.t(str(exc)) if str(exc) in LABELS["es-419"] else self.ctx.t("invalid_conditions"))
        await _render(interaction, Confirmation(self.ctx, "save", self.draft))

    async def discard(self, interaction):
        existing = (engine.get_rule(self.ctx.host["db_connect"], self.guild_id,
                                    self.draft["rule_id"])
                    if self.draft["rule_id"] else None)
        if self.draft["rule_id"] and existing is None:
            return await _render(interaction, ConnectionsList(self.ctx))
        await _render(interaction, ConnectionEditor(self.ctx, new_draft(existing)))

    async def delete(self, interaction):
        await _render(interaction, Confirmation(self.ctx, "delete", self.draft))

    async def toggle_enabled(self, interaction):
        rule = engine.get_rule(self.ctx.host["db_connect"], self.guild_id, self.draft["rule_id"])
        if rule is None or rule.revision != self.draft["revision"]:
            return await _error(interaction, self.ctx.t("stale_rule"))
        if not engine.switch_rule(
            self.ctx.host["db_connect"], self.guild_id, rule.rule_id,
            rule.revision, not rule.enabled,
        ):
            return await _error(interaction, self.ctx.t("stale_rule"))
        latest = engine.get_rule(self.ctx.host["db_connect"], self.guild_id, rule.rule_id)
        await _render(interaction, ConnectionEditor(self.ctx, new_draft(latest)))

    async def back(self, interaction):
        await _render(interaction, ConnectionsList(self.ctx))


class GroupEditor(Base):
    def __init__(self, ctx, draft):
        super().__init__(ctx)
        self.draft = draft
        self.index = draft["group_index"]
        group = draft["groups"][self.index]
        if group["conditions"]:
            guild = ctx.host["bot"].get_guild(ctx.guild_id)
            selector = discord.ui.Select(
                placeholder=ctx.t("condition"), row=0,
                options=[
                    discord.SelectOption(
                        label=f"{i+1}. {ctx.t('has' if c['op'] == 'has' else 'lacks')}: "
                              f"{_option_role(guild, c['role_id'])}"[:100],
                        value=str(i)
                    ) for i, c in enumerate(group["conditions"])
                ],
            )

            async def selected(interaction):
                await _render(interaction, ConditionEditor(
                    ctx, draft, self.index, int(selector.values[0])
                ))

            selector.callback = selected
            self.add_item(selector)
            row = 1
        else:
            row = 0
        self.button("add_condition", self.add_condition, row=row)
        self.button("group_mode", self.toggle, row=row, style=discord.ButtonStyle.secondary)
        self.button("delete_group", self.delete, row=row, style=discord.ButtonStyle.danger,
                    disabled=len(draft["groups"]) == 1)
        self.navigation(self.back, row=row+1)

    def summary(self, guild):
        group = self.draft["groups"][self.index]
        details = _format_groups(self.ctx, guild, [group], self.draft["groups_mode"])
        return (
            f"**{self.ctx.t('title')} — "
            f"{self.ctx.t('group_status', n=self.index+1, mode=group['mode'].upper(), count=len(group['conditions']))}**"
            f"\n{details}\n\n*{self.ctx.t('draft')}*"
        )

    async def add_condition(self, interaction):
        if len(self.draft["groups"][self.index]["conditions"]) >= engine.MAX_CONDITIONS:
            return await _error(interaction, self.ctx.t("limit_conditions"))
        await _render(interaction, ConditionEditor(self.ctx, self.draft, self.index, None))

    async def toggle(self, interaction):
        group = self.draft["groups"][self.index]
        group["mode"] = "any" if group["mode"] == "all" else "all"
        await _render(interaction, GroupEditor(self.ctx, self.draft))

    async def delete(self, interaction):
        if len(self.draft["groups"]) <= 1:
            return await _error(interaction, self.ctx.t("no_group_delete"))
        self.draft["groups"].pop(self.index)
        self.draft["group_index"] = max(0, self.index - 1)
        await _render(interaction, ConnectionEditor(self.ctx, self.draft))

    async def back(self, interaction):
        await _render(interaction, ConnectionEditor(self.ctx, self.draft))


class ConditionEditor(Base):
    def __init__(self, ctx, draft, group_index, index):
        super().__init__(ctx)
        self.draft, self.group_index, self.index = draft, group_index, index
        group = draft["groups"][group_index]
        self.pending = copy.deepcopy(
            group["conditions"][index] if index is not None
            else {"role_id": None, "op": "has"}
        )
        guild = ctx.host["bot"].get_guild(ctx.guild_id)
        role_select = discord.ui.RoleSelect(
            placeholder=ctx.t("condition_role") + (
                f": {_option_role(guild, self.pending['role_id'])}"
                if self.pending["role_id"] else ""),
            row=0, min_values=1, max_values=1,
        )
        if (index is not None and self.pending["role_id"]
                and "default_values" in inspect.signature(discord.ui.RoleSelect).parameters
                and guild is not None and guild.get_role(self.pending["role_id"]) is not None):
            role_select.default_values = [guild.get_role(self.pending["role_id"])]

        async def selected_role(interaction):
            self.pending["role_id"] = role_select.values[0].id
            await _render(interaction, self._refresh())

        role_select.callback = selected_role
        self.add_item(role_select)
        mode = discord.ui.Select(
            placeholder=ctx.t("has") + " / " + ctx.t("lacks"), row=1,
            options=[
                discord.SelectOption(label=ctx.t("has"), value="has",
                                     default=self.pending["op"] == "has"),
                discord.SelectOption(label=ctx.t("lacks"), value="lacks",
                                     default=self.pending["op"] == "lacks")
            ],
        )

        async def selected_mode(interaction):
            self.pending["op"] = mode.values[0]
            await _render(interaction, self._refresh())

        mode.callback = selected_mode
        self.add_item(mode)
        self.button("save_condition", self.save, row=2, style=discord.ButtonStyle.success)
        if index is not None:
            self.button("delete_condition", self.delete, row=2,
                        style=discord.ButtonStyle.danger)
        self.navigation(self.back, row=3)

    def _refresh(self):
        # Update UI select placeholder/default from the pending draft.
        return ConditionEditorWithPending(
            self.ctx, self.draft, self.group_index, self.index, self.pending
        )

    def summary(self, guild):
        return (
            f"**{self.ctx.t('title')} — {self.ctx.t('group_status', n=self.group_index+1, mode=self.draft['groups'][self.group_index]['mode'].upper(), count=len(self.draft['groups'][self.group_index]['conditions']))}**"
            f"\n{self.ctx.t('has' if self.pending['op'] == 'has' else 'lacks')}: "
            f"{_role(guild, self.pending['role_id'])}\n\n*{self.ctx.t('draft')}*"
        )

    async def save(self, interaction):
        if self.pending["role_id"] is None:
            return await _error(interaction, self.ctx.t("no_condition"))
        conditions = self.draft["groups"][self.group_index]["conditions"]
        proposed = copy.deepcopy(conditions)
        if self.index is None:
            proposed.append(self.pending)
        else:
            proposed[self.index] = self.pending
        # Validate duplicate / contradictory conditions, without requiring
        # every other group to be completed.
        seen = set()
        for cond in proposed:
            pair = (cond["role_id"], cond["op"])
            opposite = (cond["role_id"], "lacks" if cond["op"] == "has" else "has")
            if pair in seen or opposite in seen:
                key = "duplicate_condition" if pair in seen else "contradictory_condition"
                return await _error(interaction, self.ctx.t(key))
            seen.add(pair)
        if self.pending["role_id"] == self.draft["target_role_id"]:
            return await _error(interaction, self.ctx.t("circular_rule"))
        conditions[:] = proposed
        await _render(interaction, GroupEditor(self.ctx, self.draft))

    async def delete(self, interaction):
        self.draft["groups"][self.group_index]["conditions"].pop(self.index)
        await _render(interaction, GroupEditor(self.ctx, self.draft))

    async def back(self, interaction):
        await _render(interaction, GroupEditor(self.ctx, self.draft))


class ConditionEditorWithPending(ConditionEditor):
    """Rebuild from temporary selection without silently writing it to the rule."""
    def __init__(self, ctx, draft, group_index, index, pending):
        super().__init__(ctx, draft, group_index, index)
        self.pending = copy.deepcopy(pending)
        for item in self.children:
            if isinstance(item, discord.ui.RoleSelect):
                guild = ctx.host["bot"].get_guild(ctx.guild_id)
                item.placeholder = (
                    ctx.t("condition_role") + ": " + _option_role(guild, pending["role_id"])
                )[:150]
            elif isinstance(item, discord.ui.Select):
                for opt in item.options:
                    opt.default = opt.value == pending["op"]


class Confirmation(Base):
    def __init__(self, ctx, action, draft):
        super().__init__(ctx)
        self.action, self.draft = action, draft
        key = {"save": "confirm_save", "delete": "confirm_delete",
               "sync": "confirm_sync"}[action]
        self.button(key, self.confirm, row=0,
                    style=discord.ButtonStyle.danger if action in ("delete", "sync")
                    else discord.ButtonStyle.success)
        self.button("cancel", self.cancel, row=0, style=discord.ButtonStyle.danger)
        self.navigation(self.cancel, row=1)

    def summary(self, guild):
        info = {"save": "save_info", "delete": "delete_info",
                "sync": "sync_info"}[self.action]
        if self.action == "sync":
            detail = ""
        else:
            detail = f"\n**{self.ctx.t('main_role')}:** {_role(guild, self.draft['target_role_id'])}"
        return f"**{self.ctx.t('title')}**\n{self.ctx.t(info)}{detail}"

    async def cancel(self, interaction):
        if self.action == "sync":
            return await _render(interaction, ConnectionsList(self.ctx))
        return await _render(interaction, ConnectionEditor(self.ctx, self.draft))

    async def confirm(self, interaction):
        ctx = self.ctx
        guild = interaction.guild
        if self.action == "sync":
            if not any(rule.enabled for rule in ctx.rules()):
                return await _error(interaction, ctx.t("not_applicable"))
            if not interaction.response.is_done():
                await interaction.response.defer()
            try:
                checked, added, removed, exceeded = await engine.synchronize(
                    guild, connect=ctx.host["db_connect"], protected_ids=ctx.protected(),
                    blocked=ctx.blocked,
                )
            except Exception as exc:
                print(f"ROLE_CONNECTIONS status=SYNC_FAILED guild={guild.id} "
                      f"exception={type(exc).__name__}", flush=True)
                return await _error(interaction, ctx.t("error"))
            view = ConnectionsList(ctx)
            result = ctx.t("synced", checked=checked, added=added, removed=removed)
            if exceeded:
                result += "\n" + ctx.t("sync_partial")
            return await interaction.edit_original_response(
                content=view.summary(guild) + "\n\n" + result, embed=None, view=view
            )
        if self.action == "delete":
            result = engine.delete_rule(
                ctx.host["db_connect"], ctx.guild_id,
                self.draft["rule_id"], self.draft["revision"],
            )
            if not result:
                return await _error(interaction, ctx.t("stale_rule"))
            view = ConnectionsList(ctx)
            return await _render_with_note(interaction, view, ctx.t("deleted"))
        try:
            new = engine.save_rule(
                ctx.host["db_connect"], guild, name=self.draft["name"] or (
                    guild.get_role(self.draft["target_role_id"]).name
                    if guild.get_role(self.draft["target_role_id"]) else ""),
                target_role_id=self.draft["target_role_id"],
                groups=self.draft["groups"], groups_mode=self.draft["groups_mode"],
                rule_id=self.draft["rule_id"],
                expected_revision=self.draft["revision"],
                protected_ids=ctx.protected(),
            )
        except ValueError as exc:
            key = str(exc)
            return await _error(interaction, ctx.t(key) if key in LABELS["es-419"]
                                else ctx.t("error"))
        except Exception as exc:
            print(f"ROLE_CONNECTIONS status=SAVE_FAILED guild={guild.id} "
                  f"exception={type(exc).__name__}", flush=True)
            return await _error(interaction, ctx.t("error"))
        view = ConnectionsList(ctx)
        await _render_with_note(interaction, view, ctx.t("saved"))


async def _render_with_note(interaction, view, note):
    content = view.summary(interaction.guild) + "\n\n" + note
    if interaction.response.is_done():
        await interaction.edit_original_response(content=content, embed=None, view=view)
    else:
        await interaction.response.edit_message(content=content, embed=None, view=view)


def create_panel(host, guild_id, owner_id):
    ctx = Context(host, guild_id, owner_id)
    view = ConnectionsList(ctx)
    return view.summary(host["bot"].get_guild(guild_id)), view
