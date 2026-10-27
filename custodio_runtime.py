"""Adaptador de Observar: eventos reales, reglas frescas, evidencia privada.

No ejecuta IA ni sanciones. La aprobación de detectores por regla y el botón
Activar son requisitos separados, ambos desactivados de forma predeterminada.
"""
from __future__ import annotations
import asyncio
from collections import OrderedDict
from contextlib import closing
import json
import os
import time

import discord
from discord.ext import tasks
from heraldo_i18n import text as _t, guild_context as _i18n_context
from custodio_detection import LocalDetector, image_fingerprint, KIND_KEYS
from custodio_policy import KEY, ObservePolicy
from custodio_interpretation import KEY as PLAN_KEY, InterpretationPlan
from custodio_source import load_server_rules
from custodio_core import RulesUnavailable
from custodio_reports import SETTING_KEY, _get_safe_existing, publish_literal_observation, unlink_deleted_original, compatible_evidence_access


def protected(member) -> bool:
    """Propietario y personal autorizado se excluyen antes de analizar contenido."""
    guild = member.guild
    permissions = getattr(member, "guild_permissions", None)
    return bool(member.id == guild.owner_id or getattr(member, "bot", False)
                or permissions is None or any(getattr(permissions, name, False)
                   for name in ("administrator", "manage_guild", "manage_messages",
                                "moderate_members", "kick_members", "ban_members")))


