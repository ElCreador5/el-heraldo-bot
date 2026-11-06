"""Panel nativo de conexiones: condiciones directas y grupos avanzados.

El panel edita un borrador en memoria. Guardar requiere confirmación y
el motor de reglas existente sigue siendo la única fuente de persistencia.
"""
from __future__ import annotations

import copy
import inspect

import discord

import role_connections as engine
from panel_navigation import dismiss_panel
from operation_progress import ProgressReporter

_SYNC_IN_PROGRESS: set[int] = set()

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
        "unsafe_protected": "Ese rol está reservado para verificación, personalidad o moderación. Úsalo como condición y selecciona un rol principal diferente.",
        "unsafe_default": "El rol @everyone no puede administrarse mediante conexiones.",
        "unsafe_managed": "Ese rol lo administra una integración de Discord y no puede asignarse automáticamente.",
        "unsafe_bot_member": "No se pudo comprobar la posición de El Heraldo en la lista de roles. Revisa que esté conectado e inténtalo nuevamente.",
        "unsafe_bot_permissions": "El Heraldo necesita el permiso Gestionar roles para asignar el rol principal.",
        "unsafe_hierarchy": "El rol principal está al mismo nivel o por encima del rol más alto de El Heraldo. Mueve el rol de El Heraldo por encima de ese rol en Configuración del servidor → Roles.",
        "unsafe_privileged": "Este rol tiene permisos administrativos o de gestión. Por seguridad, las conexiones no pueden asignarlo.",
        "attention": "No se puede guardar esta conexión:",
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
        "sync_running": "**Conexiones de roles · Sincronizando**\nMiembros revisados: {checked} · Roles agregados: {added} · Roles retirados: {removed}\nLa operación sigue en curso. Los botones estarán disponibles al finalizar.",
        "sync_failed": "Sincronización interrumpida. Último avance registrado: {checked} miembros, {added} roles agregados, {removed} retirados. Algunos cambios pueden haberse aplicado.",
        "sync_busy": "Ya existe una sincronización de roles en curso en este servidor.",
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
        "conditions_header": "Condiciones",
        "preview": "Vista previa de la regla (no modifica roles)",
        "advanced_groups": "Grupos avanzados",
        "condition_operator": "Cambiar AND/OR",
        "group_overview": "Grupos de condiciones",
        "group_hint": "Usa grupos para combinar alternativas. AND exige todos; OR exige al menos uno.",
        "no_changes": "Guarda o descarta los cambios antes de activar o pausar.",
        "list_intro": "Asigna o retira automáticamente el rol principal cuando se cumplen sus condiciones.",
        "list_total": "Conexiones guardadas: {count}/{limit}",
        "list_hint": "Selecciona una conexión en el menú para editarla.",
        "role_hint": "Se asignará o retirará según las condiciones configuradas.",
        "conditions_empty": "Añade una condición para comenzar.",
        "editor_create": "Crear conexión",
        "editor_edit": "Editar conexión",
        "advanced_count": "Grupos: {count}/{limit}",
        "rule_count": "{count} condiciones · {op}",
        "groups_brief": "{count} grupos · {op} entre grupos",
        "mode_all": "AND · Todas las condiciones",
        "mode_any": "OR · Al menos una condición",
        "mode_xor": "XOR · Exactamente una condición",
        "mode_not": "NOT · Negar el conjunto AND",
        "mode_at_least": "Al menos N · Mínimo de condiciones",
        "minimum_select": "Selecciona cuántas condiciones exige el grupo",
        "minimum_option": "Al menos {count} de {total} condiciones",
        "at_least_label": "Al menos {count}",
        "invalid_minimum": "El mínimo debe estar entre 1 y el número de condiciones del grupo.",
        "advanced_operator_note": "XOR exige exactamente una; NOT significa que no se cumplen todas; Al menos N exige el mínimo seleccionado.",
        "advanced_edit_hint": "Los operadores avanzados se cambian desde Editar grupo.",
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
        "unsafe_protected": "This role is reserved for verification, personality, or moderation. Use it as a condition and choose a different main role.",
        "unsafe_default": "The @everyone role cannot be managed through connections.",
        "unsafe_managed": "A Discord integration manages this role; it cannot be assigned automatically.",
        "unsafe_bot_member": "El Heraldo could not verify its own role position. Ensure the bot is connected and try again.",
        "unsafe_bot_permissions": "El Heraldo needs the Manage Roles permission to assign the main role.",
        "unsafe_hierarchy": "The main role is at or above El Heraldo's highest role. Move El Heraldo's role above it in Server Settings → Roles.",
        "unsafe_privileged": "This role grants administrative or management permissions. Role connections cannot assign it for security reasons.",
        "attention": "Cannot save this connection:",
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
        "sync_running": "**Role connections · Syncing**\nMembers checked: {checked} · Roles added: {added} · Roles removed: {removed}\nThe operation is still running. Controls return when it finishes.",
        "sync_failed": "Sync interrupted. Last recorded progress: {checked} members, {added} roles added, {removed} removed. Some changes may already have been applied.",
        "sync_busy": "A role synchronization is already running in this server.",
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
        "conditions_header": "Conditions",
        "preview": "Rule preview (does not change roles)",
        "advanced_groups": "Advanced groups",
        "condition_operator": "Toggle AND/OR",
        "group_overview": "Condition groups",
        "group_hint": "Use groups to combine alternatives. AND requires all; OR requires at least one.",
        "no_changes": "Save or discard changes before activating or pausing.",
        "list_intro": "Automatically assign or remove a main role when its conditions are met.",
        "list_total": "Saved connections: {count}/{limit}",
        "list_hint": "Select a connection in the menu to edit it.",
        "role_hint": "Automatically assigned or removed according to the conditions.",
        "conditions_empty": "Add a condition to get started.",
        "editor_create": "Create connection",
        "editor_edit": "Edit connection",
        "advanced_count": "Groups: {count}/{limit}",
        "rule_count": "{count} conditions · {op}",
        "groups_brief": "{count} groups · {op} between groups",
        "mode_all": "AND · All conditions",
        "mode_any": "OR · At least one condition",
        "mode_xor": "XOR · Exactly one condition",
        "mode_not": "NOT · Negate the AND group",
        "mode_at_least": "At least N · Minimum conditions",
        "minimum_select": "Choose how many conditions the group requires",
        "minimum_option": "At least {count} of {total} conditions",
        "at_least_label": "At least {count}",
        "invalid_minimum": "Minimum must be between 1 and the number of conditions in the group.",
        "advanced_operator_note": "XOR requires exactly one; NOT means not all are met; At least N requires the selected minimum.",
        "advanced_edit_hint": "Advanced operators can be changed in Edit group.",
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
        "unsafe_protected": "Este cargo é reservado para verificação, personalidade ou moderação. Use-o como condição e escolha outro cargo principal.",
        "unsafe_default": "O cargo @everyone não pode ser gerenciado por conexões.",
        "unsafe_managed": "Uma integração do Discord gerencia este cargo; ele não pode ser atribuído automaticamente.",
        "unsafe_bot_member": "Não foi possível verificar a posição do cargo de El Heraldo. Confira se o bot está conectado e tente novamente.",
        "unsafe_bot_permissions": "El Heraldo precisa da permissão Gerenciar cargos para atribuir o cargo principal.",
        "unsafe_hierarchy": "O cargo principal está no mesmo nível ou acima do cargo mais alto de El Heraldo. Mova o cargo de El Heraldo para cima em Configurações do servidor → Cargos.",
        "unsafe_privileged": "Este cargo possui permissões administrativas ou de gerenciamento. Por segurança, as conexões não podem atribuí-lo.",
        "attention": "Não é possível salvar esta conexão:",
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
        "sync_running": "**Conexões de cargos · Sincronizando**\nMembros revisados: {checked} · Cargos adicionados: {added} · Cargos removidos: {removed}\nA operação continua em andamento. Os botões voltarão ao final.",
        "sync_failed": "Sincronização interrompida. Último avanço registrado: {checked} membros, {added} cargos adicionados, {removed} removidos. Algumas alterações podem ter sido aplicadas.",
        "sync_busy": "Uma sincronização de cargos já está em andamento neste servidor.",
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
        "conditions_header": "Condições",
        "preview": "Prévia da regra (não altera cargos)",
        "advanced_groups": "Grupos avançados",
        "condition_operator": "Alternar AND/OR",
        "group_overview": "Grupos de condições",
        "group_hint": "Use grupos para combinar alternativas. AND exige todas; OR exige ao menos uma.",
        "no_changes": "Salve ou descarte as alterações antes de ativar ou pausar.",
        "list_intro": "Atribua ou remova automaticamente o cargo principal ao cumprir as condições.",
        "list_total": "Conexões salvas: {count}/{limit}",
        "list_hint": "Selecione uma conexão no menu para editá-la.",
        "role_hint": "Será atribuído ou removido conforme as condições configuradas.",
        "conditions_empty": "Adicione uma condição para começar.",
        "editor_create": "Criar conexão",
        "editor_edit": "Editar conexão",
        "advanced_count": "Grupos: {count}/{limit}",
        "rule_count": "{count} condições · {op}",
        "groups_brief": "{count} grupos · {op} entre grupos",
        "mode_all": "AND · Todas as condições",
        "mode_any": "OR · Pelo menos uma condição",
        "mode_xor": "XOR · Exatamente uma condição",
        "mode_not": "NOT · Negar o grupo AND",
        "mode_at_least": "Pelo menos N · Mínimo de condições",
        "minimum_select": "Escolha quantas condições o grupo exige",
        "minimum_option": "Pelo menos {count} de {total} condições",
        "at_least_label": "Pelo menos {count}",
        "invalid_minimum": "O mínimo deve estar entre 1 e o número de condições do grupo.",
        "advanced_operator_note": "XOR exige exatamente uma; NOT significa que nem todas são atendidas; Pelo menos N exige o mínimo selecionado.",
        "advanced_edit_hint": "Operadores avançados podem ser alterados em Editar grupo.",
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


