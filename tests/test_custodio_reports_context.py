"""Regresiones del canal de Custodio y metadatos de evidencia (sin Discord API real)."""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, patch

import discord

from custodio_context import PUBLIC_NETWORKS, classify_community, may_collect_evidence
from custodio_reports import (
    CHANNEL_NAME, CHANNEL_TOPIC, SETTING_KEY,
    ObservationEvidence, ReportChannelError,
    create_private_report_channel, observation_embed, private_report_channel,
)


class FakeRole:
    def __init__(self, ident, *, moderator=False):
        self.id = ident
        self.permissions = SimpleNamespace(
            administrator=False, manage_guild=False,
            manage_messages=moderator, moderate_members=False,
        )


class FakeChannel:
    def __init__(self, guild, ident, overwrites, *, name=CHANNEL_NAME, topic=CHANNEL_TOPIC):
        self.guild, self.id, self.name, self.topic = guild, ident, name, topic
        self.overwrites = dict(overwrites)
        self._allowed = True

    def overwrites_for(self, role):
        return self.overwrites.get(role, discord.PermissionOverwrite())

    def permissions_for(self, member):
        return SimpleNamespace(
            view_channel=self._allowed, send_messages=self._allowed,
            embed_links=self._allowed, read_message_history=self._allowed,
        )


class FakeMember:
    def __init__(self, ident, permissions=None):
        self.id = ident
        self.guild_permissions = permissions


class FakeGuild:
    def __init__(self, guild_id=1, *, manage_channels=True):
        self.id = guild_id
        self.owner_id = 101
        self.default_role = FakeRole(guild_id)
        self.roles = [self.default_role, FakeRole(302, moderator=True), FakeRole(303)]
        bot_perms = SimpleNamespace(
            manage_channels=manage_channels, view_channel=True, send_messages=True,
            embed_links=True, read_message_history=True,
        )
        self.me = FakeMember(201, bot_perms)
        self.text_channels = []
        self.create_count = 0

    def get_channel(self, channel_id):
        return next((x for x in self.text_channels if x.id == channel_id), None)

    async def create_text_channel(self, name, *, topic, overwrites, nsfw, reason):
        self.create_count += 1
        assert nsfw is False and name == CHANNEL_NAME and topic == CHANNEL_TOPIC
        assert overwrites[self.default_role].view_channel is False
        assert self.roles[1] in overwrites and self.roles[2] not in overwrites
        c = FakeChannel(self, 9000 + self.create_count, overwrites, name=name, topic=topic)
        self.text_channels.append(c)
        return c


class ReportChannelTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.guild = FakeGuild()
        self.settings = {}
        self.get = lambda guild, key: self.settings.get((guild, key))
        self.set = lambda guild, key, value: self.settings.__setitem__((guild, key), value)
        self.patch_channel = patch("custodio_reports.discord.TextChannel", FakeChannel)
        self.patch_member = patch("custodio_reports.discord.Member", FakeMember)
        self.patch_channel.start()
        self.patch_member.start()

    def tearDown(self):
        self.patch_member.stop()
        self.patch_channel.stop()

    async def test_confirmed_creation_is_private_and_idempotent(self):
        channel, created = await create_private_report_channel(self.guild, self.get, self.set)
        self.assertTrue(created)
        self.assertEqual(self.guild.create_count, 1)
        self.assertTrue(private_report_channel(channel))
        self.assertEqual(self.get(self.guild.id, SETTING_KEY), str(channel.id))
        same, again = await create_private_report_channel(self.guild, self.get, self.set)
        self.assertFalse(again)
        self.assertEqual(same.id, channel.id)
        self.assertEqual(self.guild.create_count, 1)

    async def test_missing_bot_permissions_never_creates_channel(self):
        self.guild = FakeGuild(manage_channels=False)
        with self.assertRaises(ReportChannelError):
            await create_private_report_channel(self.guild, self.get, self.set)
        self.assertEqual(self.guild.create_count, 0)
        self.assertEqual(self.settings, {})

    async def test_channel_with_public_permissions_never_reused(self):
        channel, _ = await create_private_report_channel(self.guild, self.get, self.set)
        channel.overwrites[self.guild.default_role] = discord.PermissionOverwrite(view_channel=True)
        with self.assertRaises(ReportChannelError):
            await create_private_report_channel(self.guild, self.get, self.set)
        self.assertEqual(self.guild.create_count, 1)

    async def test_crash_between_creation_and_saving_recovers_safe_channel(self):
        class FailureOnce:
            def __init__(self):
                self.calls = 0
            def __call__(self, guild_id, key, value):
                self.calls += 1
                if self.calls == 1:
                    raise OSError("db busy")
                self_value = value
                self.settings[(guild_id, key)] = self_value
        failure = FailureOnce()
        failure.settings = self.settings
        with self.assertRaises(OSError):
            await create_private_report_channel(self.guild, self.get, failure)
        self.assertEqual(self.guild.create_count, 1)
        channel, created = await create_private_report_channel(self.guild, self.get, failure)
        self.assertFalse(created)
        self.assertEqual(channel.id, 9001)
        self.assertEqual(self.guild.create_count, 1)

    async def test_concurrent_requests_create_one_channel(self):
        import asyncio
        results = await asyncio.gather(
            create_private_report_channel(self.guild, self.get, self.set),
            create_private_report_channel(self.guild, self.get, self.set),
        )
        self.assertEqual(self.guild.create_count, 1)
        self.assertEqual(sum(created for _, created in results), 1)


class EvidenceAndContextTests(TestCase):
    def test_metadata_evidence_never_copies_raw_messages(self):
        evidence = ObservationEvidence(
            guild_id=100, channel_id=200, message_id=300,
            rule_numbers=(1, 2), rules_revision="a" * 64, category="ambiguous",
            classification="age_restricted",
            timestamp=datetime.now(timezone.utc),
            content_sha256="b" * 64,
        )
        embed = observation_embed(evidence)
        self.assertIn("https://discord.com/channels/100/200/300", embed.to_dict()["fields"][-1]["value"])
        self.assertNotIn("texto_original", str(embed.to_dict()))
        self.assertIn("No se archivó", embed.footer.text)

    def test_invalid_reference_and_digests_are_rejected(self):
        with self.assertRaises(ValueError):
            ObservationEvidence(
                guild_id=1, channel_id=2, message_id=3, rule_numbers=(1,),
                rules_revision="bad", category="suspected", classification="sfw",
                timestamp=datetime.now(timezone.utc),
            )

    def test_age_restrictions_are_context_not_rule_permission(self):
        rev = "a" * 64
        safe = classify_community(1, 2, 2, False, rev, rev)
        restricted = classify_community(1, 3, 2, True, rev, rev)
        mixed = classify_community(1, 4, 3, False, rev, rev)
        unknown = classify_community(1, 5, 0, False, rev, None)
        self.assertEqual(safe.effective_classification, "sfw")
        self.assertEqual(restricted.effective_classification, "age_restricted")
        self.assertEqual(mixed.effective_classification, "age_restricted")
        self.assertEqual(unknown.effective_classification, "unknown")
        self.assertTrue(may_collect_evidence(safe, True, False))
        self.assertFalse(may_collect_evidence(unknown, True, False))
        self.assertFalse(may_collect_evidence(safe, False, False))
        self.assertFalse(may_collect_evidence(safe, True, True))

    def test_each_social_network_disallows_unapproved_training(self):
        self.assertEqual({x["name"] for x in PUBLIC_NETWORKS}, {"Reddit", "X", "Instagram"})
        self.assertTrue(all(x["training"] == "not_authorized" for x in PUBLIC_NETWORKS))


if __name__ == "__main__":
    import unittest
    unittest.main()
