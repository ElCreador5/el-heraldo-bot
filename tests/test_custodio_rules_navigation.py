"""Regresión del subpanel de Server Rules, sin Gateway ni inferencia."""
from i18n_source_helpers import source_text as _source_text
import ast
from pathlib import Path
import unittest
import os
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock,Mock,patch
import discord

SOURCE = _source_text(Path(__file__).resolve().parents[1] / 'custodio_setup.py', 'utf-8')
TREE = ast.parse(SOURCE)


class CustodioRulesNavigationTests(unittest.IsolatedAsyncioTestCase):
    def test_manual_rules_reader_only(self):
        cls = next(n for n in TREE.body if isinstance(n, ast.ClassDef) and n.name == "CustodioSetupView")
        constructor = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
        self.assertFalse(any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "load_server_rules"
            for n in ast.walk(constructor)
        ))
        self.assertIn('label="Reglas del servidor"', SOURCE)

    async def test_subpanel_disallows_unconfigured_ai(self):
        from custodio_setup import CustodioRulesView
        from test_custodio_runtime_integration import SNAPSHOT
        import custodio_rule_analysis as analysis
        analysis._cache.clear();analysis._busy.clear()
        parent=NS(guild_id=101,owner_id=303,get_setting=lambda gid,key:None,
                  access_check=AsyncMock(return_value=True),observation_editors={},save_atomic=Mock())
        interaction=NS(user=NS(id=303,guild_permissions=discord.Permissions(administrator=True)),
            guild=NS(id=101,owner_id=999,text_channels=[],roles=[]),
            response=NS(defer=AsyncMock()),edit_original_response=AsyncMock())
        view=CustodioRulesView(parent,SNAPSHOT)
        with patch.dict(os.environ,{},clear=True),patch('aiohttp.ClientSession') as transport,\
             patch('custodio_detection_setup.load_server_rules',new=AsyncMock(return_value=SNAPSHOT)),\
             patch.object(analysis,'BUDGET',NS(take=AsyncMock())):
            await view.analyze_rules.callback(interaction)
        transport.assert_not_called();parent.save_atomic.assert_not_called()
        self.assertEqual(parent.observation_editors[False].pending.rules[0].status,'unavailable')

    def test_subpanel_back_navigation(self):
        self.assertIn("view=self.parent, embed=None", SOURCE)

    def test_snapshot_is_not_saved_or_approved(self):
        cls = next(n for n in TREE.body if isinstance(n, ast.ClassDef) and n.name == "CustodioRulesView")
        methods = {n.name: n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.assertTrue({"__init__", "interaction_check", "summary", "analyze_rules", "back",
                         "choose_rule", "fragments", "previous", "next", "sync"}.issubset(methods))
        self.assertNotIn("set_setting(", ast.get_source_segment(SOURCE, cls))


if __name__ == "__main__":
    unittest.main()
