"""Adaptador de las cinco acciones al sistema central. No activa sanciones.

El runtime Observar no llama este ejecutor. Las medidas requieren una revisión
verificada y una autorización administrativa explícita; nunca vienen de la IA.
"""
from __future__ import annotations
import asyncio
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import re
import discord
from heraldo_i18n import text as _t, guild_context as _i18n_context
from custodio_runtime import protected
from custodio_rule_actions import VALID_ACTIONS
from evidence_archive import ledger


@dataclass(frozen=True)
class ReviewedIncident:
    guild_id: int
    message_id: int
    actor_id: int
    rule_number: int
    revision: str
    report_url: str


class DisciplineBlocked(ValueError):
    pass


class CustodioDiscipline:
    def __init__(self, namespace):
        self.n = namespace

    @_i18n_context
    async def execute(self, guild, incident, snapshot, *, action="report",
                      duration_minutes=60, verified=False, administrator_confirmed=False,
                      automatic=False, moderator_id=None):
        if (automatic or verified is not True or administrator_confirmed is not True
                or action not in VALID_ACTIONS or guild.id != incident.guild_id
                or snapshot.guild_id != guild.id or snapshot.revision != incident.revision
                or not 1 <= incident.rule_number <= snapshot.count
                or incident.actor_id == guild.owner_id):
            raise DisciplineBlocked("review_and_administrator_confirmation_required")
        reviewer = guild.get_member(moderator_id) if moderator_id else None
        if reviewer is None or (reviewer.id != guild.owner_id and not reviewer.guild_permissions.administrator):
            raise DisciplineBlocked("administrator_required")
        key = f"custodio-action:{guild.id}:{incident.message_id}"
        import sqlite3
        import json
        with closing(self.n["db_connect"]()) as db:
            try:
                prior = db.execute("SELECT status,receipts FROM evidence_archive_v1 WHERE evidence_key=?", (key,)).fetchone()
            except sqlite3.OperationalError:
                prior = None
        if prior:
            if prior[0] == "complete":
                return json.loads(prior[1])[0]
            raise DisciplineBlocked("uncertain_action_requires_review")
        if action == "report":
            return {"status": "observed", "case_number": None, "action": "report"}
        if action == "temp_ban" and (type(duration_minutes) is not int or not 1 <= duration_minutes <= 43200):
            raise DisciplineBlocked("invalid_temp_ban_duration")
        # No conceder autorización mediante un bool externo: el revisor conserva
        # permiso actual en el servidor y su jerarquía se valida antes de actuar.
        member = await guild.fetch_member(incident.actor_id)
        if protected(member) or guild.me is None:
            raise DisciplineBlocked("protected_member")
        required = {"warn": None, "kick": "kick_members", "ban": "ban_members", "temp_ban": "ban_members"}[action]
        if (member.top_role >= guild.me.top_role
                or reviewer.id != guild.owner_id and member.top_role >= reviewer.top_role
                or required and not getattr(guild.me.guild_permissions, required, False)):
            raise DisciplineBlocked("permissions_or_hierarchy")
        # La evidencia debe estar completa y ser una copia propia aún disponible.
        report_key = f"custodio-report:{guild.id}:{incident.message_id}"
        with closing(self.n["db_connect"]()) as db:
            row = db.execute("SELECT status, receipts FROM evidence_archive_v1 WHERE evidence_key=?", (report_key,)).fetchone()
        import json
        if not row or row[0] != "complete":
            raise DisciplineBlocked("complete_evidence_required")
        receipts = json.loads(row[1])
        if not receipts or incident.report_url != f"https://discord.com/channels/{guild.id}/{receipts[0]['channel_id']}/{receipts[0]['message_id']}":
            raise DisciplineBlocked("invalid_report_reference")
        from custodio_reports import _get_safe_existing
        channel = _get_safe_existing(guild, receipts[0]["channel_id"])
        for receipt in receipts:
            copy = await channel.fetch_message(receipt["message_id"])
            if copy.author.id != guild.me.id:
                raise DisciplineBlocked("evidence_author_mismatch")
        if (receipts[0].get("actor_id") != member.id
                or receipts[0].get("rule_number") != incident.rule_number
                or receipts[0].get("rules_revision") != snapshot.revision):
            raise DisciplineBlocked("evidence_metadata_mismatch")
        # Recuperar reglas nuevamente justo antes de la reclamación persistente.
        from custodio_source import load_server_rules
        import os
        fresh = await load_server_rules(guild.id, os.environ.get("DISCORD_TOKEN", ""))
        if fresh.revision != snapshot.revision or protected(member):
            raise DisciplineBlocked("rules_or_exemptions_changed")
        if action in {"ban", "temp_ban"}:
            try:
                await guild.fetch_ban(discord.Object(id=member.id))
            except discord.NotFound:
                pass
            else:
                raise DisciplineBlocked("existing_ban_requires_review")
        claimed, state, result = await asyncio.to_thread(ledger, self.n["DB_PATH"], key, "claim")
        if not claimed:
            if state == "complete":
                return result[0]
            raise DisciplineBlocked("uncertain_action_requires_review")
        if protected(member):
            raise DisciplineBlocked("protected_member")
        policy = "custodio:" + sha256(snapshot.rules[incident.rule_number - 1].encode()).hexdigest()
        reason = str(_t("text.custodio.case_reason", rule=incident.rule_number, reference=incident.message_id))
        case = None
        try:
            if action == "warn":
                case, active, limit = self.n["moderation_warning_create"](
                    guild.id, member.id, reason, duration_minutes=43200,
                    author_id=reviewer.id, proof=incident.report_url,
                    history_ref=incident.report_url, policy_ref=policy)
                # Un mes SIN reincidencia de esta conducta; conservar el historial.
                expires = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
                with closing(self.n["db_connect"]()) as db, db:
                    db.execute("UPDATE moderation_cases SET expires_at=? WHERE guild_id=? AND user_id=? "
                               "AND type='WARN' AND open=1 AND moderator_notes=?",
                               (expires, guild.id, member.id, policy))
                await self.n["moderation_warning_escalation"](guild, member, case, active, limit)
            else:
                kind = "KICK" if action == "kick" else "BAN"
                duration = duration_minutes if action == "temp_ban" else None
                case = self.n["moderation_case_create"](guild.id, kind, member.id, reason,
                    duration_minutes=duration, author_id=reviewer.id, proof=incident.report_url,
                    moderator_notes=policy + "|pending\n" + str(_t("text.custodio.measure_pending")), history_ref=incident.report_url)
                # Crear la fecha de caducidad ANTES del ban permite recuperarlo
                # tras una caída. El expirador compara la razón única de Custodio.
                if action == "kick":
                    await self.n["heraldo_kick"](member, reason=reason)
                else:
                    await self.n["heraldo_ban"](member, reason=reason, delete_message_seconds=0,
                                               duration_minutes=duration if duration is not None else 0,
                                               record_case=False)
                with closing(self.n["db_connect"]()) as db, db:
                    expiry = (datetime.now(timezone.utc) + timedelta(minutes=duration)).isoformat() if duration is not None else None
                    db.execute("UPDATE moderation_cases SET moderator_notes=?, expires_at=? WHERE guild_id=? AND case_number=? AND open=1",
                               (policy + "|complete\n" + str(_t("text.custodio.measure_confirmed")), expiry, guild.id, case))
                    linked = db.execute("SELECT case_number FROM moderation_cases WHERE guild_id=? AND user_id=? "
                                        "AND type='WARN' AND open=1 AND moderator_notes=?", (guild.id, member.id, policy)).fetchall()
                for warning in linked:
                    self.n["moderation_case_close"](guild.id, int(warning[0]), closed_by=reviewer.id,
                                                     resolution=str(_t("text.custodio.warning_served")))
            result = {"status": "complete", "case_number": case, "action": action}
            await asyncio.to_thread(ledger, self.n["DB_PATH"], key, "complete", [result])
            if action == "warn" and callable(getattr(member, "send", None)):
                embed = discord.Embed(title=_t("text.custodio.warn_title"),
                    description=_t("text.custodio.warn_notice", rule=snapshot.rules[incident.rule_number - 1]),
                    color=discord.Color.orange(), timestamp=datetime.now(timezone.utc))
                embed.set_footer(text=self.n["LAB_FOOTER_TEXT"], icon_url=str(guild.icon.url) if guild.icon else None)
                try:
                    await member.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
                except discord.HTTPException:
                    pass  # El reporte privado permite al administrador verificar el aviso.
            return result
        except discord.Forbidden:
            if case is not None:
                self.n["moderation_case_close"](guild.id, case, closed_by=None,
                                                resolution=str(_t("text.custodio.action_failed")))
            raise
        # Cualquier resultado incierto conserva pending y no se repite a ciegas.