class CustodioRuntime:
    def __init__(self, namespace, *, clock=time.monotonic, loader=load_server_rules,
                 publisher=publish_literal_observation):
        self.n = namespace
        self.clock, self.loader, self.publisher = clock, loader, publisher
        self.detector = LocalDetector()
        self.snapshots = OrderedDict()
        self.recent = OrderedDict()
        self.locks = {}
        self.image_lock = asyncio.Semaphore(1)
        self.policy_versions = OrderedDict()
        self.plans = OrderedDict()

    def raw_policy(self, guild_id):
        return self.n["guild_config_get"](guild_id, KEY)

    def prepared(self, guild_id):
        try:
            raw = self.raw_policy(guild_id)
            return bool(type(raw) is str and len(raw) <= 16384 and json.loads(raw).get("enabled") is True)
        except (TypeError, ValueError, AttributeError):
            return False

    async def snapshot(self, guild_id, *, fresh=False):
        now = self.clock()
        cached = self.snapshots.get(guild_id)
        if not fresh and cached and now - cached[0] < 30:
            if cached[1] is None:
                raise RulesUnavailable("source_backoff")
            return cached[1]
        lock = self.locks.setdefault(guild_id, asyncio.Lock())
        async with lock:
            cached = self.snapshots.get(guild_id)
            if not fresh and cached and self.clock() - cached[0] < 30:
                if cached[1] is None:
                    raise RulesUnavailable("source_backoff")
                return cached[1]
            try:
                value = await self.loader(guild_id, os.environ.get("DISCORD_TOKEN", ""))
            except Exception:
                self.snapshots[guild_id] = (self.clock(), None)
                while len(self.snapshots) > 32:
                    self.snapshots.popitem(last=False)
                raise
            self.snapshots[guild_id] = (self.clock(), value)
            while len(self.snapshots) > 32:
                self.snapshots.popitem(last=False)
            return value

    def cleanup(self):
        now = self.clock()
        self.detector.expire(now)
        self.snapshots = OrderedDict((gid, item) for gid, item in self.snapshots.items() if now - item[0] < 30)
        self.recent = OrderedDict((key, at) for key, at in self.recent.items() if now - at < 90)
        self.locks = {gid: lock for gid, lock in self.locks.items() if lock.locked() or gid in self.snapshots}

    def honeypot(self, guild_id, channel_id):
        with closing(self.n["db_connect"]()) as db:
            return db.execute("SELECT 1 FROM guild_honeypot_channels WHERE guild_id=? AND channel_id=? LIMIT 1",
                              (guild_id, channel_id)).fetchone() is not None

    @_i18n_context
    async def process(self, message):
        guild = message.guild
        if (guild is None or message.webhook_id
                or not isinstance(message.author, discord.Member) or protected(message.author)
                or not isinstance(message.channel, discord.TextChannel)):
            return None
        if not await asyncio.to_thread(self.prepared, guild.id):
            return None
        channel = message.channel
        if guild.me is None or not self.n["bot"].intents.message_content:
            return None
        permissions = channel.permissions_for(guild.me)
        if not permissions.view_channel or not permissions.read_message_history:
            return None
        if await asyncio.to_thread(self.honeypot, guild.id, channel.id):
            return None
        snapshot = await self.snapshot(guild.id)
        raw = await asyncio.to_thread(self.raw_policy, guild.id)
        plan_raw = await asyncio.to_thread(self.n['guild_config_get'],guild.id,PLAN_KEY)
        version = (raw,plan_raw,snapshot.revision)
        if self.policy_versions.get(guild.id) != version:
            self.detector.clear_guild(guild.id)
            self.policy_versions[guild.id] = version
            while len(self.policy_versions) > 32:
                self.policy_versions.popitem(last=False)
        policy = ObservePolicy.decode(raw, snapshot)
        cached = self.plans.get(guild.id)
        if not cached or cached[0] != (plan_raw,snapshot.revision):
            plan = InterpretationPlan.decode(plan_raw,snapshot)
            self.plans[guild.id] = ((plan_raw,snapshot.revision),plan)
            self.plans.move_to_end(guild.id)
            while len(self.plans)>32:
                self.plans.popitem(last=False)
        else:
            plan = cached[1]
        if not plan or not plan.approved_by:
            return None
        roles = {role.id for role in message.author.roles}
        if not policy.eligible(role_ids=roles, channel_id=channel.id):
            return None
        from dataclasses import replace
        bindings = tuple(replace(binding,kinds=binding.kinds & plan.rules[binding.number-1].kinds)
            for binding in policy.allowed_bindings(role_ids=roles, channel_id=channel.id)
            if plan.rules[binding.number-1].eligible(channel.id,roles))
        kinds = frozenset(kind for binding in bindings for kind in binding.kinds)
        if not kinds:
            return None
        destination = await asyncio.to_thread(self.n["guild_config_get"], guild.id, SETTING_KEY)
        if not destination or not destination.isdecimal():
            return None
        report_channel = _get_safe_existing(guild, int(destination))
        if not compatible_evidence_access(channel, report_channel):
            return None
        images = []
        if kinds & {"images", "similar_images"}:
            for attachment in message.attachments[:4]:
                if (0 < attachment.size <= 1024 * 1024
                        and (attachment.content_type or "").startswith("image/")):
                    async with self.image_lock:
                        data = await attachment.read(use_cached=False)
                        if len(data) == attachment.size and len(data) <= 1024 * 1024:
                            images.append(await asyncio.to_thread(image_fingerprint, data))
        sensitivity = await asyncio.to_thread(self.n["guild_config_get"], guild.id, "custodio_sensitivity")
        detections = []
        for binding in bindings:
            for detection in self.detector.inspect(
                guild_id=guild.id, channel_id=channel.id, actor_id=message.author.id,
                message_id=message.id, now=self.clock(), content=message.content,
                kinds=binding.kinds, images=tuple(images), rule_number=binding.number,
                mention_count=len({m.id for m in message.mentions}) + len({r.id for r in message.role_mentions})
                              + (8 if message.mention_everyone else 0),
                # Las menciones automáticas de una respuesta no son pings explícitos.
                mention_ids=tuple({m.id for m in message.mentions
                    if f'<@{m.id}>' in message.content or f'<@!{m.id}>' in message.content})[:100],
                sticker_ids=tuple(s.id for s in getattr(message,'stickers',()))[:3],
                attachment_count=min(10,len(message.attachments)),
                sensitivity=sensitivity or "balanced",
            ):
                detections.append((binding, detection))
        for binding, detection in detections:
            key = (guild.id, message.author.id, binding.number)
            if key in self.recent and self.clock() - self.recent[key] < 90:
                continue
            # Revalidar la revisión y la autorización DESPUÉS del IO, antes del envío.
            fresh = await self.snapshot(guild.id, fresh=True)
            current_policy = await asyncio.to_thread(self.raw_policy, guild.id)
            if (fresh.revision != snapshot.revision or raw != current_policy
                    or plan_raw != await asyncio.to_thread(self.n['guild_config_get'],guild.id,PLAN_KEY)
                    or protected(message.author)):
                return None
            async def authorized():
                # Revalidar antes de CADA envío, incluso las partes de una evidencia.
                current_roles = {role.id for role in message.author.roles}
                permission = channel.permissions_for(guild.me) if guild.me else None
                return bool(not protected(message.author) and permission
                    and permission.view_channel and permission.read_message_history
                    and policy.eligible(role_ids=current_roles,channel_id=channel.id)
                    and plan.rules[binding.number-1].eligible(channel.id,current_roles)
                    and not binding.roles.intersection(current_roles)
                    and channel.id not in binding.channels
                    and raw == await asyncio.to_thread(self.raw_policy,guild.id)
                    and plan_raw == await asyncio.to_thread(self.n['guild_config_get'],guild.id,PLAN_KEY)
                    and destination == await asyncio.to_thread(self.n['guild_config_get'],guild.id,SETTING_KEY))
            self.recent[key] = self.clock()
            while len(self.recent) > 2048:
                self.recent.popitem(last=False)
            description = str(_t("text.custodio.image_observation", hashes=", ".join(h for h, _ in images))) if images else None
            from custodio_review import report_review_view
            report = await self.publisher(
                guild=guild, report_channel_id=int(destination), source_message=message,
                rule_text=fresh.rules[binding.number - 1], rule_number=binding.number,
                rules_revision=fresh.revision,
                authorization_check=authorized,
                review_view=report_review_view(message.id),
                footer=self.n["LAB_FOOTER_TEXT"],
                icon_url=str(guild.icon.url) if guild.icon else None,
                observed_description=description,
                conduct=str(_t("text.custodio.observation_conduct", kind=str(_t(KIND_KEYS[detection.kind])),
                               count=detection.occurrences)),
            )
            return report
        return None

    @_i18n_context
    async def deleted(self, payload):
        if payload.guild_id is None:
            return
        guild = self.n["bot"].get_guild(payload.guild_id)
        if guild is None:
            return
        raw = self.n["guild_config_get"](guild.id, SETTING_KEY)
        if raw and raw.isdecimal():
            await unlink_deleted_original(guild=guild, deleted_message_id=payload.message_id,
                                          report_channel_id=int(raw))

    async def reconcile(self):
        """Recuperación limitada por índices; no se exploran historiales de mensajes."""
        import sqlite3
        from custodio_evidence_index import prepare_index, save_reference
        from types import SimpleNamespace
        for guild in self.n["bot"].guilds:
            if not self.n["guild_config_get"](guild.id, SETTING_KEY):
                continue
            prefix = f"custodio-report:{guild.id}:"
            def recent_receipts():
                with closing(self.n["db_connect"]()) as db:
                    try:
                        return db.execute("SELECT receipts FROM evidence_archive_v1 WHERE evidence_key>=? AND evidence_key<? "
                                          "ORDER BY evidence_key DESC LIMIT 32", (prefix, prefix + "~")).fetchall()
                    except sqlite3.OperationalError:
                        return []
            rows = await asyncio.to_thread(recent_receipts)
            for row in rows:
                receipts = json.loads(row[0])
                if not receipts:
                    continue
                metadata = receipts[0]
                if metadata.get("guild_id") != guild.id:
                    continue
                source = guild.get_channel(metadata["source_channel_id"])
                if source is None:
                    continue
                await asyncio.to_thread(prepare_index, self.n["DB_PATH"])
                await asyncio.to_thread(save_reference, self.n["DB_PATH"], guild.id,
                                        metadata["source_message_id"], metadata["message_id"])
                try:
                    await source.fetch_message(metadata["source_message_id"])
                except discord.NotFound:
                    await self.deleted(SimpleNamespace(guild_id=guild.id, message_id=metadata["source_message_id"]))
                except discord.HTTPException:
                    continue


