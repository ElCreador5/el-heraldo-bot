"""NH UX-03B: contrato del port selectivo de /setup a main (sin Gateway)."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "tools" / "main_ux03b_candidate.py"
TARGET = CANDIDATE if CANDIDATE.exists() else ROOT / "bot.py"
SOURCE = TARGET.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE, filename=str(TARGET))

def segment(name):
    node = next(
        n for n in TREE.body
        if isinstance(n, ast.ClassDef) and n.name == name
    )
    return ast.get_source_segment(SOURCE, node)

def back(name):
    class_code = segment(name)
    return class_code.split("    async def back(", 1)[1].split("\n    @", 1)[0].split("\n    async def ", 1)[0]

class UX03BMainReleaseContract(unittest.TestCase):
    def test_source_parses(self):
        self.assertGreater(len(TREE.body), 100)

    def test_nested_back_goes_to_immediate_parent(self):
        parents = {
            "HeraldoHoneypotSetupView": "HeraldoAutomodSetupView",
            "HeraldoRaidSetupView": "HeraldoAutomodSetupView",
            "HeraldoVerificationSetupView": "HeraldoVerificationHubView",
            "HeraldoOrientationSetupView": "HeraldoVerificationHubView",
            "HeraldoJoinRolesBasicView": "HeraldoJoinRolesSetupView",
            "HeraldoJoinRolesUsersView": "HeraldoJoinRolesSetupView",
            "HeraldoJoinRolesBotsView": "HeraldoJoinRolesSetupView",
            "HeraldoJoinRolesSyncView": "HeraldoJoinRolesSetupView",
        }
        for name, parent in parents.items():
            with self.subTest(name=name):
                fn = back(name)
                self.assertIn("view=" + parent + "(", fn)
                self.assertNotIn("heraldo_setup_go_home(", fn)

    def test_only_volver_navigation_label(self):
        self.assertNotIn('label="Volver a /setup"', SOURCE)
        self.assertNotIn('label="Join Roles", style=discord.ButtonStyle.secondary', SOURCE)
        for name in ("HeraldoJoinRolesBasicView", "HeraldoJoinRolesUsersView",
                     "HeraldoJoinRolesBotsView", "HeraldoJoinRolesSyncView",
                     "HeraldoMessagesSetupView", "HeraldoModerationSetupView",
                     "HeraldoReactionRolesSetupView"):
            with self.subTest(name=name):
                self.assertIn('label="Volver"', segment(name))

    def test_roles_panel_never_overflows_a_row(self):
        role_panel = segment("HeraldoRoleSetupView")
        self.assertIn('row=3,', role_panel)  # three dynamically created roles
        for label in ("Guardar cambios", "Descartar cambios", "Volver"):
            self.assertRegex(role_panel,
                r'@discord\.ui\.button\(label="' + label
                + r'", style=discord\.ButtonStyle\.\w+, row=4\)')
        self.assertEqual(role_panel.count("@discord.ui.button("), 3)

    def test_join_roles_hub_balanced(self):
        hub = segment("HeraldoJoinRolesSetupView")
        self.assertIn('@discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary, row=1)', hub)

    def test_preserve_important_features(self):
        for name in ("HeraldoVerificationHubView", "HeraldoModerationSetupView",
                     "HeraldoLoggingSetupView", "HeraldoHoneypotSubView",
                     "HeraldoReactionRolesEditorView"):
            self.assertTrue(segment(name), name)

if __name__ == "__main__":
    unittest.main()
