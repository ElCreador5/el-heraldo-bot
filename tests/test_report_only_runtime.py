"""Ejecuta la acción real de reporte con configuración heredada, sin Gateway."""
import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, patch
from test_safety_regressions import b


class ReportOnlyRuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_legacy_report_cannot_purge_or_punish(self):
        target = NS(timeout=AsyncMock(), kick=AsyncMock(), ban=AsyncMock())
        with patch.object(b, 'condemnation_protection_reason', return_value=None), \
                patch.object(b, 'run_purge_job', new=AsyncMock()) as purge, \
                patch.object(b, 'condemn_member', new=AsyncMock()) as condemn:
            result = await b.execute_moderation_report_action(
                NS(id=901), target, NS(),
                {'action': 'report', 'purge_minutes': 1440}, 3)
        self.assertEqual(result, (True, 'Reporte registrado'))
        for operation in (purge, condemn, target.timeout, target.kick, target.ban):
            operation.assert_not_awaited()

    def test_normalization_removes_legacy_purge(self):
        rule = b._normalize_moderation_report_rule(
            {'action': 'report', 'emoji': 'flag', 'label': 'Reporte', 'purge_minutes': 1440})
        self.assertIsNotNone(rule)
        self.assertIsNone(rule['purge_minutes'])