def install(namespace):
    bot = namespace["bot"]
    engine = CustodioRuntime(namespace)

    @bot.listen("on_interaction")
    async def custodio_review_interaction(interaction):
        from custodio_review import dispatch
        await dispatch(namespace, interaction)

    @bot.listen("on_message")
    async def custodio_observe_message(message):
        try:
            await engine.process(message)
        except Exception as exc:
            # No registrar contenido, tokens, nombres ni identificadores privados.
            print(f"CUSTODIO status=PAUSED exception={type(exc).__name__}")

    @bot.listen("on_raw_message_delete")
    async def custodio_evidence_deleted(payload):
        try:
            await engine.deleted(payload)
        except Exception as exc:
            print(f"CUSTODIO evidence=REVIEW exception={type(exc).__name__}")

    @bot.listen("on_raw_bulk_message_delete")
    async def custodio_evidence_bulk_deleted(payload):
        from types import SimpleNamespace
        for message_id in payload.message_ids:
            await custodio_evidence_deleted(SimpleNamespace(guild_id=payload.guild_id, message_id=message_id))

    @bot.listen("on_guild_update")
    async def custodio_guild_changed(before, after):
        engine.snapshots.pop(after.id, None)

    @tasks.loop(seconds=30)
    async def custodio_cleanup():
        engine.cleanup()

    @bot.listen("on_ready")
    async def custodio_ready():
        if not custodio_cleanup.is_running():
            custodio_cleanup.start()
        if getattr(engine, "reconcile_task", None) is None or engine.reconcile_task.done():
            async def recover():
                try:
                    await engine.reconcile()
                except Exception as exc:
                    print(f"CUSTODIO recovery=REVIEW exception={type(exc).__name__}")
            engine.reconcile_task = asyncio.create_task(recover())

    return engine
