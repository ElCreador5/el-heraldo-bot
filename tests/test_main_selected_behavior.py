"""SQLite and runtime behavior checks for main settings promotion."""
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, patch

import discord
from main_case_management import CaseDeleteModal, CaseManagerView
from member_rejoin_restore import capture_departure, restore_join, saved_role
from main_pending_roles import pending_get, pending_set
from message_automation import ScheduledMessages
from message_autofeeds import persist_schedule, get_jobs


class MainSelectedBehaviorTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        path = str(Path(self.tempdir.name) / "bot.db")
        self.connect = lambda: sqlite3.connect(path, isolation_level=None)
        db = self.connect()
        db.execute(
            "CREATE TABLE guild_settings (guild_id INTEGER, key TEXT, value TEXT, "
            "PRIMARY KEY(guild_id,key))")
        db.execute("CREATE TABLE guild_config(guild_id INTEGER PRIMARY KEY, updated_at TEXT)")
        db.execute("INSERT INTO guild_config(guild_id,updated_at) VALUES(1,'now'),(2,'now')")
        db.execute("CREATE TABLE moderation_cases(guild_id INTEGER, case_number INTEGER, open INTEGER, "
                   "type TEXT DEFAULT 'WARN', user_id INTEGER DEFAULT 2, reason TEXT DEFAULT 'Test')")
        db.execute("CREATE TABLE guild_cases(guild_id INTEGER, user_id INTEGER, active INTEGER)")
        db.close()

    def host(self):
        def get(gid, key):
            db = self.connect()
            try:
                row = db.execute("SELECT value FROM guild_settings WHERE guild_id=? AND key=?",
                                 (gid,key)).fetchone()
                return row[0] if row else None
            finally:
                db.close()
        def put(gid,key,val):
            db = self.connect()
            try:
                db.execute("INSERT INTO guild_settings(guild_id,key,value) VALUES(?,?,?) "
                           "ON CONFLICT(guild_id,key) DO UPDATE SET value=excluded.value",
                           (gid,key,val))
            finally:
                db.close()
        return {"db_connect":self.connect,"guild_config_get":get,"guild_config_set":put,
                "guild_language":lambda gid:"es-419",
                "moderation_case_code":lambda number,gid:f"EH-{gid}-{number}",
                "moderation_case_get":lambda gid,number:None}

    def test_scheduled_announcements_persist_and_state_is_idempotent(self):
        host = self.host()
        engine = ScheduledMessages(host)
        engine.initialize()
        actor = NS(id=22,guild_permissions=NS(administrator=True, manage_guild=True,
                                              manage_messages=True))
        now = datetime.now(timezone.utc) + timedelta(hours=2)
        job = dict(id="announcement-test-1", author=actor.id, guild=1,
                   requester=actor.id, start=now.isoformat(),
                   autofeed=True, text="Mensaje de prueba", embed=None,
                   channel=66, repeat="diaria", zone="America/Santo_Domingo",
                   role=None, paused=False)
        persist_schedule(host,1,actor,job)
        self.assertEqual(len(get_jobs(host,1)),1)
        self.assertEqual(len(get_jobs(host,2)),0)
        self.assertEqual(engine.state(1,job)[1],"pending")
        self.assertEqual(engine.state(1,job)[1],"pending")

    async def test_case_cleanup_requires_phrase_and_is_guild_scoped(self):
        db=self.connect()
        db.execute("INSERT INTO moderation_cases(guild_id,case_number,open) VALUES(1,1,1),(1,2,0),(2,1,1)")
        db.execute("INSERT INTO guild_cases(guild_id,user_id,active) VALUES(1,2,1)")
        db.close()
        host=self.host()
        panel=NS(guild_id=1,owner_id=5,host=host,locale="es-419",
                 authorize=AsyncMock(return_value=True),is_finished=lambda:False,
                 t=lambda key,**kw:"Limpiados" if key=="deleted" else key)
        modal=CaseDeleteModal(panel,"all")
        i=NS(user=NS(id=5),response=NS(send_message=AsyncMock()))
        modal.acknowledgement._value="INCORRECTO"
        await modal.on_submit(i)
        db=self.connect()
        self.assertEqual(db.execute("SELECT COUNT(*) FROM moderation_cases WHERE guild_id=1").fetchone()[0],2)
        db.close()
        modal.acknowledgement._value="LIMPIAR TODO"
        await modal.on_submit(i)
        db=self.connect()
        self.assertEqual(db.execute("SELECT COUNT(*) FROM moderation_cases WHERE guild_id=1").fetchone()[0],0)
        self.assertEqual(db.execute("SELECT COUNT(*) FROM moderation_cases WHERE guild_id=2").fetchone()[0],1)
        self.assertEqual(db.execute("SELECT COUNT(*) FROM guild_cases WHERE guild_id=1").fetchone()[0],1)
        db.close()

    def test_case_manager_displays_paged_actions_without_exceeding_discord_rows(self):
        view=CaseManagerView(self.host(),1,5)
        self.assertEqual(len(view.case_select.options),1)
        self.assertTrue(view.case_select.disabled)
        self.assertTrue(view.finish.disabled)
        self.assertTrue(view.delete_one.disabled)
        self.assertLessEqual(max(item.row or 0 for item in view.children),4)

    async def test_rejoin_restores_only_safe_verified_role_and_consumes_snapshot(self):
        perms=NS(administrator=False,manage_guild=False,manage_roles=False,
                 ban_members=False,kick_members=False,moderate_members=False)
        class Role:
            id=44
            managed=False
            permissions=perms
            def is_default(self): return False
            def __ge__(self,other): return False
        role=Role()
        state={"present":False}
        class Guild:
            id=1
            me=NS(top_role=NS(),guild_permissions=NS(manage_roles=True,view_audit_log=True))
            def get_role(self,rid): return role if rid==44 else None
            def get_member(self,uid): return member if state["present"] else None
            async def audit_logs(self,**kwargs):
                if False:
                    yield None
        guild=Guild()
        member=NS(bot=False,id=70,guild=guild,roles=[role],add_roles=AsyncMock(),
                  remove_roles=AsyncMock())
        with patch("member_rejoin_restore.asyncio.sleep",new=AsyncMock()):
            await capture_departure(member,connect=self.connect,enabled=lambda gid:True,
                                    personality_ids=lambda gid:{44},
                                    verify_role_id=lambda gid:55,is_verified=lambda m:True,
                                    audit_action=NS(kick="kick",ban="ban"))
            self.assertEqual(saved_role(self.connect,1,70),44)
            state["present"]=True
            self.assertTrue(await restore_join(
                member,connect=self.connect,enabled=lambda gid:True,
                personality_ids=lambda gid:{44},verify_role_id=lambda gid:55,
                sin_role_id=lambda gid:0))
        member.add_roles.assert_awaited_once()
        self.assertIsNone(saved_role(self.connect,1,70))

    def test_pending_roles_can_only_be_loaded_for_their_guild(self):
        host=self.host()
        pending_set(host,1,40,[15,11])
        self.assertEqual(pending_get(host,1,40),[11,15])
        self.assertEqual(pending_get(host,2,40),[])
        pending_set(host,1,40,[])
        self.assertFalse(pending_get(host,1,40))


if __name__=="__main__":
    unittest.main()
