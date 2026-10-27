"""Revisión administrativa de un reporte completo, sin sanciones automáticas."""
from __future__ import annotations
import asyncio
from contextlib import closing
import json
import os
import re
import discord
from heraldo_i18n import text as _t, guild_context as _i18n_context, variants
from custodio_discipline import ReviewedIncident
from custodio_source import load_server_rules
from custodio_server_rule_actions_setup import SETTING_KEY, decode, decode_durations, ACTIONS
from custodio_reports import _get_safe_existing

PREFIX = "custodio-review:"


def report_review_view(source_message_id):
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label=_t("text.custodio.review"), style=discord.ButtonStyle.primary,
                                   custom_id=PREFIX + str(source_message_id)))
    return view


def allowed(interaction):
    return bool(interaction.guild and (interaction.user.id == interaction.guild.owner_id
                or interaction.user.guild_permissions.administrator))


class CustodioReviewPanel(discord.ui.View):
    @_i18n_context
    def __init__(self, namespace, owner_id, snapshot, incident):
        super().__init__(timeout=300)
        self.n, self.owner_id, self.snapshot, self.incident = namespace, owner_id, snapshot, incident
        self.guild_id = snapshot.guild_id
        self.raw = self.n["guild_config_get"](self.guild_id, SETTING_KEY)
        self.action = decode(self.raw, snapshot)[incident.rule_number - 1]
        self.duration = decode_durations(self.raw, snapshot)[incident.rule_number - 1]
        self.done = False
        self.confirm.style = discord.ButtonStyle.success if self.action == "report" else discord.ButtonStyle.danger

    @_i18n_context
    def summary(self):
        labels = {value: label for value, label, _ in ACTIONS}
        rule = self.snapshot.rules[self.incident.rule_number - 1]
        quote = rule[:900] + (str(_t("text.custodio.excerpt")) if len(rule) > 900 else "")
        return str(_t("text.custodio.review_panel", rule=self.incident.rule_number, quote=quote,
                      action=str(labels[self.action]), duration=self.duration, reference=self.incident.report_url))

    @_i18n_context
    async def interaction_check(self, interaction):
        if (self.done or interaction.user.id != self.owner_id
                or interaction.guild_id != self.guild_id or not allowed(interaction)):
            await interaction.response.edit_message(content=str(_t("text.custodio.review_blocked")), view=None, embed=None)
            return False
        return True

    @discord.ui.button(label=_t('text.8b43fae929eaa0'), style=discord.ButtonStyle.danger)
    @_i18n_context
    async def confirm(self, interaction, button):
        if not await self.interaction_check(interaction):
            return
        self.done = True
        await interaction.response.defer(thinking=False)
        try:
            if self.n["guild_config_get"](self.guild_id, SETTING_KEY) != self.raw:
                raise ValueError("stale_action_configuration")
            result = await self.n["custodio_discipline_engine"].execute(
                interaction.guild, self.incident, self.snapshot, action=self.action,
                duration_minutes=self.duration, verified=True, administrator_confirmed=True,
                automatic=False, moderator_id=interaction.user.id)
            actual_action = result.get("action", "report")
            notice = _t("text.custodio.review_complete", action=str(dict((a, label) for a,label,_ in ACTIONS)[actual_action]),
                        case=result.get("case_number") or "—")
            # Editar únicamente la medida; nunca reescribir la transcripción.
            match = re.fullmatch(r"https://discord.com/channels/(\d+)/(\d+)/(\d+)", self.incident.report_url)
            channel = _get_safe_existing(interaction.guild, int(match.group(2)))
            report = await channel.fetch_message(int(match.group(3)))
            embeds = [embed.copy() for embed in report.embeds]
            for embed in embeds:
                for index, field in enumerate(embed.fields):
                    if field.name in variants('text.a71bc39fe3f33e'):
                        embed.set_field_at(index, name=field.name, value=str(notice), inline=field.inline)
            await report.edit(embeds=embeds, allowed_mentions=discord.AllowedMentions.none())
        except Exception:
            notice = _t("text.custodio.review_uncertain")
        await interaction.edit_original_response(content=str(notice), view=None, embed=None)

    @discord.ui.button(label=_t('text.80ca383e9c8d3e'), style=discord.ButtonStyle.danger)
    @_i18n_context
    async def discard(self, interaction, button):
        self.done = True
        await interaction.response.edit_message(content=str(_t("text.custodio.review_discarded")), view=None, embed=None)


@_i18n_context
async def dispatch(namespace, interaction):
    data = interaction.data or {}
    custom_id = data.get("custom_id", "")
    if not isinstance(custom_id, str) or not custom_id.startswith(PREFIX):
        return False
    try:
        await interaction.response.defer(ephemeral=True, thinking=True)
    except discord.HTTPException:
        return True
    try:
        if not allowed(interaction):
            raise ValueError("administrator_required")
        message_id = int(custom_id[len(PREFIX):])
        key = f"custodio-report:{interaction.guild.id}:{message_id}"
        def get_receipt():
            with closing(namespace["db_connect"]()) as db:
                return db.execute("SELECT status, receipts FROM evidence_archive_v1 WHERE evidence_key=?", (key,)).fetchone()
        row = await asyncio.to_thread(get_receipt)
        if row is None or row[0] != "complete":
            raise ValueError("complete_evidence_required")
        receipt = json.loads(row[1])[0]
        if (interaction.message.id != receipt["message_id"]
                or interaction.message.author.id != interaction.client.user.id
                or interaction.channel_id != receipt["channel_id"]):
            raise ValueError("report_context_mismatch")
        _get_safe_existing(interaction.guild, interaction.channel_id)
        snapshot = await load_server_rules(interaction.guild.id, os.environ.get("DISCORD_TOKEN", ""))
        if snapshot.revision != receipt.get("rules_revision"):
            raise ValueError("stale_rules")
        incident = ReviewedIncident(interaction.guild.id, message_id, receipt["actor_id"], receipt["rule_number"],
            snapshot.revision, f"https://discord.com/channels/{interaction.guild.id}/{interaction.channel_id}/{interaction.message.id}")
        view = CustodioReviewPanel(namespace, interaction.user.id, snapshot, incident)
        await interaction.edit_original_response(content=view.summary(), view=view, embed=None)
    except Exception:
        await interaction.edit_original_response(content=str(_t("text.custodio.review_blocked")), view=None, embed=None)
    return True
