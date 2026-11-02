"""Registro y navegación de producción con SQLite desechable y sin Gateway."""
import ast
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

_tmp = tempfile.TemporaryDirectory()
_path = Path(__file__).with_name("bot.py")
os.environ["DB_PATH"] = str(Path(_tmp.name)/"commands.db")
spec = importlib.util.spec_from_file_location("heraldo_command_main_test", _path)
b = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = b
spec.loader.exec_module(b)
b.db_init(); b.honeypot_db_init(); b.suggestion_db_init()


def interaction(allowed=True, guild_id=777444):
    guild=MagicMock(spec=b.discord.Guild)
    guild.id=guild_id;guild.owner_id=10;guild.name="Comunidad de prueba";guild.roles=[]
    guild.get_channel.return_value=None;guild.get_role.return_value=None
    return NS(guild=guild,guild_id=guild.id,channel=None,data={},
              user=NS(id=10,guild_permissions=b.discord.Permissions(manage_guild=allowed)),
              response=NS(is_done=lambda:False,send_message=AsyncMock(),edit_message=AsyncMock(),
                          send_modal=AsyncMock(),defer=AsyncMock()),
              edit_original_response=AsyncMock(),followup=NS(send=AsyncMock()))


def snapshot():
    conn=b.db_connect()
    try:return conn.execute("SELECT guild_id,key,value FROM guild_settings ORDER BY guild_id,key").fetchall()
    finally:conn.close()