def _operator(mode):
    """Human-facing labels: internal values remain stable in groups_json."""
    return {"all": "AND", "any": "OR", "xor": "XOR",
            "not": "NOT", "at_least": "N"}[mode]


def _group_operator(ctx, group):
    if group["mode"] == "at_least":
        return ctx.t("at_least_label", count=group.get("min_required", 1))
    return _operator(group["mode"])


def _format_groups(ctx, guild, groups, mode):
    """Compact hierarchy: group header, numbered conditions, clear operators."""
    lines = []
    for index, group in enumerate(groups, 1):
        if index > 1:
            lines.append(f"**{_operator(mode)}**")
        count = len(group["conditions"])
        if len(groups) == 1:
            heading = (
                f"{ctx.t('conditions_header')} · {count}/{engine.MAX_CONDITIONS}"
                f" · {_group_operator(ctx, group)}"
            )
        else:
            heading = ctx.t(
                "group_status", n=index, mode=_group_operator(ctx, group), count=count
            )
        lines.append(f"**{heading}**")
        if not group["conditions"]:
            lines.append(f"> *{ctx.t('conditions_empty')}*")
        for number, condition in enumerate(group["conditions"], 1):
            expression = ctx.t("has" if condition["op"] == "has" else "lacks")
            lines.append(
                f"> {number}. {expression} {_role(guild, condition.get('role_id'))}"
            )
        if index != len(groups):
            lines.append("")
    return "\n" + "\n".join(lines)


