"""Matriz conductual de todos los módulos visibles de /setup, sin Gateway.

Amplía la cobertura de navegación existente: comprueba que cada entrada real
abre componentes utilizables, respeta colores en tiempo de ejecución y que
navegar no persiste cambios en SQLite. No simula acciones de administración
destructivas ni declara cubiertos todos los subpaneles profundos.
"""
from __future__ import annotations

import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, MagicMock

from test_safety_regressions import b


def guild_fixture():
    guild = MagicMock(spec=b.discord.Guild)
    guild.id = 987640
    guild.owner_id = 10
    guild.name = "Laboratorio UX"
    guild.roles = []
    guild.channels = []
    guild.text_channels = []
    guild.members = []
    guild.get_role.return_value = None
    guild.get_channel.return_value = None
    return guild


def sqlite_snapshot():
    conn = b.db_connect()
    try:
        return tuple(conn.iterdump())
    finally:
        conn.close()


class AllSetupPanelsBehaviorTests(unittest.IsolatedAsyncioTestCase):
    async def test_every_visible_module_opens_without_writing_sqlite(self):
        guild = guild_fixture()
        options = list(b.HeraldoSetupView(guild.id, 10).module_select.options)
        self.assertGreaterEqual(len(options), 4, "No se descubrieron los módulos de /setup")
        self.assertEqual(len({x.value for x in options}), len(options))
        baseline = sqlite_snapshot()
        for option in options:
            with self.subTest(module=option.value):
                view = b.HeraldoSetupView(guild.id, 10)
                interaction = NS(
                    data={"values": [option.value]},
                    guild=guild,
                    response=NS(
                        edit_message=AsyncMock(),
                        send_message=AsyncMock(),
                    ),
                )
                await view.select_module(interaction)
                interaction.response.edit_message.assert_awaited_once()
                target = interaction.response.edit_message.call_args.kwargs.get("view")
                self.assertIsInstance(target, b.discord.ui.View)
                self.assertTrue(target.to_components(), "Panel sin controles")
                self.assertEqual(
                    sqlite_snapshot(), baseline,
                    f"Abrir {option.value} modificó la base SQLite",
                )

    async def test_every_visible_module_has_correct_runtime_palette(self):
        guild = guild_fixture()
        options = list(b.HeraldoSetupView(guild.id, 10).module_select.options)
        seen = {"cancel": 0, "back": 0, "save": 0}
        for option in options:
            with self.subTest(module=option.value):
                interaction = NS(
                    data={"values": [option.value]}, guild=guild,
                    response=NS(edit_message=AsyncMock(), send_message=AsyncMock()),
                )
                await b.HeraldoSetupView(guild.id, 10).select_module(interaction)
                view = interaction.response.edit_message.call_args.kwargs["view"]
                for component in view.children:
                    if not isinstance(component, b.discord.ui.Button):
                        continue
                    label = component.label or ""
                    if label.startswith(("Cancelar", "Cerrar", "Descartar")):
                        self.assertEqual(component.style, b.discord.ButtonStyle.danger,
                                         (option.value, label))
                        seen["cancel"] += 1
                    elif label.startswith("Volver") or label == "Vista previa":
                        self.assertEqual(component.style, b.discord.ButtonStyle.secondary,
                                         (option.value, label))
                        seen["back"] += 1
                    elif label.startswith("Guardar"):
                        self.assertEqual(component.style, b.discord.ButtonStyle.success,
                                         (option.value, label))
                        seen["save"] += 1
        self.assertGreater(seen["back"], 0, "No se verificaron botones de navegación")
        self.assertGreater(seen["save"], 0, "No se verificaron botones de guardado")

    async def test_every_visible_module_can_be_opened_twice_without_state_leak(self):
        guild = guild_fixture()
        for option in b.HeraldoSetupView(guild.id, 10).module_select.options:
            with self.subTest(module=option.value):
                panels = []
                for _ in range(2):
                    response = NS(edit_message=AsyncMock(), send_message=AsyncMock())
                    interaction = NS(
                        data={"values": [option.value]}, guild=guild,
                        response=response,
                    )
                    await b.HeraldoSetupView(guild.id, 10).select_module(interaction)
                    panels.append(response.edit_message.call_args.kwargs["view"])
                self.assertIsNot(panels[0], panels[1])
                self.assertEqual(
                    [type(item) for item in panels[0].children],
                    [type(item) for item in panels[1].children],
                )




class SetupSelectorDraftPersistenceTests(unittest.TestCase):
    """Barrera estructural común: los selects de configuración no escriben datos."""

    def test_administrative_select_callbacks_never_commit_directly(self):
        import ast
        from pathlib import Path
        source = Path(__file__).resolve().parents[1] / "bot.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        forbidden = {
            "guild_config_set", "guild_resource_set",
            "hp_setting_set", "hp_add_trap", "hp_remove_trap",
            "verification_atomic_setup_save", "set_motw_channel_id",
        }
        checked = 0
        for klass in tree.body:
            if not isinstance(klass, ast.ClassDef):
                continue
            if not any(key in klass.name.lower() for key in ("view", "select", "editor", "modal")):
                continue
            for method in klass.body:
                if not isinstance(method, ast.AsyncFunctionDef):
                    continue
                if not method.name.startswith(("select", "choose", "pick", "_select")):
                    continue
                checked += 1
                for call in ast.walk(method):
                    if not isinstance(call, ast.Call):
                        continue
                    called = call.func
                    name = called.id if isinstance(called, ast.Name) else (
                        called.attr if isinstance(called, ast.Attribute) else ""
                    )
                    self.assertNotIn(name, forbidden,
                                     f"{klass.name}.{method.name} guarda al seleccionar")
        self.assertGreaterEqual(checked, 40,
                                "La revisión perdió cobertura de selectores de setup")

if __name__ == "__main__":
    unittest.main()