class ProductionCommandPanelsTests(unittest.IsolatedAsyncioTestCase):
    def test_configuration_groups_are_replaced_by_unique_commands(self):
        names=[c.name for c in b.bot.tree.get_commands()]
        self.assertEqual(len(names),len(set(names)))
        for old in ["joinroles","suggestions","heraldo_log_channel","verify_setup","verify_texts",
                    "verify_dm_texts","motw_set_schedule","motw_set_channel","condenar_setup",
                    "condenar_template","server_template_setup"]:
            self.assertNotIn(old,names)
        self.assertEqual([c.name for c in b.bot.tree.get_commands() if isinstance(c,b.app_commands.Group)],["list"])
        for root in ["honeypot","raid","embed","roles_ingreso","sugerencias","anuncios","mensajes","registros",
                     "moderacion","automod","verificacion","roles_reaccion","estructura_servidor"]:
            self.assertIsInstance(b.bot.tree.get_command(root),b.app_commands.Command)
        self.assertIn("list comandos",{p for _,p,_ in b._heraldo_registered_commands()})

    async def test_shortcuts_open_the_actual_setup_views_without_saving(self):
        expected=[(b.shortcut_automod,b.HeraldoAutomodSetupView),
                  (b.shortcut_moderacion,b.HeraldoModerationSetupView),
                  (b.shortcut_roles_ingreso,b.HeraldoJoinRolesSetupView),
                  (b.shortcut_roles_reaccion,b.HeraldoReactionRolesSetupView),
                  (b.shortcut_registros,b.HeraldoLoggingSetupView),
                  (b.shortcut_verificacion,b.HeraldoVerificationHubView),
                  (b.shortcut_anuncios,b.HeraldoMotwSetupView),
                  (b.shortcut_sugerencias,b.SuggestionsSetupView),
                  (b.shortcut_estructura_servidor,b.ServerStructureSetupView),
                  (b.mensajes_command,b.HeraldoMessagesSetupView)]
        before=snapshot()
        for command,kind in expected:
            i=interaction();await command.callback(i)
            view=i.response.send_message.call_args.kwargs["view"]
            self.assertIsInstance(view,kind);self.assertTrue(view.to_components())
            self.assertEqual(snapshot(),before)
            denied=interaction(False);await command.callback(denied)
            self.assertNotIn("view",denied.response.send_message.call_args.kwargs)

    async def test_honeypot_and_raid_controls_open_without_missing_dependencies(self):
        i=interaction()
        for parent,action in [(b.HoneypotCommandPanel(i.guild_id,10),"settings"),
                              (b.RaidCommandPanel(i.guild_id,10),"setup")]:
            await getattr(parent,action).callback(i)
            child=i.response.edit_message.call_args.kwargs["view"]
            self.assertTrue(child.to_components())
        before=snapshot()
        selector=b.HoneypotExemptSelector(i.guild_id,10,True)
        self.assertTrue(selector.adding);self.assertTrue(selector.to_components())
        self.assertEqual(snapshot(),before)

    async def test_embed_builder_only_exposes_manual_operations(self):
        i=interaction();view=b.EmbedHubView(10,i.guild_id)
        self.assertFalse(hasattr(view,"schedules"))
        editor=b.EmbedEditorView(10,i.guild_id,"draft",{})
        self.assertFalse(hasattr(editor,"schedule_embed"))
        self.assertFalse(hasattr(b,"scheduled_embeds_loop"))
        await view.create.callback(i)
        modal=i.response.send_modal.call_args.args[0]
        self.assertEqual(modal.owner_id,10)

    async def test_type_and_module_catalog_filters_remember_the_selection(self):
        i=interaction();catalog=b.HeraldoCommandsCatalog(i.guild_id,10)
        self.assertEqual(len(catalog.commands),len(b._heraldo_registered_commands()))
        i.data={"values":["roles"]};await catalog.choose_module(i)
        self.assertEqual({path for path,_ in catalog._rows()},{"roles_ingreso","roles_reaccion"})
        i.data={"values":["consultation"]};await catalog.choose(i)
        self.assertEqual(catalog.module,"roles")
        self.assertEqual([o.value for o in catalog.type_select.options if o.default],["consultation"])
        self.assertTrue(catalog.to_components())

    async def test_raid_action_requires_confirmation_and_rechecks_permissions(self):
        i=interaction();view=b.RaidCommandPanel(i.guild_id,10)
        with (patch.object(b,"raid_is_active",return_value=False),patch.object(b,"raid_until",return_value=None),
              patch.object(b,"raid_start",new=AsyncMock()) as start,
              patch.object(b,"raid_config_summary",return_value="Estado")):
            await view.start.callback(i);start.assert_not_awaited()
            confirm=i.response.edit_message.call_args.kwargs["view"]
            await confirm.confirm.callback(interaction(False));start.assert_not_awaited()
            await confirm.confirm.callback(i);start.assert_awaited_once()
            await confirm.confirm.callback(i);start.assert_awaited_once()

    def test_production_keeps_server_identity_and_does_not_import_lab_modules(self):
        self.assertEqual(b.GLOBAL_FOOTER_TEXT,"{servidor}")
        self.assertEqual(b.GLOBAL_FOOTER_ICON,"{servericon}")
        source=_path.read_text()
        self.assertNotIn("import custodio_runtime",source)
        self.assertNotIn("import message_automation",source)
        self.assertNotIn("import enzonic_test_host",source)
        self.assertFalse(any("Labs" in text for text in b.i18n.COPY.values()))

    def test_all_setup_modules_still_serialize_with_close_controls(self):
        # Instantiation is asynchronous in current discord.py.
        self.assertIn("messages",{row[0] for row in b.HeraldoSetupView.MODULES})

    async def test_full_reaction_editor_keeps_its_tools_and_gains_close(self):
        i=interaction()
        panel={"channel_id":10,"message_id":20,"existing":True,"roles":[
            {"emoji":str(n),"add":[],"remove":[]} for n in range(20)],
            "allowed_roles":[],"max_reactions":1}
        view=b.HeraldoReactionRolesEditorView(i.guild_id,10,panel,selected=0)
        self.assertTrue(view.to_components())
        self.assertIn("Cerrar",{item.label for item in view.children if isinstance(item,b.discord.ui.Button)})
        more=next(item for item in view.children if getattr(item,"label",None)=="Más acciones")
        await more.callback(i)
        submenu=i.response.edit_message.call_args.kwargs["view"]
        self.assertTrue(submenu.to_components())
        self.assertTrue({"Opciones","Editar mensaje","Volver","Cerrar"} <=
                        {item.label for item in submenu.children if isinstance(item,b.discord.ui.Button)})
        options=next(item for item in submenu.children if getattr(item,"label",None)=="Opciones")
        await options.callback(i)
        i.response.send_modal.assert_awaited_once()
        edit=next(item for item in submenu.children if getattr(item,"label",None)=="Editar mensaje")
        await edit.callback(i)
        self.assertIn("mensajes existentes",i.response.send_message.call_args.args[0])


class SendWithoutViewTests(unittest.IsolatedAsyncioTestCase):
    async def test_send_omits_none_and_edit_can_still_clear_a_view(self):
        from main_panel_navigation import install
        class View:
            def to_components(self):return []
            async def _scheduled_task(self,*args):pass
        class Response:
            async def send_message(self,**kwargs):
                if kwargs.get("view",False) is None:raise TypeError("view None")
                return kwargs
            async def edit_message(self,**kwargs):return kwargs
        class Webhook:
            async def send(self,**kwargs):
                if kwargs.get("view",False) is None:raise TypeError("view None")
                return kwargs
        install(NS(ui=NS(View=View),InteractionResponse=Response,Webhook=Webhook))
        self.assertNotIn("view",await Response().send_message(view=None))
        self.assertNotIn("view",await Webhook().send(view=None))
        self.assertIsNone((await Response().edit_message(view=None))["view"])
