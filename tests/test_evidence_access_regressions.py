"""Regresiones estáticas para los controles de archivado y restauración.

Estas comprobaciones no sustituyen pruebas interactivas en Discord.
"""
from pathlib import Path
import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, MagicMock, patch
from test_safety_regressions import b

SOURCE = Path(__file__).resolve().parents[1].joinpath("bot.py").read_text(encoding="utf-8")

ARCHIVE_SOURCE = Path(b.evidence_archive.__file__).read_text(encoding="utf-8")

class EvidenceAndRoleSafetyTests(unittest.TestCase):
    def test_evidence_archive_rejects_non_admin_role_access(self):
        start = ARCHIVE_SOURCE.index("def private_channel(")
        end = ARCHIVE_SOURCE.index("\ndef snapshot", start + 1)
        body = ARCHIVE_SOURCE[start:end]
        self.assertIn("for role in guild.roles:", body)
        self.assertIn("channel.permissions_for(role).view_channel", body)
        self.assertIn("return False", body)

    def test_evidence_archive_rejects_member_overrides(self):
        start = ARCHIVE_SOURCE.index("def private_channel(")
        end = ARCHIVE_SOURCE.index("\ndef snapshot", start + 1)
        body = ARCHIVE_SOURCE[start:end]
        self.assertIn("channel.overwrites.items()", body)
        self.assertIn("overwrite.view_channel is True", body)

    def test_partial_restoration_keeps_role_identifiers_for_private_log(self):
        start = SOURCE.index("async def _release_condemned_member_inner(")
        end = SOURCE.index("\nasync def ", start + 1)
        body = SOURCE[start:end]
        self.assertIn("missing_role_ids.append(rid)", body)
        self.assertIn("Roles sin restaurar (IDs):", body)


class EvidenceRuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_condemnation_uses_same_verified_archive_and_contract(self):
        message = NS(author=NS(id=11), content='Texto de prueba')
        guild, member = NS(id=901, get_channel=lambda _: NS()), NS(id=11)
        with patch.object(b, 'condemnation_fetch_source_message', new=AsyncMock(return_value=message)), \
                patch.object(b.evidence_archive, 'private_channel', return_value=True), \
                patch.object(b.evidence_archive, 'preserve', new=AsyncMock(return_value='private-reference')) as preserve, \
                patch.object(type(b.bot), 'intents', new_callable=lambda: property(lambda _: NS(message_content=True))):
            result = await b.condemnation_archive_evidence(guild, member,
                source_message_url='reference', reason='Prueba', applied_by=None)
        self.assertEqual(result, ('private-reference', 'Texto de prueba'))
        preserve.assert_awaited_once()

    async def test_other_author_never_archived_as_case_evidence(self):
        with patch.object(b, 'condemnation_fetch_source_message', new=AsyncMock(return_value=NS(author=NS(id=12)))), \
                patch.object(b.evidence_archive, 'preserve', new=AsyncMock()) as preserve:
            self.assertEqual(await b.condemnation_archive_evidence(NS(), NS(id=11),
                source_message_url='reference', reason='Prueba', applied_by=None), (None, None))
        preserve.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
