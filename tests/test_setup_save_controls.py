"""Guardar cambios permanece deshabilitado hasta detectar un cambio real."""
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace as NS

from setup_save_controls import refresh_save_button, has_unsaved_changes


def panel(name, **fields):
    cls = type(name, (), {})
    view = cls()
    view.children = [NS(label="Guardar cambios", disabled=False),
                     NS(label="Confirmar cambios", disabled=False),
                     NS(label="Activar", disabled=False)]
    for key, value in fields.items():
        setattr(view, key, value)
    return view


class SaveControlsTests(unittest.TestCase):
    def assert_state(self, view, pending):
        result = refresh_save_button(view)
        self.assertEqual(result, pending)
        self.assertEqual(view.children[0].disabled, not pending)
        self.assertFalse(view.children[1].disabled)
        self.assertFalse(view.children[2].disabled)

    def test_no_pending_on_main_setup_panels(self):
        cases = {
            "HeraldoChannelSetupView": dict(pending_channels={}),
            "HeraldoRoleSetupView": dict(pending_roles={}),
            "HeraldoJoinRolesBasicView": dict(pending_role_ids=None,
                pending_screening=None, pending_enabled=None, pending_delay=None),
            "HeraldoJoinRolesUsersView": dict(pending_remove_after=None),
            "HeraldoJoinRolesBotsView": dict(pending_role_ids=None,
                pending_enabled=None, pending_delay=None, pending_different=None),
            "HeraldoJoinRolesSyncView": dict(pending_excluded=None),
            "HeraldoOrientationSetupView": dict(pending_channel_id=None,
                pending_bindings=None, pending_enabled=None,
                pending_required=None, pending_allow_change=None,
                pending_dm_template=None),
            "HeraldoMotwSetupView": dict(pending_channel_id=None, original_channel_id=123),
            "HeraldoHoneypotSetupView": dict(pending_trap_id=None, pending_enabled=None,
                pending_paused=None, pending_action=None, pending_kick_purge_minutes=None,
                pending_ban_minutes=None, pending_timeout_minutes=None, pending_purge_spec=None),
            "HeraldoVerificationSetupView": dict(pending_role_id=None,
                pending_sin_role_id=None, pending_channel_id=None, pending_enabled=None),
            "HeraldoRaidSetupView": dict(pending_action=None,
                pending_role_id=None, pending_enabled=None,
                pending_invites=None, pending_purge=None),
            "EmbedEditorView": dict(pending_timestamp=None, pending_remove_index=None),
        }
        for name, fields in cases.items():
            with self.subTest(name=name):
                view = panel(name, **fields)
                self.assert_state(view, False)
                key = next(iter(fields))
                if isinstance(fields[key], dict):
                    fields[key] = {"test": 8}
                else:
                    fields[key] = 8
                # No modifica el servidor: solo el borrador.
                setattr(view, key, fields[key])
                self.assert_state(view, True)
                if isinstance(fields[key], dict):
                    setattr(view, key, {})
                else:
                    setattr(view, key, None)
                self.assert_state(view, False)

    def test_existing_value_does_not_count_as_change(self):
        view = panel("HeraldoMotwSetupView",
                     pending_channel_id=123, original_channel_id=123)
        self.assert_state(view, False)
        view.pending_channel_id = 456
        self.assert_state(view, True)
        view.pending_channel_id = 123
        self.assert_state(view, False)

    def test_template_publication_fields_do_not_activate_save(self):
        view = panel("TemplateEditorView", original_template=None,
                     name="", text="", embed=None, extra_embeds=[],
                     channel_id=998, role_id=1234, dirty=True)
        self.assert_state(view, False)
        view.name = "Aviso"
        self.assert_state(view, True)
        view.name = ""
        self.assert_state(view, False)

    def test_template_existing_uses_persisted_snapshot(self):
        view = panel("TemplateEditorView", original_template={"name": "Aviso"},
                     name="Aviso", text="Sin cambios", embed=None,
                     extra_embeds=[], dirty=False)
        view._is_saved = lambda: view.text == "Sin cambios"
        self.assert_state(view, False)
        view.text = "Texto nuevo"
        self.assert_state(view, True)
        view.text = "Sin cambios"
        self.assert_state(view, False)

    def test_autofeed_existing_values_and_reversions(self):
        old = dict(channel=42, role=None, text="Aviso", embed=None,
                   start="2026-10-30T17:00:00+00:00", repeat="custom",
                   repeat_parts={"days": 2})
        view = panel("AutofeedEditorView", original=old,
                     channel_id=42, role_id=None, text="Aviso", embed=None,
                     start=datetime(2026, 10, 30, 17, tzinfo=timezone.utc),
                     parts={"days": 2}, dirty=False)
        self.assert_state(view, False)
        view.role_id = 999
        self.assert_state(view, True)
        view.role_id = None
        self.assert_state(view, False)

    def test_unknown_and_confirmations_are_never_disabled(self):
        unknown = panel("DraftConfirm")
        self.assertIsNone(refresh_save_button(unknown))
        self.assertFalse(unknown.children[0].disabled)
        self.assertFalse(unknown.children[1].disabled)

    def test_report_reminders_and_user_reports_reuse_existing_detection(self):
        for kind in ("ReportReminderSetupView", "HeraldoUserReportsSetupView"):
            view = panel(kind)
            view._has_pending_changes = lambda: False
            self.assert_state(view, False)
            view._has_pending_changes = lambda: True
            self.assert_state(view, True)
            view._has_pending_changes = lambda: False
            self.assert_state(view, False)

    def test_honeypot_subpanel_uses_parent_draft(self):
        parent = NS(pending_trap_id=None, pending_enabled=None,
            pending_paused=None, pending_action=None, pending_kick_purge_minutes=None,
            pending_ban_minutes=None, pending_timeout_minutes=None,
            pending_purge_spec=None)
        subpanel = panel("HeraldoHoneypotDraftSubView", parent=parent)
        self.assert_state(subpanel, False)
        parent.pending_action = "kick"
        self.assert_state(subpanel, True)
        parent.pending_action = None
        self.assert_state(subpanel, False)


if __name__ == "__main__":
    unittest.main()
