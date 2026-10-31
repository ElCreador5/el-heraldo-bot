"""Contrato de navegación sin acciones duplicadas en los paneles nativos de /setup.

Verifica que una acción tenga una única entrada dentro de cada pantalla,
sin confundir el destino del anuncio con las referencias de su embed.
No requiere Discord Gateway ni altera SQLite.
"""
import ast
from pathlib import Path
import unittest
from i18n_source_helpers import source_text


ROOT = Path(__file__).resolve().parents[1]
BOT = ast.parse(source_text(ROOT / "bot.py", encoding="utf-8"))
ANNOUNCEMENTS = ast.parse((ROOT / "autofeed_setup.py").read_text(encoding="utf-8"))
BUILDER = ast.parse((ROOT / "autofeed_embed_builder.py").read_text(encoding="utf-8"))


def find_class(module, name):
    return next(node for node in module.body
                if isinstance(node, ast.ClassDef) and node.name == name)


def find_method(node, name):
    return next(item for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                and item.name == name)


def decorated_buttons(node):
    for method in node.body:
        if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in method.decorator_list:
            if not (isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Attribute)
                    and decorator.func.attr == "button"):
                continue
            label = next((kw.value for kw in decorator.keywords if kw.arg == "label"), None)
            if label is not None:
                yield method.name, ast.dump(label, include_attributes=False)


class SetupNoOverlaps(unittest.TestCase):
    def test_module_routes_are_unique_and_messages_are_separate_from_announcements(self):
        root = find_class(BOT, "HeraldoSetupView")
        assignment = next(node for node in root.body
                          if isinstance(node, ast.Assign)
                          and any(isinstance(target, ast.Name) and target.id == "MODULES"
                                  for target in node.targets))
        keys = [entry[0] for entry in ast.literal_eval(assignment.value)]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertIn("messages", keys)
        self.assertIn("autofeeds", keys)

        messages = find_method(find_class(BOT, "HeraldoMessagesSetupView"), "__init__")
        values = [kw.value.value for node in ast.walk(messages)
                  if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                  and node.func.attr == "SelectOption"
                  for kw in node.keywords
                  if kw.arg == "value" and isinstance(kw.value, ast.Constant)]
        self.assertEqual(len(values), len(set(values)))
        self.assertTrue({"verification", "verify_dm", "suggestions",
                         "honeypot", "condemnation", "logs"}.issubset(values))
        self.assertTrue({"autofeeds", "templates", "create_message"}.isdisjoint(values))

    def test_no_duplicate_static_button_labels_inside_each_setup_panel(self):
        for module, names in (
            (BOT, ("HeraldoAutomodSetupView", "HeraldoModerationSetupView",
                   "HeraldoVerificationHubView", "HeraldoJoinRolesSetupView",
                   "HeraldoVerificationSetupView", "HeraldoOrientationSetupView",
                   "HeraldoHoneypotSetupView", "HeraldoRaidSetupView",
                   "HeraldoLoggingSetupView", "HeraldoMemberLogSetupView",
                   "HeraldoUserReportsSetupView", "HeraldoMessagesSetupView")),
            (ANNOUNCEMENTS, ("AutofeedEditorView",)),
            (BUILDER, ("EmbedBuilderView",)),
        ):
            for name in names:
                with self.subTest(panel=name):
                    labels = [label for _, label in decorated_buttons(find_class(module, name))]
                    self.assertEqual(len(labels), len(set(labels)))

    def test_verification_texts_are_edited_only_in_messages(self):
        # Mensajes -> Verificación ofrece el editor de texto y vista previa.
        age = find_class(BOT, "HeraldoVerificationSetupView")
        self.assertNotIn("texts", {name for name, _ in decorated_buttons(age)})
        studio = find_class(BOT, "DefaultMessageStudioView")
        edit = ast.unparse(find_method(studio, "edit_verification"))
        self.assertIn("VerifyTextsModal", edit)

    def test_announcement_main_panel_has_no_duplicate_embed_controls(self):
        editor = find_class(ANNOUNCEMENTS, "AutofeedEditorView")
        methods = {method for method, _ in decorated_buttons(editor)}
        self.assertTrue({"message", "embed_builder", "save", "publish_button"}.issubset(methods))
        self.assertTrue({"mention", "embed_channel", "images_button"}.isdisjoint(methods))
        init = ast.unparse(find_method(editor, "__init__"))
        self.assertIn("self.embed_builder", init)
        self.assertNotIn("self.mention,", init)
        self.assertNotIn("self.embed_channel,", init)
        self.assertNotIn("self.images_button,", init)

        builder = ast.unparse(find_method(find_class(BUILDER, "EmbedBuilderView"), "__init__"))
        self.assertIn("'media'", builder)
        self.assertIn("'author'", builder)
        self.assertIn("'fields'", builder)
        self.assertIn("discord.ui.RoleSelect", builder)
        self.assertIn("discord.ui.ChannelSelect", builder)


if __name__ == "__main__":
    unittest.main()
