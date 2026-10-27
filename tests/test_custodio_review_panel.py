"""Las revisiones requieren administrador, confirmación y una acción real."""
from types import SimpleNamespace as NS
import unittest
from unittest.mock import AsyncMock,patch,Mock
import discord
from custodio_core import RulesSnapshot
from custodio_discipline import ReviewedIncident
from custodio_review import CustodioReviewPanel,report_review_view,dispatch
from custodio_server_rule_actions_setup import encode


class ReviewPanelTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.snapshot=RulesSnapshot(101,('No enviar spam.',),'a'*64)
        self.incident=ReviewedIncident(101,20,30,1,'a'*64,'https://discord.com/channels/101/5/6')
        self.execute=AsyncMock(return_value={'status':'complete','case_number':7,'action':'warn'})
        raw=encode(self.snapshot,['warn'],[60])
        self.namespace={'guild_config_get':lambda gid,key:raw,'custodio_discipline_engine':NS(execute=self.execute)}
        self.guild=NS(id=101,owner_id=999)
        self.interaction=NS(guild=self.guild,guild_id=101,user=NS(id=1,guild_permissions=discord.Permissions(administrator=True)),
            response=NS(defer=AsyncMock(),edit_message=AsyncMock()),edit_original_response=AsyncMock())

    async def test_open_and_discard_never_sanction(self):
        view=CustodioReviewPanel(self.namespace,1,self.snapshot,self.incident)
        self.assertIn('Advertir',view.summary())
        await view.discard.callback(self.interaction)
        self.execute.assert_not_awaited()

    async def test_confirm_checks_current_permission_and_calls_executor_once(self):
        view=CustodioReviewPanel(self.namespace,1,self.snapshot,self.incident)
        report=NS(embeds=[],edit=AsyncMock())
        channel=NS(fetch_message=AsyncMock(return_value=report))
        with patch('custodio_review._get_safe_existing',return_value=channel):
            await view.confirm.callback(self.interaction)
            await view.confirm.callback(self.interaction)
        self.execute.assert_awaited_once()
        self.assertFalse(self.execute.call_args.kwargs['automatic'])
        self.assertTrue(self.execute.call_args.kwargs['administrator_confirmed'])
        self.assertTrue(self.execute.call_args.kwargs['verified'])

    async def test_permission_revoked_blocks_effects(self):
        view=CustodioReviewPanel(self.namespace,1,self.snapshot,self.incident)
        self.interaction.user.guild_permissions=discord.Permissions.none()
        await view.confirm.callback(self.interaction)
        self.execute.assert_not_awaited()

    async def test_button_id_survives_restart_without_storing_a_transcript(self):
        widget=report_review_view(123456)
        self.assertEqual(widget.children[0].custom_id,'custodio-review:123456')
        self.assertFalse(await dispatch({},NS(data={'custom_id':'unrelated:123'})))

    async def test_failed_ack_cannot_execute_anything(self):
        error=discord.NotFound(NS(status=404,reason='NotFound'),{'code':10062,'message':'Unknown interaction'})
        interaction=NS(data={'custom_id':'custodio-review:123'},response=NS(defer=AsyncMock(side_effect=error)))
        self.assertTrue(await dispatch({},interaction))
        self.execute.assert_not_awaited()


if __name__=='__main__':unittest.main()
