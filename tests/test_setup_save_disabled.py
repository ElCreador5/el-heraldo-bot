"""Regresión del estado de Guardar cambios en los paneles de /setup.

El bot no se importa: se comprueban las vistas y se ejecuta únicamente la
lógica de borradores con dobles de Discord para evitar iniciar el cliente.
"""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest


SOURCE = ast.parse((Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8"))


def definition(name):
    return next(node for node in SOURCE.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name)


class StubView:
    def to_components(self):
        return self.children


class StubButton:
    def __init__(self, name, label="Guardar cambios"):
        self.callback = SimpleNamespace(__name__=name)
        self.label = label
        self.disabled = False


def sandbox(**extra):
    ns = {
        "discord": SimpleNamespace(ui=SimpleNamespace(View=StubView, Button=StubButton)),
        "_t": lambda key: "Guardar cambios" if key == "text.14bdfaf2face3a" else key,
        **extra,
    }
    subset = ast.fix_missing_locations(ast.Module(body=[
        definition("_setup_has_unsaved_changes"), definition("_SetupDirtySaveView")
    ], type_ignores=[]))
    exec(compile(subset, "bot.py", "exec"), ns)
    return ns


def view(ns, classname, **fields):
    cls = type(classname, (ns["_SetupDirtySaveView"],), {})
    instance = cls()
    instance.children = [StubButton("save_changes"), StubButton("toggle", "Activar")]
    for key, value in fields.items():
        setattr(instance, key, value)
    return instance


class TestSetupSaveDisabled(unittest.TestCase):
    def test_all_setup_panels_with_save_button_use_shared_control(self):
        names = (
            "HeraldoChannelSetupView", "HeraldoRoleSetupView",
            "_JoinRolesOwnedView", "HeraldoOrientationSetupView",
            "HeraldoMotwSetupView", "HeraldoHoneypotSetupView",
            "HeraldoHoneypotSubView", "HeraldoVerificationSetupView",
            "HeraldoRaidDetectionView", "HeraldoRaidSetupView",
            "ReportReminderSetupView", "HeraldoUserReportsSetupView",
            "HeraldoCondemnationSetupView", "HeraldoLoggingSetupView",
            "ExitCommentSetupView", "HeraldoMemberLogSetupView",
            "HeraldoReactionRolesEditorView", "HeraldoDateFormatSetupView",
            "HeraldoLanguageView",
        )
        for name in names:
            with self.subTest(name=name):
                bases = [node.id for node in definition(name).bases if isinstance(node, ast.Name)]
                self.assertIn("_SetupDirtySaveView", bases)

    def test_new_reverted_and_saved(self):
        ns = sandbox()
        item = view(ns, "HeraldoLanguageView", guild_id=1, original="es-419", pending="es-419")
        item.to_components()
        self.assertTrue(item.children[0].disabled)
        self.assertFalse(item.children[1].disabled)
        item.pending = "en-US"
        item.to_components()
        self.assertFalse(item.children[0].disabled)
        item.pending = "es-419"
        item.to_components()
        self.assertTrue(item.children[0].disabled)
        item.pending = "pt-BR"
        item.original = "pt-BR"
        item.to_components()
        self.assertTrue(item.children[0].disabled)

    def test_channel_same_as_saved_is_not_a_change(self):
        ns = sandbox(get_guild_channel_id=lambda guild, key: 100)
        item = view(ns, "HeraldoChannelSetupView", guild_id=4, pending_channels={})
        item.to_components()
        self.assertTrue(item.children[0].disabled)
        item.pending_channels["logs"] = 100
        item.to_components()
        self.assertTrue(item.children[0].disabled)
        item.pending_channels["logs"] = 200
        item.to_components()
        self.assertFalse(item.children[0].disabled)
        item.pending_channels.clear()
        item.to_components()
        self.assertTrue(item.children[0].disabled)

    def test_member_log_toggle_reverted_disables_save(self):
        ns = sandbox(log_member_channel_id=lambda guild, event: 33,
                     log_member_event_enabled=lambda guild, event: True)
        item = view(ns, "HeraldoMemberLogSetupView", guild_id=4,
                    event_key="member_ban", pending_channel_id=None,
                    pending_enabled=None)
        item.to_components()
        self.assertTrue(item.children[0].disabled)
        item.pending_enabled = False
        item.to_components()
        self.assertFalse(item.children[0].disabled)
        item.pending_enabled = True
        item.to_components()
        self.assertTrue(item.children[0].disabled)

    def test_custom_save_and_nested_draft(self):
        ns = sandbox(get_guild_channel_id=lambda guild, key: 9)
        item = view(ns, "HeraldoChannelSetupView", guild_id=1, pending_channels={})
        item.children[0] = StubButton("save_changes", "Guardar cambios")
        item.to_components()
        self.assertTrue(item.children[0].disabled)
        item.pending_channels["logs"] = 10
        item.to_components()
        self.assertFalse(item.children[0].disabled)


if __name__ == "__main__":
    unittest.main()
