"""Raid Protection main: Guardar una vez, persistir atomico y actualizar el panel."""
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock
import unittest

from test_regressions import b


class RaidSaveMainTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.gid = 903688
        for key, value in zip(b.RAID_FIELDS, (12, 20, 604800, 60, 900)):
            b.guild_config_set(self.gid, key, str(value))
        self.user = NS(id=501, guild_permissions=NS(manage_guild=True))
        self.guild = NS(id=self.gid, get_role=lambda _: None)

    def interaction(self, user=None):
        response = NS(
            send_message=AsyncMock(), edit_message=AsyncMock(),
            send_modal=AsyncMock(), is_done=lambda: False,
        )
        return NS(
            guild=self.guild, user=user or self.user,
            response=response, followup=NS(send=AsyncMock()),
            data={"values": []},
        )

    def view(self):
        return b.HeraldoRaidDetectionView(
            b.HeraldoRaidSetupView(self.gid, self.user.id))

    async def test_single_save_persists_and_refreshes_same_message(self):
        view = self.view()
        view.profile_select._values = ["moderada"]
        await view.profile_select.callback(self.interaction())
        self.assertEqual(b.raid_threshold(self.gid), 12)
        self.assertIn("(pendiente)", view.summary())
        i = self.interaction()
        await view.save(i)
        self.assertEqual(b.raid_threshold(self.gid), 15)
        self.assertEqual(b.raid_new_account_ratio(self.gid), 70)
        self.assertEqual(view.draft, view.original)
        self.assertEqual(view.active_profile(), "moderada")
        self.assertNotIn("(pendiente)", view.summary())
        i.response.edit_message.assert_awaited_once()
        i.response.send_message.assert_not_awaited()
        self.assertIs(i.response.edit_message.await_args.kwargs["view"], view)
        self.assertIn("Cambios guardados", i.response.edit_message.await_args.kwargs["content"])
        self.assertTrue(next(x for x in view.children if getattr(x, "label", None) == "Guardar cambios").disabled)
        self.assertTrue(any(o.default and o.value == "moderada"
                            for o in view.profile_select.options))

    async def test_save_on_advanced_page_refreshes_both_selectors(self):
        view = self.view()
        await view.next_page(self.interaction())
        sel = view.selectors["raid_duration_seconds"]
        sel._values = ["1800"]
        await sel.callback(self.interaction())
        i = self.interaction()
        await view.save(i)
        self.assertEqual(b.raid_duration_seconds(self.gid), 1800)
        self.assertNotIn("(pendiente)", i.response.edit_message.await_args.kwargs["content"])
        self.assertTrue(any(o.default and o.value == "1800"
                            for o in view.selectors["raid_duration_seconds"].options))

    async def test_discard_and_back_never_write(self):
        view = self.view()
        view.draft["raid_threshold"] = 20
        await view.discard(self.interaction())
        self.assertEqual(b.raid_threshold(self.gid), 12)
        view.draft["raid_threshold"] = 20
        await view.back(self.interaction())
        self.assertEqual(b.raid_threshold(self.gid), 12)

    async def test_stale_draft_does_not_overwrite_another_session(self):
        view = self.view()
        view.draft["raid_threshold"] = 15
        b.guild_config_set(self.gid, "raid_threshold", "17")
        i = self.interaction()
        await view.save(i)
        self.assertEqual(b.raid_threshold(self.gid), 17)
        i.response.send_message.assert_awaited_once()
        i.response.edit_message.assert_not_awaited()

    async def test_save_rejects_revoked_permission_and_other_user(self):
        view = self.view()
        view.draft["raid_threshold"] = 15
        for user in (NS(id=502, guild_permissions=NS(manage_guild=True)),
                     NS(id=501, guild_permissions=NS(manage_guild=False))):
            i = self.interaction(user)
            await view.save(i)
            i.response.send_message.assert_awaited_once()
            i.response.edit_message.assert_not_awaited()
            self.assertEqual(b.raid_threshold(self.gid), 12)

    async def test_invalid_ratio_age_does_not_write(self):
        view = self.view()
        view.draft["raid_min_age_seconds"] = 0
        i = self.interaction()
        await view.save(i)
        self.assertEqual(b.raid_min_age_seconds(self.gid), 604800)
        i.response.send_message.assert_awaited_once()

    async def test_raw_snapshot_detects_same_effective_value_change(self):
        # Valor ausente => predeterminado 0. Otra sesión guarda 0 explícito:
        # el valor efectivo no cambia, pero el estado almacenado sí.
        connection = b.db_connect()
        try:
            connection.execute(
                "DELETE FROM guild_settings WHERE guild_id=? AND key=?",
                (self.gid, "raid_new_account_ratio"),
            )
        finally:
            connection.close()
        view = self.view()
        view.draft["raid_threshold"] = 15
        b.guild_config_set(self.gid, "raid_new_account_ratio", "0")
        i = self.interaction()
        await view.save(i)
        self.assertEqual(b.raid_threshold(self.gid), 12)
        i.response.send_message.assert_awaited_once()
        i.response.edit_message.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
