import copy
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock
import discord
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from message_components import validate, build_view, ActionConfirm
from message_editor import VisualEditor, VisualModal


class EditorTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.template = {'name': 'Aviso', 'content': 'Original'}
        self.saved = [copy.deepcopy(self.template)]
        self.host = {'configuration_access': AsyncMock(return_value=True),
                     'heraldo_template_list': lambda _: copy.deepcopy(self.saved),
                     'confirm_configuration': AsyncMock()}
        self.interaction = NS(guild_id=1, user=NS(id=2), response=NS(send_message=AsyncMock(), edit_message=AsyncMock()))

    async def test_visual_changes_remain_draft_until_confirmation(self):
        view = VisualEditor(self.host, 1, 2, self.template)
        modal = VisualModal(view, 'content')
        modal.inputs['content']._value = 'Nuevo texto'
        await modal.on_submit(self.interaction)
        self.assertEqual(self.saved[0]['content'], 'Original')
        await view.save.callback(self.interaction)
        proposal = self.host['confirm_configuration'].call_args.args[2]
        self.assertEqual(json.loads(proposal['message_custom_templates'])[0]['content'], 'Nuevo texto')

    async def test_visual_concurrent_changes_are_not_overwritten(self):
        view = VisualEditor(self.host, 1, 2, self.template)
        self.saved[0]['content'] = 'Otro administrador'
        await view.save.callback(self.interaction)
        self.host['confirm_configuration'].assert_not_awaited()

    async def test_stale_visual_modal_is_rejected(self):
        view = VisualEditor(self.host, 1, 2, self.template)
        modal = VisualModal(view, 'content')
        modal.inputs['content']._value = 'No aplicar'
        view.version += 1
        await modal.on_submit(self.interaction)
        self.assertEqual(view.draft['content'], 'Original')

    async def test_empty_embed_cannot_be_saved(self):
        view = VisualEditor(self.host, 1, 2, self.template)
        await view.add_embed.callback(self.interaction)
        await view.save.callback(self.interaction)
        self.host['confirm_configuration'].assert_not_awaited()

    async def test_components_independent_options_and_multiple_selection(self):
        definitions = [{'tipo': 'menu', 'etiqueta': 'Opciones', 'maximo': 2, 'opciones': [
            {'etiqueta': 'Primera', 'acciones': [{'tipo': 'respuesta', 'plantilla': 'Uno'}]},
            {'etiqueta': 'Segunda', 'acciones': [{'tipo': 'añadir_rol', 'rol': '123'}, {'tipo': 'dm', 'plantilla': 'Dos'}]}]}]
        template = {'componentes': definitions, 'componentes_revision': 'abcdef'}
        view = build_view(template, 1)
        self.assertEqual(view.children[0].max_values, 2)
        self.assertEqual(len(view.children[0].options), 2)
        self.assertIn(':1:abcdef:', view.children[0].custom_id)
        json.dumps(view.to_components())
        self.assertEqual(validate(definitions), definitions)

    async def test_components_reject_limits_and_invalid_types(self):
        bad = [None, [{'tipo': 'script', 'etiqueta': 'X'}],
               [{'tipo': 'boton', 'etiqueta': 'X', 'acciones': [{'tipo': 'añadir_rol', 'rol': 123}]}],
               [{'tipo': 'boton', 'etiqueta': 'X', 'acciones': [{'tipo': 'eliminar'}, {'tipo': 'dm', 'plantilla': 'Y'}]}]]
        for value in bad:
            with self.assertRaises(ValueError):
                validate(value)

    async def test_component_cancel_has_no_effects(self):
        view = ActionConfirm(self.host, 1, 2, NS(), self.template, [{'tipo': 'eliminar'}])
        await view.cancel.callback(self.interaction)
        self.assertTrue(view.finished)
        self.host['confirm_configuration'].assert_not_awaited()

    async def test_component_other_owner_is_rejected(self):
        view = ActionConfirm(self.host, 1, 3, NS(), self.template, [{'tipo': 'eliminar'}])
        self.assertFalse(await view.interaction_check(self.interaction))

    async def test_visual_long_description_is_not_silently_truncated(self):
        view = VisualEditor(self.host, 1, 2, {'name': 'Largo', 'embeds': [{'description': 'x' * 4096}]})
        with self.assertRaises(ValueError):
            VisualModal(view, 'text')
        self.assertEqual(len(view.draft['embeds'][0]['description']), 4096)

    async def test_modal_from_closed_editor_cannot_reopen_draft(self):
        view = VisualEditor(self.host, 1, 2, self.template)
        modal = VisualModal(view, 'content')
        modal.inputs['content']._value = 'Tardío'
        await view.cancel.callback(self.interaction)
        await modal.on_submit(self.interaction)
        self.assertEqual(view.draft['content'], 'Original')
        self.assertIn('cerrado', self.interaction.response.send_message.call_args.args[0])

    async def test_component_partial_failure_stops_sequence_and_persists_audit(self):
        with tempfile.TemporaryDirectory() as folder:
            connect = lambda: sqlite3.connect(str(Path(folder) / 'actions.db'), isolation_level=None)
            template = dict(self.template, componentes_revision='one', componentes_autor=3)
            member = NS(id=2, send=AsyncMock())
            author = NS(id=3, guild_permissions=discord.Permissions(manage_guild=True))
            guild = NS(id=1, fetch_member=AsyncMock(side_effect=lambda uid: member if uid == 2 else author))
            host = dict(self.host, db_connect=connect, heraldo_template_list=lambda _: [template],
                        condemnation_get=lambda *_: None, heraldo_template_payload=lambda *_: {'content': 'Respuesta'})
            i = self.interaction
            i.guild = guild
            i.response.defer = AsyncMock()
            i.edit_original_response = AsyncMock()
            actions = [{'tipo': 'dm', 'plantilla': 'Aviso'}, {'tipo': 'dm', 'plantilla': 'Ausente'}, {'tipo': 'dm', 'plantilla': 'Aviso'}]
            view = ActionConfirm(host, 1, 2, NS(channel=NS()), template, actions)
            await view.execute.callback(i)
            member.send.assert_awaited_once()
            self.assertIn('ya no existe', i.edit_original_response.call_args.kwargs['content'])
            conn = connect()
            self.assertEqual(conn.execute('SELECT outcome FROM message_action_audit').fetchall(), [('ok',), ('error',)])
            conn.close()
            repeat = ActionConfirm(host, 1, 2, NS(channel=NS()), template, actions)
            await repeat.execute.callback(i)
            member.send.assert_awaited_once()
            self.assertIn('quince segundos', i.edit_original_response.call_args.kwargs['content'])

    async def test_component_revoked_author_and_active_condemnation_block_actions(self):
        for revoked in (False, True):
            with tempfile.TemporaryDirectory() as folder:
                template = dict(self.template, componentes_revision='one', componentes_autor=3)
                member = NS(id=2, send=AsyncMock())
                author = NS(id=3, guild_permissions=discord.Permissions(manage_guild=not revoked))
                host = dict(self.host, db_connect=lambda: sqlite3.connect(str(Path(folder) / 'actions.db'), isolation_level=None),
                            heraldo_template_list=lambda _: [template], condemnation_get=lambda *_: None if revoked else {'active': True})
                i = self.interaction
                i.guild = NS(id=1, fetch_member=AsyncMock(side_effect=lambda uid: member if uid == 2 else author))
                i.response.defer = AsyncMock()
                i.edit_original_response = AsyncMock()
                view = ActionConfirm(host, 1, 2, NS(channel=NS()), template, [{'tipo': 'dm', 'plantilla': 'Aviso'}])
                await view.execute.callback(i)
                member.send.assert_not_awaited()
                self.assertIn('permisos' if revoked else 'condena', i.edit_original_response.call_args.kwargs['content'])
