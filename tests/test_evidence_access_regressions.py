"""Regresiones estáticas para los controles de archivado y restauración.

Estas comprobaciones no sustituyen pruebas interactivas en Discord.
"""
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1].joinpath("bot.py").read_text(encoding="utf-8")


class EvidenceAndRoleSafetyTests(unittest.TestCase):
    def test_evidence_archive_rejects_non_admin_role_access(self):
        start = SOURCE.index("async def condemnation_archive_evidence(")
        end = SOURCE.index("\nasync def ", start + 1)
        body = SOURCE[start:end]
        self.assertIn("for role in guild.roles:", body)
        self.assertIn("archive_channel.permissions_for(role).view_channel", body)
        self.assertIn("return None, None", body)

    def test_evidence_archive_rejects_member_overrides(self):
        start = SOURCE.index("async def condemnation_archive_evidence(")
        end = SOURCE.index("\nasync def ", start + 1)
        body = SOURCE[start:end]
        self.assertIn("archive_channel.overwrites.items()", body)
        self.assertIn("overwrite.view_channel is True", body)

    def test_partial_restoration_keeps_role_identifiers_for_private_log(self):
        start = SOURCE.index("async def _release_condemned_member_inner(")
        end = SOURCE.index("\nasync def ", start + 1)
        body = SOURCE[start:end]
        self.assertIn("missing_role_ids.append(rid)", body)
        self.assertIn("Roles sin restaurar (IDs):", body)


if __name__ == "__main__":
    unittest.main()
