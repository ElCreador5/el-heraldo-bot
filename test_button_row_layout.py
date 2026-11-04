"""Offline regression tests for the global Discord button row layout."""
import sys
import types
import unittest
from button_row_layout import balance_view_buttons, install


class Button:
    width = 1

    def __init__(self, label):
        self.label = label
        self.row = None
        self._rendered_row = None
        self.callback = object()
        self.custom_id = "button:" + label
        self.disabled = False


class Select:
    width = 5

    def __init__(self):
        self.row = None
        self._rendered_row = None


class View:
    def __init__(self, items=()):
        self._children = []
        for item in items:
            self.add_item(item)

    @property
    def children(self):
        return self._children

    def clear_items(self):
        self._children.clear()

    def add_item(self, item):
        row = item.row
        if row is None:
            row = next((i for i in range(5)
                        if sum(x.width for x in self.children if x._rendered_row == i)
                        + item.width <= 5), None)
        if row is None or sum(x.width for x in self.children
                              if x._rendered_row == row) + item.width > 5:
            raise ValueError("row over capacity")
        item._rendered_row = row
        self._children.append(item)

    def to_components(self):
        rows = [[] for _ in range(5)]
        for item in self.children:
            rows[item._rendered_row].append(getattr(item, "label", "select"))
        return [row for row in rows if row]


class LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_discord = sys.modules.get("discord")
        sys.modules["discord"] = types.SimpleNamespace(
            ui=types.SimpleNamespace(View=View, Button=Button))

    @classmethod
    def tearDownClass(cls):
        if cls.old_discord is None:
            sys.modules.pop("discord", None)
        else:
            sys.modules["discord"] = cls.old_discord

    def rows(self, count, nav=("Volver", "Cerrar"), selects=0):
        actions = [Button("Acción " + str(i)) for i in range(count)]
        navigation = [Button(label) for label in nav]
        view = View([Select() for _ in range(selects)] + actions + navigation)
        identities = [(id(x), x.callback, x.custom_id, x.disabled)
                      for x in actions + navigation]
        balance_view_buttons(view)
        self.assertFalse(balance_view_buttons(view), "render must be idempotent")
        self.assertEqual(identities, [(id(x), x.callback, x.custom_id, x.disabled)
                         for x in actions + navigation])
        return view.to_components()

    def test_four_actions(self):
        self.assertEqual([len(r) for r in self.rows(4, ())], [2, 2])

    def test_five_actions_navigation(self):
        rows = self.rows(5)
        self.assertEqual([len(r) for r in rows], [3, 2, 2])
        self.assertEqual(rows[-1], ["Volver", "Cerrar"])

    def test_seven_actions(self):
        self.assertEqual([len(r) for r in self.rows(7, ())], [3, 2, 2])

    def test_selects_own_rows(self):
        self.assertEqual([len(r) for r in self.rows(4, selects=1)], [1, 2, 2, 2])

    def test_constrained_discord_rows(self):
        self.assertEqual([len(r) for r in self.rows(5, selects=3)], [1, 1, 1, 5, 2])

    def test_last_row_fallback(self):
        rows = self.rows(3, selects=4)
        self.assertEqual(rows[-1], ["Volver", "Acción 0", "Acción 1", "Acción 2", "Cerrar"])

    def test_setup_home_close_only(self):
        self.assertEqual(self.rows(3, ("Cerrar",))[-1], ["Cerrar"])

    def test_different_languages(self):
        self.assertEqual(self.rows(2, ("Back", "Close"))[-1], ["Back", "Close"])
        self.assertEqual(self.rows(2, ("Voltar", "Fechar"))[-1], ["Voltar", "Fechar"])

    def test_duplicate_navigation_not_published(self):
        view = View([Button("Acción"), Button("Volver"), Button("Volver"),
                     Button("Cerrar"), Button("Cerrar")])
        balance_view_buttons(view)
        labels = [label for row in view.to_components() for label in row]
        self.assertEqual(labels, ["Acción", "Volver", "Cerrar"])

    def test_unknown_component_unchanged(self):
        class Unknown:
            width = 2
            row = 0
            _rendered_row = None
        view = View([Unknown(), Button("Acción")])
        self.assertFalse(balance_view_buttons(view))
        self.assertEqual(len(view.children), 2)

    def test_install_once(self):
        fake = sys.modules["discord"]
        install(fake)
        wrapped = fake.ui.View.to_components
        install(fake)
        self.assertIs(fake.ui.View.to_components, wrapped)


if __name__ == "__main__":
    unittest.main()
