"""Pruebas del panel de Custodio: borradores y configuración no destructiva."""
import ast
from pathlib import Path
import unittest

from custodio_preferences import (
    DEFAULTS, KEY_SENSITIVITY, KEY_ENABLED, KEY_MODE, KEY_SCOPE, KEY_NOTIFY,
    CustodioPreferences, load_preferences, validate_settings,
)
from custodio_setup import CustodioSetupView, CustodioConfirmView


class CustodioPreferencesTests(unittest.TestCase):
    def test_defaults_are_observe_balanced_eligible_no_alerts(self):
        self.assertEqual(DEFAULTS, {
            KEY_MODE: "observe",
            KEY_SENSITIVITY: "balanced",
            KEY_SCOPE: "eligible",
            KEY_NOTIFY: "0",
            KEY_ENABLED: "0",
        })

    def test_settings_are_isolated_per_guild(self):
        values = {(1, KEY_SENSITIVITY): "strict", (2, KEY_SENSITIVITY): "conservative"}
        getter = lambda guild, key: values.get((guild, key))
        self.assertEqual(load_preferences(getter, 1).sensitivity, "strict")
        self.assertEqual(load_preferences(getter, 2).sensitivity, "conservative")

    def test_cannot_enable_actions_through_preferences(self):
        for key, value in (
            (KEY_MODE, "automatic"), (KEY_MODE, "assist"),
            (KEY_SCOPE, "unrestricted"), (KEY_NOTIFY, "1"), (KEY_ENABLED, "1"),
        ):
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_settings({**DEFAULTS, key: value})

    def test_unknown_setting_is_not_given_privileges(self):
        getter = lambda guild, key: "automatic" if key == KEY_MODE else None
        self.assertEqual(load_preferences(getter, 2).mode, "observe")


class CustodioSetupTests(unittest.TestCase):
    def setUp(self):
        self.db = {}
        self.calls = []
        self.getter = lambda guild, key: self.db.get((guild, key))

        def save_atomic(guild_id, old, new):
            self.calls.append((guild_id, old.copy(), new.copy()))
            if any(self.getter(guild_id, key) != value for key, value in old.items()):
                return False
            for key, value in new.items():
                self.db[(guild_id, key)] = value
            return True

        self.save_atomic = save_atomic
        self.access = lambda *args: True

    def make_view(self, guild=123, user=456):
        return CustodioSetupView(
            guild, user, get_setting=self.getter,
            save_atomic=self.save_atomic,
            access_check=self.access,
            parent_factory=lambda: CustodioSetupView(
                guild, user, get_setting=self.getter, save_atomic=self.save_atomic,
                access_check=self.access, parent_factory=lambda: None,
            ),
        )

    def test_opening_view_does_not_write_configuration(self):
        view = self.make_view()
        self.assertIn("Observar", view.summary())
        self.assertIn("Equilibrada", view.summary())
        self.assertIn("Canales elegibles", view.summary())
        self.assertIn("Desactivados", view.summary())
        self.assertIn("No activada", view.summary())
        self.assertEqual(self.db, {})
        self.assertEqual(self.calls, [])
        self.assertIn("Modo Custodio", view.summary())
        self.assertEqual(next(x.label for x in view.children if getattr(x, "label", None) == "Crear canal de reportes"), "Crear canal de reportes")
        self.assertEqual(len(view.children), 6)
        self.assertEqual([x.row for x in view.children], [0, 1, 1, 2, 2, 2])

    def test_confirmation_only_prepares_observing_preferences(self):
        view = self.make_view()
        proposed = view._raw_changes()
        self.assertEqual(proposed, DEFAULTS)
        confirmation = CustodioConfirmView(view, proposed, {key: None for key in DEFAULTS})
        self.assertEqual(confirmation.changes, DEFAULTS)
        self.assertEqual(self.db, {})
        self.assertEqual(self.calls, [])

    def test_draft_sensitivity_is_not_persisted_until_save(self):
        view = self.make_view()
        view.pending_sensitivity = "strict"
        view._sync_controls()
        self.assertEqual(view._raw_changes()[KEY_SENSITIVITY], "strict")
        self.assertEqual(self.db, {})
        self.assertEqual(self.calls, [])

    def test_cas_detects_conflicting_configuration(self):
        view = self.make_view()
        old = {key: self.getter(123, key) for key in DEFAULTS}
        updated = view._raw_changes()
        self.db[(123, KEY_SENSITIVITY)] = "strict"
        self.assertFalse(self.save_atomic(123, old, updated))
        self.assertEqual(self.db[(123, KEY_SENSITIVITY)], "strict")

    def test_automod_entry_is_present_and_back_not_to_setup_home(self):
        source = Path(__file__).resolve().parents[1].joinpath("bot.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        cls = next(c for c in tree.body if isinstance(c, ast.ClassDef)
                   and c.name == "HeraldoAutomodSetupView")
        methods = {n.name: n for n in cls.body if isinstance(n, ast.AsyncFunctionDef)}
        self.assertIn("modo_custodio", methods)
        body = ast.get_source_segment(source, methods["modo_custodio"])
        self.assertIn("CustodioSetupView(", body)
        self.assertIn("parent_factory=lambda: HeraldoAutomodSetupView", body)
        self.assertNotIn("guild_config_set(", body)
        self.assertNotIn("kick(", body)
        self.assertNotIn("ban(", body)


if __name__ == "__main__":
    unittest.main()
