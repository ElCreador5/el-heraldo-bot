"""Contrato de recuperación oficial: DM previo y título/servidor configurables."""
from __future__ import annotations
from i18n_source_helpers import source_text as _source_text
import ast
import re
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
SOURCE=_source_text(Path(__file__).resolve().parents[1] / 'bot.py', encoding='utf-8')
TREE=ast.parse(SOURCE)

class PersonalityRecoveryTests(unittest.TestCase):
    def test_dm_template_explains_planned_not_completed_action(self):
        fragment=SOURCE.split("DM_TEXT = (",1)[1].split("# En Railway",1)[0]
        self.assertIn("está prevista tu expulsión",fragment)
        self.assertIn("{servidor}",fragment)
        self.assertIn("{titulo_embed}",fragment)
        self.assertIn("{invitacion}",fragment)
        self.assertNotIn("Fuiste expulsado",fragment)

    def test_recovery_template_resolves_real_server_and_panel(self):
        nodes=[n for n in TREE.body if isinstance(n,ast.FunctionDef)
               and n.name=="render_personality_recovery_dm"]
        self.assertEqual(len(nodes),1)
        mod=ast.Module(body=[ast.ImportFrom(module="__future__",
                        names=[ast.alias(name="annotations")],level=0),nodes[0]],type_ignores=[])
        ctx={"guild_config_get":lambda *_:None, "DM_TEXT":"{servidor} / {titulo_embed} / {razon} / {invitacion} / {literal}",
             "get_orientation_embed_title":lambda *_:"Mi personalidad",
             "re":re,"discord":NS(utils=NS(escape_mentions=lambda s:s))}
        exec(compile(ast.fix_missing_locations(mod),"bot.py","exec"),ctx)
        guild=NS(id=5,name="Comunidad")
        self.assertEqual(ctx["render_personality_recovery_dm"](guild,"discord.gg/example"),
            "Comunidad / Mi personalidad / No definió su personalidad / discord.gg/example / {literal}")

    def test_expulsion_success_is_never_claimed_when_kick_fails(self):
        source=ast.get_source_segment(SOURCE,next(n for n in TREE.body if isinstance(n,ast.AsyncFunctionDef) and n.name=="expel"))
        self.assertLess(source.index("await send_recovery_dm("),source.index("await heraldo_kick("))
        self.assertIn("if not kicked:",source)
        self.assertIn("Advertencia: Expulsión no completada",source)

if __name__=="__main__":unittest.main()
