"""Dropdown choices stay visible without writing settings to SQLite.

These tests use small Discord-shaped fakes and require no Gateway connection.
"""
import sys
import types
import unittest

from button_row_layout import synchronize_dropdown_defaults


class Button:
    width = 1


class Option:
    def __init__(self, value, default=False):
        self.value = value
        self.default = default


class Select:
    width = 5
    def __init__(self, options, values=None):
        self.options = options
        self._values = [] if values is None else values


class Entity:
    def __init__(self, id):
        self.id = id


class DefaultValue:
    def __init__(self, id, type):
        self.id, self.type = id, type


class ChannelSelect:
    def __init__(self, values=None, defaults=()):
        self._values = values or []
        self.default_values = list(defaults)


class RoleSelect(ChannelSelect):
    pass


class UserSelect(ChannelSelect):
    pass


class View:
    def __init__(self, children):
        self.children = children


class DropdownTests(unittest.TestCase):
    def setUp(self):
        self.existing = sys.modules.get("discord")
        self.fake = types.SimpleNamespace(
            ui=types.SimpleNamespace(View=View, Button=Button, Select=Select,
                                     ChannelSelect=ChannelSelect, RoleSelect=RoleSelect,
                                     UserSelect=UserSelect),
            SelectDefaultValueType=types.SimpleNamespace(
                channel="channel", role="role", user="user"),
            SelectDefaultValue=DefaultValue,
        )
        sys.modules["discord"] = self.fake

    def tearDown(self):
        if self.existing is None:
            sys.modules.pop("discord", None)
        else:
            sys.modules["discord"] = self.existing

    def test_creation_stays_empty(self):
        control = Select([Option("one"), Option("two")])
        self.assertFalse(synchronize_dropdown_defaults(View([control])))
        self.assertFalse(any(option.default for option in control.options))

    def test_edit_preserves_saved_choice(self):
        control = Select([Option("one"), Option("two", True)])
        self.assertFalse(synchronize_dropdown_defaults(View([control])))
        self.assertEqual([x.value for x in control.options if x.default], ["two"])

    def test_live_choice_remains_selected_across_rendering(self):
        control = Select([Option("one", True), Option("two")], ["two"])
        view = View([control, Button()])
        self.assertTrue(synchronize_dropdown_defaults(view))
        self.assertEqual([x.value for x in control.options if x.default], ["two"])
        self.assertFalse(synchronize_dropdown_defaults(view))

    def test_changed_options_do_not_revive_stale_choice(self):
        control = Select([Option("new")], ["removed"])
        self.assertFalse(synchronize_dropdown_defaults(View([control])))
        self.assertFalse(control.options[0].default)

    def test_independent_panels_do_not_share_choice(self):
        a = Select([Option("one"), Option("two")], ["two"])
        b = Select([Option("one"), Option("two")])
        synchronize_dropdown_defaults(View([a]))
        synchronize_dropdown_defaults(View([b]))
        self.assertTrue(a.options[1].default)
        self.assertFalse(b.options[1].default)

    def test_entity_selectors_restore_native_discord_default_ids(self):
        for class_name, expected in [
                ("ChannelSelect", "channel"), ("RoleSelect", "role"),
                ("UserSelect", "user")]:
            cls = getattr(self.fake.ui, class_name)
            control = cls(values=[Entity(42)])
            self.assertTrue(synchronize_dropdown_defaults(View([control])))
            self.assertEqual([(x.id, x.type) for x in control.default_values],
                             [(42, expected)])
            self.assertFalse(synchronize_dropdown_defaults(View([control])))

    def test_new_entity_selector_is_blank_and_edit_default_is_preserved(self):
        saved = DefaultValue(id=42, type="channel")
        fresh = ChannelSelect()
        existing = ChannelSelect(defaults=[saved])
        self.assertFalse(synchronize_dropdown_defaults(View([fresh, existing])))
        self.assertEqual(fresh.default_values, [])
        self.assertIs(existing.default_values[0], saved)


if __name__ == "__main__":
    unittest.main()
