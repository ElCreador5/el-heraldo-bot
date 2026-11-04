"""Execute the real registration and navigation without a token or Gateway."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, MagicMock, patch

from test_safety_regressions import b, interaction
from panel_navigation import AdministrativeClose, ensure_close_control


RETIRED = {
    "joinroles", "suggestions", "programar", "heraldo_log_channel", "verify_setup",
    "verify_texts", "verify_dm_texts", "motw_set_schedule", "motw_set_channel",
    "condenar_setup", "condenar_template", "server_template_setup", "template_sync",
}


class CommandConsolidationTests(unittest.IsolatedAsyncioTestCase):
    def test_tree_exposes_only_one_entry_per_configuration_module(self):
        roots = [cmd.name for cmd in b.bot.tree.get_commands()]
        self.assertFalse(RETIRED.intersection(roots))
        self.assertEqual(len(roots), len(set(roots)))
        for name in ("setup", "embed", "honeypot", "raid", "roles_ingreso", "anuncios",
                     "mensajes", "sugerencias", "miembro_semana", "estructura_servidor"):
            self.assertEqual(roots.count(name), 1)
            self.assertIsInstance(b.bot.tree.get_command(name), b.app_commands.Command)
        self.assertEqual([cmd.name for cmd in b.bot.tree.get_commands()
                          if isinstance(cmd, b.app_commands.Group)], ["list"])
        paths = {path for _, path, _ in b._heraldo_registered_commands()}
        self.assertTrue({"list comandos", "list variables", "list embeds", "list condenados"} <= paths)

    def test_fresh_import_executes_discord_registration_without_duplicate_names(self):
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ, DB_PATH=str(Path(directory)/"startup.db"))
            env.pop("DISCORD_TOKEN", None)
            result = subprocess.run([sys.executable, "-c", "import bot; print(len(bot.bot.tree.get_commands()))"],
                                    cwd=Path(__file__).resolve().parents[1], env=env, capture_output=True,
                                    text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(int(result.stdout.strip()), len(b.bot.tree.get_commands()))

    async def test_messages_shortcut_opens_the_same_setup_panel(self):
        i = interaction()
        await b.mensajes_command.callback(i)
        self.assertIsInstance(i.response.send_message.call_args.kwargs["view"], b.HeraldoMessagesSetupView)

    async def test_new_shortcuts_reuse_existing_editors_and_do_not_save(self):
        before = self.settings()
        for command, expected in ((b.shortcut_roles_ingreso, b.HeraldoJoinRolesSetupView),
                                  (b.shortcut_sugerencias, __import__("suggestions_setup").SuggestionsSetupView),
                                  (b.shortcut_miembro_semana, b.HeraldoMotwSetupView),
                                  (b.shortcut_estructura_servidor, __import__("server_structure_setup").ServerStructureSetupView)):
            i = interaction()
            await command.callback(i)
            target = i.response.send_message.call_args.kwargs["view"]
            self.assertIsInstance(target, expected)
            ensure_close_control(target)
            target.to_components()
            self.assertEqual(self.settings(), before)

    def settings(self):
        conn=b.db_connect()
        try:
            return conn.execute("SELECT guild_id,key,value FROM guild_settings ORDER BY guild_id,key").fetchall()
        finally:
            conn.close()

    async def test_shortcuts_deny_a_member_without_management_permissions(self):
        for cmd in (b.mensajes_command, b.shortcut_roles_ingreso, b.shortcut_sugerencias,
                    b.shortcut_miembro_semana, b.shortcut_estructura_servidor):
            i=interaction(False)
            await cmd.callback(i)
            self.assertNotIn("view", i.response.send_message.call_args.kwargs)

    async def test_catalog_keeps_type_and_module_filters_and_includes_query_subcommands(self):
        view=b.HeraldoCommandsCatalog(901,10)
        self.assertEqual(len(view.commands),len(b._heraldo_registered_commands()))
        i=interaction(); i.data={"values":["roles"]}
        await view.choose_module(i)
        self.assertEqual({path for path,_ in view._rows()}, {"roles_ingreso","roles_reaccion"})
        i.data={"values":["consultation"]}
        await view.choose(i)
        self.assertEqual(view.module,"roles")
        self.assertEqual(view._rows(),[])
        i.data={"values":["all"]}
        await view.choose_module(i)
        self.assertIn("list comandos",{path for path,_ in view._rows()})
        self.assertEqual([x.value for x in view.type_select.options if x.default],["consultation"])
        self.assertEqual([x.value for x in view.module_select.options if x.default],["all"])
        self.assertFalse(await view.interaction_check(interaction(False)))

    def test_command_types_separate_configuration_actions_queries_and_maintenance(self):
        for root in ("embed","honeypot","raid","sugerencias","estructura_servidor"):
            self.assertEqual(b._heraldo_command_category(root),"configuration")
        for root in ("ban","caseupdate","verify"):
            self.assertEqual(b._heraldo_command_category(root),"action")
        for root in ("list comandos","caseinfo","variables"):
            self.assertEqual(b._heraldo_command_category(root),"consultation")
        self.assertIsNone(b.bot.tree.get_command("template_sync"))

    async def test_catalog_translates_descriptions_using_the_server_language_only(self):
        original={path for _,path,_ in b._heraldo_registered_commands()}
        for locale in b.i18n.TARGET_LOCALES:
            b.guild_config_set(901,"language",locale)
            try:
                view=b.HeraldoCommandsCatalog(901,10)
                self.assertEqual({path for _,path,_ in view.commands},original)
                self.assertEqual(view.close.label,b.i18n.translate(locale,"text.aeccae342e4bd0"))
                self.assertTrue(view.to_components())
                description=next(text for _,path,text in view.commands if path=="anuncios")
                registry=json.loads(Path("locales/command_schema.json").read_text())
                self.assertEqual(description,b.i18n.translate(locale,registry["anuncios.description"]["key"]))
            finally:
                b.guild_config_set(901,"language","es-419")

    async def test_rendered_subpanels_gain_one_close_button_without_saving_or_overflow(self):
        before=self.settings()
        parent=b.HeraldoHoneypotSetupView(901,10)
        nested=b.HeraldoHoneypotSubView(parent)
        for view in (parent,nested,b.HeraldoJoinRolesBasicView(901,10),b.HeraldoRaidSetupView(901,10)):
            ensure_close_control(view); ensure_close_control(view)
            buttons=[item for item in view.children if isinstance(item,b.discord.ui.Button)
                     and item.label in b.i18n.variants("text.aeccae342e4bd0")]
            self.assertEqual(len(buttons),1)
            self.assertEqual(buttons[0].style,b.discord.ButtonStyle.danger)
            view.to_components()
        closer=next(item for item in nested.children if isinstance(item,AdministrativeClose))
        await closer.callback(interaction())
        self.assertTrue(nested.is_finished()); self.assertTrue(parent.is_finished())
        self.assertEqual(self.settings(),before)

    async def test_close_rechecks_identity_and_permissions(self):
        view=b.HeraldoJoinRolesBasicView(901,10)
        ensure_close_control(view)
        closer=next(item for item in view.children if isinstance(item,AdministrativeClose))
        denied=interaction(False)
        await closer.callback(denied)
        denied.response.edit_message.assert_not_awaited()
        self.assertFalse(view.is_finished())
        wrong=interaction(); wrong.user.id=11
        await closer.callback(wrong)
        wrong.response.edit_message.assert_not_awaited()

    async def test_honeypot_exemption_selector_opens_and_cancel_retains_selection(self):
        view=b.HoneypotExemptSelector(901,10,True)
        self.assertTrue(view.adding)
        view.roles._values=[NS(id=123,mention="<@&123>")]
        i=interaction()
        with patch.object(b,"hp_exempt_add") as add:
            await view.select_role(i)
            confirm=i.response.edit_message.call_args.kwargs["view"]
            self.assertIs(confirm.parent,view)
            add.assert_not_called()
            await confirm.cancel.callback(i)
            self.assertIs(i.response.edit_message.call_args.kwargs["view"],view)
            self.assertEqual(view.roles.default_values[0].id,123)
            add.assert_not_called()

    async def test_raid_panel_actions_only_execute_once_after_confirmation(self):
        view=b.RaidCommandPanel(901,10)
        i=interaction()
        with (patch.object(b,"raid_is_active",return_value=False),
              patch.object(b,"raid_until",return_value=None),
              patch.object(b,"raid_config_summary",return_value="Estado"),
              patch.object(b,"raid_start",new=AsyncMock()) as start):
            await view.start.callback(i)
            start.assert_not_awaited()
            confirmation=i.response.edit_message.call_args.kwargs["view"]
            await confirmation.confirm.callback(interaction(False))
            start.assert_not_awaited()
            await confirmation.confirm.callback(i)
            start.assert_awaited_once()
            await confirmation.confirm.callback(i)
            start.assert_awaited_once()

    async def test_embed_creation_modal_is_a_draft_and_confirm_cannot_overwrite_a_newer_embed(self):
        name="command panel draft"
        b.embed_delete(901,name)
        parent=b.EmbedHubView(10,901)
        modal=b.EmbedHubCreateModal(901,10,parent)
        modal.nombre._value=name; modal.titulo._value="Draft"; modal.descripcion._value="Test"
        i=interaction(); i.channel=None
        with patch.object(b,"build_custom_embed",return_value=(b.discord.Embed(title="Draft"),None,[])):
            await modal.on_submit(i)
        self.assertIsNone(b.embed_get(901,name))
        confirmation=i.response.edit_message.call_args.kwargs["view"]
        b.embed_save(901,name,{"title":"Saved elsewhere"})
        await confirmation.confirm.callback(i)
        self.assertEqual(b.embed_get(901,name)[0],{"title":"Saved elsewhere"})
        b.embed_delete(901,name)

    async def test_embed_destination_selection_never_publishes_and_send_rechecks_permissions(self):
        name="command send draft"
        b.embed_save(901,name,{"title":"Draft"})
        view=b.EmbedChannelPicker(10,name,901)
        channel=MagicMock(spec=b.discord.TextChannel)
        channel.id=234;channel.mention="<#234>"
        channel.permissions_for.return_value=b.discord.Permissions(view_channel=True,send_messages=True,embed_links=True)
        i=interaction();i.guild.get_channel=lambda ident:channel;i.guild.me=NS(id=456)
        i.data={"values":["234"]}
        with (patch.object(b,"build_custom_embed",return_value=(b.discord.Embed(title="Draft"),None,[])),
              patch.object(b,"embed_send",new=AsyncMock(return_value="Sent")) as send):
            await view.picked(i)
            send.assert_not_awaited()
            denied=interaction(False);denied.guild=i.guild
            await view.publish.callback(denied)
            send.assert_not_awaited()
            await view.publish.callback(i)
            send.assert_awaited_once()
            await view.publish.callback(i)
            send.assert_awaited_once()
        b.embed_delete(901,name)

    async def test_moderation_reports_secondary_options_leave_room_for_close(self):
        panel = b.HeraldoUserReportsSetupView(901, 10)
        panel.pending_condemn_emoji = "❕"
        self.assertEqual(panel.extra_settings.label, b.i18n.translate("es-419", "text.81db3b5709d0ba"))
        ensure_close_control(panel)
        panel.to_components()  # Antes se lanzaba administrative_panel_has_no_close_slot.
        self.assertEqual(sum(isinstance(item, b.discord.ui.Button) and
                             item.label in b.i18n.variants("text.aeccae342e4bd0")
                             for item in panel.children), 1)
        original = self.settings()
        i = interaction()
        await panel.extra_settings.callback(i)
        more = i.response.edit_message.call_args.kwargs["view"]
        self.assertIsInstance(more, b.HeraldoUserReportsMoreOptionsView)
        self.assertIs(more.parent, panel)
        self.assertEqual(more.configure_warn_limit.label, b.i18n.translate("es-419", "text.19bd5bd18edc40"))
        self.assertEqual(more.reminders.label, b.i18n.translate("es-419", "text.471b155a597e21"))
        ensure_close_control(more)
        more.to_components()
        await more.back.callback(i)
        self.assertIs(i.response.edit_message.call_args.kwargs["view"], panel)
        self.assertEqual(panel.pending_condemn_emoji, "❕")
        self.assertEqual(self.settings(), original)

    async def test_reports_reminders_opens_inline_with_close_and_preserved_draft(self):
        panel = b.HeraldoUserReportsSetupView(901, 10)
        panel.pending_condemn_emoji = "❕"
        options = b.HeraldoUserReportsMoreOptionsView(panel)
        before = self.settings()
        i = interaction()
        await options.reminders.callback(i)
        i.response.send_message.assert_not_awaited()
        i.response.edit_message.assert_awaited_once()
        reminders = i.response.edit_message.call_args.kwargs["view"]
        self.assertIsInstance(reminders, b.ReportReminderSetupView)
        self.assertIs(reminders.parent, options)
        ensure_close_control(reminders)
        reminders.to_components()  # Must fit a red Close button without overflow.
        closes = [item for item in reminders.children
                  if isinstance(item, b.discord.ui.Button)
                  and item.label in b.i18n.variants("text.aeccae342e4bd0")]
        self.assertEqual(len(closes), 1)
        self.assertEqual(closes[0].style, b.discord.ButtonStyle.danger)
        self.assertFalse(hasattr(reminders, "custom"))  # Frequency selector opens the same modal.
        frequency = reminders.selectors["report_reminder_frequency"]
        modal_i = interaction()
        modal_i.data = {"values": ["custom"]}
        await frequency.callback(modal_i)
        modal_i.response.send_modal.assert_awaited_once()
        back_i = interaction()
        await reminders.cancel.callback(back_i)
        self.assertIs(back_i.response.edit_message.call_args.kwargs["view"], options)
        self.assertEqual(panel.pending_condemn_emoji, "❕")
        self.assertEqual(self.settings(), before)