def _draft_values(draft):
    """Only persisted values count as changes, never the selected UI group."""
    return {
        "target_role_id": draft["target_role_id"], "name": draft["name"],
        "groups": copy.deepcopy(draft["groups"]),
        "groups_mode": draft["groups_mode"],
    }


def draft_changed(draft):
    return _draft_values(draft) != draft["original"]


def draft_can_save(draft, *, guild=None, protected_ids=()):
    if not draft_changed(draft) or not draft["target_role_id"]:
        return False
    try:
        engine.validate_groups(
            draft["groups"], draft["groups_mode"], draft["target_role_id"]
        )
    except (ValueError, TypeError):
        return False
    if guild is not None and engine.target_safety_reason(
        guild, guild.get_role(draft["target_role_id"]), protected_ids
    ):
        return False
    return True


def new_draft(rule=None):
    if rule is None:
        draft = {
            "rule_id": None, "revision": None, "target_role_id": None, "name": "",
            "groups": [{"mode": "all", "conditions": []}],
            "groups_mode": "any", "group_index": 0,
        }
    else:
        draft = {
            "rule_id": rule.rule_id, "revision": rule.revision,
            "target_role_id": rule.target_role_id, "name": rule.name,
            "groups": copy.deepcopy(list(rule.groups)), "groups_mode": rule.groups_mode,
            "group_index": 0,
        }
    draft["original"] = _draft_values(draft)
    return draft


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

    def button(self, key, callback, *, row, style=discord.ButtonStyle.primary,
               disabled=False, label=None):
        item = discord.ui.Button(label=label or self.ctx.t(key), row=row,
                                 style=style, disabled=disabled)
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
        ctx = self.ctx
        out = [
            f"**{ctx.t('title')}**",
            ctx.t("list_intro"),
            "",
            f"**{ctx.t('list_total', count=len(rules), limit=engine.MAX_RULES)}**",
        ]
        if not rules:
            out.append(f"*{ctx.t('empty')}*")
        for index, rule in enumerate(rules, 1):
            out.append(
                f"\n**{index}. {_role(guild, rule.target_role_id)}** "
                f"· {ctx.t('enabled' if rule.enabled else 'disabled')}"
            )
            if len(rule.groups) == 1:
                group = rule.groups[0]
                terms = [
                    ctx.t("has" if c["op"] == "has" else "lacks")
                    + " " + _role(guild, c["role_id"])
                    for c in group["conditions"][:2]
                ]
                separator = " **" + _group_operator(ctx, group) + "** "
                text = separator.join(terms)
                remaining = len(group["conditions"]) - 2
                if remaining > 0:
                    text += f" · +{remaining}"
                out.append(
                    f"> **{_group_operator(ctx, group)}** · {text}"
                )
            else:
                out.append(
                    "> " + ctx.t(
                        "groups_brief", count=len(rule.groups),
                        op=_operator(rule.groups_mode)
                    )
                )
        out.append(f"\n*{ctx.t('list_hint')}*")
        return "\n".join(out)[:3900]

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
    """Everyday editor: main role and first group directly on this screen."""
    def __init__(self, ctx, draft):
        super().__init__(ctx)
        self.draft = draft
        guild = ctx.host["bot"].get_guild(ctx.guild_id)
        protected_ids = ctx.protected()
        self.target_warning = (
            engine.target_safety_reason(
                guild, guild.get_role(draft["target_role_id"]), protected_ids
            )
            if guild is not None and draft["target_role_id"] else None
        )
        self.target = discord.ui.RoleSelect(
            placeholder=ctx.t("target") + (
                f": {_option_role(guild, draft['target_role_id'])}"
                if draft["target_role_id"] else ""),
            row=0, min_values=1, max_values=1,
        )
        if (draft["target_role_id"]
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

        primary = draft["groups"][0]
        if primary["conditions"]:
            selector = discord.ui.Select(
                placeholder=ctx.t("condition"), row=1,
                options=[
                    discord.SelectOption(
                        label=(f"{i + 1}. "
                               f"{ctx.t('has' if condition['op'] == 'has' else 'lacks')}: "
                               f"{_option_role(guild, condition['role_id'])}")[:100],
                        value=str(i),
                    )
                    for i, condition in enumerate(primary["conditions"])
                ],
            )

            async def picked(interaction):
                await _render(interaction, ConditionEditor(
                    ctx, self.draft, 0, int(selector.values[0]),
                    return_to="connection",
                ))

            selector.callback = picked
            self.add_item(selector)

        self.button("add_condition", self.add_condition, row=2,
                    disabled=len(primary["conditions"]) >= engine.MAX_CONDITIONS)
        self.button("condition_operator", self.toggle_conditions, row=2,
                    style=discord.ButtonStyle.secondary,
                    label=f"{ctx.t('conditions_header')}: {_group_operator(ctx, primary)}",
                    disabled=primary["mode"] not in ("all", "any"))
        self.button("advanced_groups", self.advanced, row=2,
                    style=discord.ButtonStyle.secondary)

        self.button("save", self.save, row=3, style=discord.ButtonStyle.success,
                    disabled=not draft_can_save(
                        draft, guild=guild, protected_ids=protected_ids
                    ))
        self.button("discard", self.discard, row=3, style=discord.ButtonStyle.secondary,
                    disabled=not draft_changed(draft))
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
        ctx = self.ctx
        rule_name = self.draft["name"] or ctx.t("title")
        action = ctx.t("editor_edit" if self.draft["rule_id"] else "editor_create")
        warning = (
            f"\n\n**{ctx.t('attention')}** {ctx.t(self.target_warning)}"
            if self.target_warning else ""
        )
        note = (
            f"\n\n*{ctx.t('draft')}*"
            if draft_changed(self.draft) else ""
        )
        groups = self.draft["groups"]
        summary = (
            f"**{ctx.t('title')} · {action}**\n"
            f"*{discord.utils.escape_markdown(rule_name)}*\n\n"
            f"**{ctx.t('main_role')}**\n"
            f"{_role(guild, self.draft['target_role_id'])}\n"
            f"*{ctx.t('role_hint')}*\n"
            f"{_format_groups(ctx, guild, groups, self.draft['groups_mode'])}"
        )
        if len(groups) > 1:
            summary += (
                f"\n\n*{ctx.t('advanced_count', count=len(groups), limit=engine.MAX_GROUPS)}*"
            )
        return (summary + warning + note)[:3900]

    async def add_condition(self, interaction):
        if len(self.draft["groups"][0]["conditions"]) >= engine.MAX_CONDITIONS:
            return await _error(interaction, self.ctx.t("limit_conditions"))
        await _render(interaction, ConditionEditor(
            self.ctx, self.draft, 0, None, return_to="connection"
        ))

    async def toggle_conditions(self, interaction):
        group = self.draft["groups"][0]
        if group["mode"] not in ("all", "any"):
            return await _error(interaction, self.ctx.t("advanced_edit_hint"))
        group["mode"] = "any" if group["mode"] == "all" else "all"
        await _render(interaction, ConnectionEditor(self.ctx, self.draft))

    async def advanced(self, interaction):
        await _render(interaction, AdvancedGroups(self.ctx, self.draft))

    async def save(self, interaction):
        if not draft_changed(self.draft):
            return await _error(interaction, self.ctx.t("error"))
        if self.draft["target_role_id"] is None:
            return await _error(interaction, self.ctx.t("no_target"))
        guild = interaction.guild
        safety_reason = engine.target_safety_reason(
            guild, guild.get_role(self.draft["target_role_id"]), self.ctx.protected()
        )
        if safety_reason:
            return await _error(interaction, self.ctx.t(safety_reason))
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
        if draft_changed(self.draft):
            return await _error(interaction, self.ctx.t("no_changes"))
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


class AdvancedGroups(Base):
    """Only this advanced screen exposes group selection and cross-group AND/OR."""
    def __init__(self, ctx, draft):
        super().__init__(ctx)
        self.draft = draft
        opts = [
            discord.SelectOption(
                label=ctx.t("group_status", n=i + 1,
                            mode=_group_operator(ctx, g), count=len(g["conditions"])),
                value=str(i), default=(i == draft["group_index"]),
            )
            for i, g in enumerate(draft["groups"])
        ]
        selector = discord.ui.Select(placeholder=ctx.t("group"), row=0, options=opts)

        async def picked(interaction):
            self.draft["group_index"] = int(selector.values[0])
            await _render(interaction, AdvancedGroups(ctx, self.draft))

        selector.callback = picked
        self.add_item(selector)
        self.button("edit_group", self.edit_group, row=1)
        self.button("new_group", self.new_group, row=1,
                    disabled=len(draft["groups"]) >= engine.MAX_GROUPS)
        self.button("group_operator", self.toggle_group_mode, row=1,
                    style=discord.ButtonStyle.secondary,
                    disabled=len(draft["groups"]) < 2,
                    label=f"{ctx.t('group_operator')}: {_operator(draft['groups_mode'])}")
        self.navigation(self.back, row=2)

    def summary(self, guild):
        ctx = self.ctx
        groups = self.draft["groups"]
        note = f"\n\n*{ctx.t('draft')}*" if draft_changed(self.draft) else ""
        return (
            f"**{ctx.t('title')} · {ctx.t('group_overview')}**\n"
            f"*{ctx.t('advanced_count', count=len(groups), limit=engine.MAX_GROUPS)}*\n"
            f"{ctx.t('group_hint')}"
            f"{_format_groups(ctx, guild, groups, self.draft['groups_mode'])}"
            f"{note}"
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
        await _render(interaction, AdvancedGroups(self.ctx, self.draft))

    async def back(self, interaction):
        await _render(interaction, ConnectionEditor(self.ctx, self.draft))


class GroupEditor(Base):
    """Advanced group editor with a persistent mode and numeric threshold."""
    def __init__(self, ctx, draft):
        super().__init__(ctx)
        self.draft = draft
        self.index = draft["group_index"]
        group = draft["groups"][self.index]
        guild = ctx.host["bot"].get_guild(ctx.guild_id)

        if group["conditions"]:
            conditions = discord.ui.Select(
                placeholder=ctx.t("condition"), row=0,
                options=[
                    discord.SelectOption(
                        label=(f"{i+1}. "
                               f"{ctx.t('has' if c['op'] == 'has' else 'lacks')}: "
                               f"{_option_role(guild, c['role_id'])}")[:100],
                        value=str(i),
                    )
                    for i, c in enumerate(group["conditions"])
                ],
            )

            async def selected_condition(interaction):
                await _render(interaction, ConditionEditor(
                    ctx, draft, self.index, int(conditions.values[0])
                ))

            conditions.callback = selected_condition
            self.add_item(conditions)

        operator_row = 1 if group["conditions"] else 0
        mode_selector = discord.ui.Select(
            placeholder=ctx.t("group_mode"), row=operator_row,
            options=[
                discord.SelectOption(
                    label=ctx.t(f"mode_{mode}"),
                    value=mode, default=group["mode"] == mode,
                )
                for mode in ("all", "any", "xor", "not", "at_least")
            ],
        )

        async def mode_changed(interaction):
            selected = mode_selector.values[0]
            group["mode"] = selected
            if selected == "at_least":
                group["min_required"] = min(
                    max(1, int(group.get("min_required", 1))),
                    max(1, len(group["conditions"])),
                )
            else:
                group.pop("min_required", None)
            await _render(interaction, GroupEditor(ctx, draft))

        mode_selector.callback = mode_changed
        self.add_item(mode_selector)

        if group["mode"] == "at_least":
            count = max(1, len(group["conditions"]))
            minimum = group.get("min_required", 1)
            minimum_select = discord.ui.Select(
                placeholder=ctx.t("minimum_select"), row=operator_row + 1,
                options=[
                    discord.SelectOption(
                        label=ctx.t("minimum_option", count=n, total=len(group["conditions"])),
                        value=str(n), default=n == minimum,
                    )
                    for n in range(1, count + 1)
                ],
            )

            async def minimum_changed(interaction):
                group["min_required"] = int(minimum_select.values[0])
                await _render(interaction, GroupEditor(ctx, draft))

            minimum_select.callback = minimum_changed
            self.add_item(minimum_select)

        actions_row = operator_row + (2 if group["mode"] == "at_least" else 1)
        self.button("add_condition", self.add_condition, row=actions_row,
                    disabled=len(group["conditions"]) >= engine.MAX_CONDITIONS)
        self.button("delete_group", self.delete, row=actions_row,
                    style=discord.ButtonStyle.danger,
                    disabled=len(draft["groups"]) == 1)
        self.navigation(self.back, row=actions_row+1)

    def summary(self, guild):
        group = self.draft["groups"][self.index]
        ctx = self.ctx
        details = _format_groups(ctx, guild, [group], self.draft["groups_mode"])
        return (
            f"**{ctx.t('title')} · {ctx.t('group_status', n=self.index+1, mode=_group_operator(ctx, group), count=len(group['conditions']))}**"
            f"{details}\n{ctx.t('advanced_operator_note')}\n\n*{ctx.t('draft')}*"
        )[:3900]

    async def add_condition(self, interaction):
        if len(self.draft["groups"][self.index]["conditions"]) >= engine.MAX_CONDITIONS:
            return await _error(interaction, self.ctx.t("limit_conditions"))
        await _render(interaction, ConditionEditor(self.ctx, self.draft, self.index, None))

    async def delete(self, interaction):
        if len(self.draft["groups"]) <= 1:
            return await _error(interaction, self.ctx.t("no_group_delete"))
        self.draft["groups"].pop(self.index)
        self.draft["group_index"] = max(0, self.index - 1)
        await _render(interaction, AdvancedGroups(self.ctx, self.draft))

    async def back(self, interaction):
        await _render(interaction, AdvancedGroups(self.ctx, self.draft))


class ConditionEditor(Base):
    def __init__(self, ctx, draft, group_index, index, *, return_to="group"):
        super().__init__(ctx)
        self.draft, self.group_index, self.index = draft, group_index, index
        self.return_to = return_to
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
            self.ctx, self.draft, self.group_index, self.index, self.pending,
            return_to=self.return_to,
        )

    def summary(self, guild):
        return (
            f"**{self.ctx.t('title')} — {self.ctx.t('group_status', n=self.group_index+1, mode=_group_operator(self.ctx, self.draft['groups'][self.group_index]), count=len(self.draft['groups'][self.group_index]['conditions']))}**"
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
        await self._return(interaction)

    async def delete(self, interaction):
        group = self.draft["groups"][self.group_index]
        group["conditions"].pop(self.index)
        if group["mode"] == "at_least":
            group["min_required"] = min(
                group["min_required"], max(1, len(group["conditions"]))
            )
        await self._return(interaction)

    async def back(self, interaction):
        await self._return(interaction)

    async def _return(self, interaction):
        view = (ConnectionEditor(self.ctx, self.draft)
                if self.return_to == "connection"
                else GroupEditor(self.ctx, self.draft))
        await _render(interaction, view)


class ConditionEditorWithPending(ConditionEditor):
    """Rebuild from temporary selection without silently writing it to the rule."""
    def __init__(self, ctx, draft, group_index, index, pending, *, return_to="group"):
        super().__init__(ctx, draft, group_index, index, return_to=return_to)
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
                    style=(discord.ButtonStyle.danger if action == "delete"
                           else discord.ButtonStyle.success))
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
            if guild.id in _SYNC_IN_PROGRESS:
                return await _error(interaction, ctx.t("sync_busy"))
            _SYNC_IN_PROGRESS.add(guild.id)
            checked = added = removed = 0

            def running_text():
                return ctx.t("sync_running", checked=checked, added=added, removed=removed)

            try:
                # Acknowledge immediately and remove the confirmation buttons while
                # Discord is processing members. Never run the batch twice.
                if interaction.response.is_done():
                    await interaction.edit_original_response(
                        content=running_text(), embed=None, view=None
                    )
                else:
                    await interaction.response.edit_message(
                        content=running_text(), embed=None, view=None
                    )
                progress_panel = ProgressReporter(
                    lambda content: interaction.edit_original_response(
                        content=content, embed=None, view=None
                    )
                )

                async def report(count, count_added, count_removed):
                    nonlocal checked, added, removed
                    checked, added, removed = count, count_added, count_removed
                    await progress_panel.publish(running_text())

                checked, added, removed, exceeded = await engine.synchronize(
                    guild, connect=ctx.host["db_connect"], protected_ids=ctx.protected(),
                    blocked=ctx.blocked, progress=report,
                )
                result = ctx.t("synced", checked=checked, added=added, removed=removed)
                if exceeded:
                    result += "\n" + ctx.t("sync_partial")
            except Exception as exc:
                print(f"ROLE_CONNECTIONS status=SYNC_FAILED guild={guild.id} "
                      f"exception={type(exc).__name__}", flush=True)
                result = ctx.t("sync_failed", checked=checked, added=added, removed=removed)
                if not interaction.response.is_done():
                    return await _error(interaction, result)
            finally:
                _SYNC_IN_PROGRESS.discard(guild.id)

            view = ConnectionsList(ctx)
            # Discord caps message content at 2,000 characters.
            heading = view.summary(guild)
            content = heading[:max(0, 2000 - len(result) - 2)] + "\n\n" + result
            return await interaction.edit_original_response(
                content=content, embed=None, view=view
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
