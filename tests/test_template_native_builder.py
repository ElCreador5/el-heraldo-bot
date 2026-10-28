"""Regresiones del constructor nativo de /setup -> Mensajes -> Plantillas."""
import copy
import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock

import discord
import message_payload
from template_native_builder import (
    TemplateEditorView, TemplateConfirmView, to_builder, to_raw,
)
from test_safety_regressions import b


class NativeTemplateTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.templates = []
        self.save = Mock()
        self.host = {
            "guild_config_get": lambda *args: "[]",
            "heraldo_template_list": lambda gid: copy.deepcopy(self.templates),
            "heraldo_template_save": self.save,
            "HeraldoTemplateSetupView": lambda gid, uid, selected=None: discord.ui.View(),
            "configuration_access": AsyncMock(return_value=True),
            "stamp_embed": lambda embed, guild: embed,
        }
        self.interaction = NS(
            guild_id=123,
            guild=NS(id=123),
            user=NS(id=7, guild_permissions=discord.Permissions(manage_guild=True)),
            response=NS(edit_message=AsyncMock(), send_message=AsyncMock(),
                        send_modal=AsyncMock()),
        )

    async def test_create_template_button_has_complete_label(self):
        view = b.HeraldoTemplateSetupView(123, 7)
        self.assertEqual(view.create.label, "Crear plantilla")
        self.assertEqual(view.edit.label, "Editar plantilla")

    async def test_single_native_view_respects_five_action_rows(self):
        view = TemplateEditorView(self.host, 123, 7)
        rows = [0, 0, 0, 0, 0]
        for child in view.children:
            self.assertIn(child.row, range(5))
            rows[child.row] += 1
        self.assertTrue(all(count <= 5 for count in rows))
        self.assertEqual(sum(rows), len(view.children))
        self.assertEqual(len([x for x in view.children if isinstance(x, discord.ui.ChannelSelect)]), 1)
        self.assertEqual(len([x for x in view.children if isinstance(x, discord.ui.RoleSelect)]), 1)
        self.assertIsNone(view.start)
        self.assertIn("Guardar cambios", [x.label for x in view.children if hasattr(x, "label")])
        self.assertNotIn(view.discard, view.children)

    async def test_main_panel_shows_reference_sections_in_order(self):
        view = TemplateEditorView(self.host, 123, 7)
        panel = view.panel_embed(self.interaction.guild)
        self.assertEqual(panel.title, "Editor de plantillas")
        self.assertEqual([field.name for field in panel.fields[:4]],
                         ["Canal de publicación", "Nombre de plantilla",
                          "Mensaje", "Constructor de embed"])
        self.assertTrue(panel.fields[4].name.startswith("Fecha"))
        self.assertEqual(panel.fields[5].name, "Rol a mencionar")
        self.assertEqual(panel.fields[6].name, "Repetir cada")
        self.assertIn("Meses: **0**", panel.fields[6].value)
        self.assertEqual(view.publish_button.label, "Enviar")
        self.assertEqual(view.frequency.label, "Repetir cada")
        self.assertEqual(view.name_button.label, "Nombre de plantilla")

    async def test_panel_reflects_draft_without_auto_save(self):
        view = TemplateEditorView(self.host, 123, 7)
        view.name, view.text = "Aviso", "Hola mundo"
        view.channel_id, view.role_id = 321, 444
        view.parts = {"months": 0, "days": 1, "hours": 2, "minutes": 0}
        fields = view.panel_embed(self.interaction.guild).fields
        self.assertIn("<#321>", fields[0].value)
        self.assertIn("Aviso", fields[1].value)
        self.assertIn("Hola mundo", fields[2].value)
        self.assertIn("<@&444>", fields[5].value)
        self.assertIn("Días: **1**", fields[6].value)
        self.save.assert_not_called()

    async def test_repeat_button_opens_native_numeric_modal(self):
        view = TemplateEditorView(self.host, 123, 7)
        await view.frequency.callback(self.interaction)
        modal = self.interaction.response.send_modal.call_args.args[0]
        self.assertEqual(len(modal.children), 4)
        self.assertEqual([field.label for field in modal.children],
                         ["Meses", "Días", "Horas", "Minutos"])

    async def test_save_requires_second_confirmation_and_does_not_publish(self):
        view = TemplateEditorView(self.host, 123, 7)
        view.name, view.text = "Aviso", "Hola mundo"
        view.dirty = True
        await view.save.callback(self.interaction)
        self.save.assert_not_called()
        confirm = self.interaction.response.edit_message.call_args.kwargs["view"]
        self.assertIsInstance(confirm, TemplateConfirmView)
        await confirm.confirm.callback(self.interaction)
        self.save.assert_called_once()
        saved = self.save.call_args.args[1]
        self.assertEqual(saved[0]["name"], "Aviso")
        self.assertEqual(saved[0]["content"], "Hola mundo")
        self.assertNotIn("start", saved[0])
        self.assertNotIn("channel", saved[0])
        # Seguir en el mismo editor sin perder la preparación del envío.
        displayed = self.interaction.response.edit_message.call_args.kwargs["view"]
        self.assertIs(displayed, view)
        self.assertEqual(view.original_name, "Aviso")
        self.assertFalse(view.dirty)

    async def test_publish_without_saved_template_is_blocked(self):
        view = TemplateEditorView(self.host, 123, 7)
        view.name, view.text = "Prueba", "Mensaje de prueba"
        await view.publish_button.callback(self.interaction)
        self.assertIn("Guarda y confirma", self.interaction.response.edit_message.call_args.kwargs["content"])
        self.save.assert_not_called()

    async def test_preserves_other_embeds_and_attached_components(self):
        old = {"name": "Aviso", "content": "Hola",
               "embeds": [{"title": "Primero"}, {"title": "Segundo"}],
               "role_component": "Acceso", "role_component_mode": "boton"}
        self.templates = [copy.deepcopy(old)]
        view = TemplateEditorView(self.host, 123, 7, old)
        result = view.template()
        self.assertEqual(len(result["embeds"]), 2)
        self.assertEqual(result["embeds"][1]["title"], "Segundo")
        self.assertEqual(result["role_component"], "Acceso")
        self.assertEqual(result["content"], "Hola")

    async def test_timestamps_and_author_fields_roundtrip(self):
        raw = {"title": "Aviso", "color": 12345,
               "author": {"name": "Autor", "icon_url": "https://example.com/i.png"},
               "fields": [{"name": "Uno", "value": "Dos", "inline": True}],
               "timestamp": "2026-10-28T10:00:00+00:00"}
        rebuilt = to_raw(to_builder(raw))
        self.assertEqual(rebuilt["author"]["name"], "Autor")
        self.assertEqual(rebuilt["fields"][0]["name"], "Uno")
        self.assertTrue(rebuilt["timestamp"])
        message_payload.validate({"embeds": [rebuilt]})

    async def test_name_and_content_changes_are_not_persisted_on_select(self):
        view = TemplateEditorView(self.host, 123, 7)
        view.name = "Nueva"
        view.text = "Borrador"
        self.assertEqual(self.templates, [])
        self.save.assert_not_called()

    async def test_concurrent_template_changes_block_confirm(self):
        view = TemplateEditorView(self.host, 123, 7)
        view.name, view.text = "Prueba", "Texto"
        await view.save.callback(self.interaction)
        confirm = self.interaction.response.edit_message.call_args.kwargs["view"]
        self.templates.append({"name": "Otra", "content": "Otro contenido"})
        await confirm.confirm.callback(self.interaction)
        self.save.assert_not_called()
        self.assertIn("cambiaron", self.interaction.response.edit_message.call_args.kwargs["content"])


if __name__ == "__main__":
    unittest.main()
