"""Protocolo de ACK: ejecuta el despacho real de discord.py sin Gateway."""
from i18n_source_helpers import source_text as _source_text
import asyncio
import inspect
import itertools
import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock

import discord
import setup_interactions as runtime


class TransportError(Exception):
    code = 10062


class Response:
    def __init__(self, parent):
        self._parent = parent
        self.done = False

    def is_done(self):
        return self.done

    async def defer(self, **kw):
        if self.done:
            raise AssertionError("Doble ACK")
        self._parent.events.append("ack")
        self.done = True

    async def send_message(self, text=None, **kw):
        if self.done:
            raise AssertionError("Respuesta inicial duplicada")
        self.done = True
        self._parent.events.append(("initial", text, kw))

    async def edit_message(self, **kw):
        if self.done:
            raise AssertionError("Edición inicial duplicada")
        self.done = True
        self._parent.events.append(("initial_edit", kw))

    async def send_modal(self, modal):
        if self.done:
            raise AssertionError("El ACK consumió la respuesta del modal")
        self.done = True
        self._parent.events.append("modal")


class View(discord.ui.View):
    # Usar el cuerpo REAL de despacho, con sus checks y manejo de errores.
    _scheduled_task = inspect.unwrap(discord.ui.View._scheduled_task)

    def __init__(self):
        super().__init__(timeout=300)
        self.guild_id, self.owner_id = 901, 10
        self.errors = []

    async def on_error(self, interaction, error, item):
        self.errors.append(error)


class Modal:
    _scheduled_task = inspect.unwrap(discord.ui.Modal._scheduled_task)


runtime.install(NS(ui=NS(View=View, Modal=Modal), InteractionResponse=Response,
                   HTTPException=TransportError))
counter = itertools.count(10000)


def interaction(message_id=10):
    events = []
    i = NS(id=next(counter), guild_id=901, extras={}, events=events,
           data={}, message=NS(id=message_id))
    i.response = Response(i)
    async def edit(**kw):
        events.append(("edit", kw))
    async def send(*args, **kw):
        events.append(("followup", args, kw))
    i.edit_original_response = edit
    i.followup = NS(send=send)
    return i


def item(callback):
    return NS(callback=callback, _refresh_state=lambda *a: None,
              _run_checks=AsyncMock(return_value=True))


class SetupInteractionRuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_messages_menu_keeps_editors_without_create_message(self):
        from test_safety_regressions import b
        view = b.HeraldoMessagesSetupView(901, 10)
        options = {option.value for option in view.panel_select.options}
        self.assertNotIn("create_message", options)
        self.assertNotIn("autofeeds", options)
        self.assertTrue({
            "verification", "verify_dm", "suggestions", "honeypot",
            "condemnation", "logs", "templates",
        }.issubset(options))
        self.assertNotIn(
            "create_message", getattr(view, "_no_defer_select_values", ())
        )

    async def test_ack_precedes_checks_database_and_render_for_all_root_modules(self):
        from test_safety_regressions import b
        from test_ux_panel_matrix import guild_fixture, sqlite_snapshot
        guild = guild_fixture()
        baseline = sqlite_snapshot()
        for option in b.HeraldoSetupView(guild.id, 10).module_select.options:
            with self.subTest(module=option.value):
                view = b.HeraldoSetupView(guild.id, 10)
                i = interaction()
                i.guild, i.guild_id = guild, guild.id
                i.user = NS(id=10, guild_permissions=discord.Permissions(manage_guild=True))
                i.data = {"values": [option.value]}
                self.assertFalse(runtime.may_open_modal(view.select_module, view))
                await View._scheduled_task(view, item(view.select_module), i)
                self.assertEqual(i.events[0], "ack")
                self.assertEqual(i.events[-1][0], "edit")
                target = i.events[-1][1]["view"]
                self.assertTrue(runtime.is_setup_session(target), type(target).__name__)
                self.assertEqual(sqlite_snapshot(), baseline)

    async def test_checks_and_slow_work_run_after_ack_and_legacy_responses_route_once(self):
        view = View()
        i = interaction()
        async def check(current):
            current.events.append("permissions")
            return True
        async def callback(current):
            current.events.append("sqlite")
            await current.response.defer()  # Reconocido ya por el despacho.
            await current.response.edit_message(content="Guardado")
            await current.response.send_message("Resultado", ephemeral=True)
        view.interaction_check = check
        await view._scheduled_task(item(callback), i)
        self.assertFalse(view.errors)
        self.assertEqual(i.events[:3], ["ack", "permissions", "sqlite"])
        self.assertEqual([e[0] for e in i.events[3:]], ["edit", "followup"])

    async def test_modal_and_helper_modal_keep_initial_response(self):
        class ModalView(View):
            async def helper(self, current):
                await current.response.send_modal(object())
            async def open(self, current):
                await self.helper(current)
        view = ModalView()
        i = interaction()
        self.assertTrue(runtime.may_open_modal(view.open, view))
        await view._scheduled_task(item(view.open), i)
        self.assertEqual(i.events, ["modal"])
        self.assertFalse(view.errors)

    async def test_real_modal_openers_and_nested_setup_sessions_are_detected(self):
        import ast
        from pathlib import Path
        from test_safety_regressions import b
        source = _source_text(Path(__file__).resolve().parents[1] / 'bot.py', 'utf-8')
        count = 0
        for klass in ast.parse(source).body:
            if not isinstance(klass, ast.ClassDef):
                continue
            actual = getattr(b, klass.name, None)
            if actual is None or not issubclass(actual, discord.ui.View):
                continue
            for method in klass.body:
                if not isinstance(method, ast.AsyncFunctionDef):
                    continue
                if any(isinstance(n, ast.Attribute) and n.attr == "send_modal" for n in ast.walk(method)):
                    callback = getattr(actual, method.name, None)
                    self.assertTrue(runtime.may_open_modal(callback, NS()),
                                    f"{klass.name}.{method.name}")
                    count += 1
        self.assertGreater(count, 30)
        for link in ("parent", "editor", "parent_view", "setup_view"):
            self.assertTrue(runtime.is_setup_session(NS(**{link: NS(guild_id=901, owner_id=10)})))

    async def test_expired_panel_recovers_navigation_without_replaying_old_action(self):
        from unittest.mock import patch
        from test_safety_regressions import b
        i = interaction()
        i.type = discord.InteractionType.component
        i.guild = NS(id=901)
        i.user = NS(id=10, guild_permissions=discord.Permissions(manage_guild=True))
        i.message.author = NS(id=55)
        with patch.object(b.bot._connection, "user", NS(id=55)):
            await b.heraldo_expired_panel_reply(i)
        self.assertEqual(i.events[0][0], "initial")
        self.assertIn("No se ejecutó", i.events[0][1])
        self.assertIsInstance(i.events[0][2]["view"], b.HeraldoSetupView)
        handled = interaction()
        handled.type = discord.InteractionType.component
        handled.extras[runtime.STARTED_KEY] = True
        await b.heraldo_expired_panel_reply(handled)
        self.assertEqual(handled.events, [])

    async def test_repeated_click_during_work_and_same_event_never_reexecute(self):
        view = View()
        entered, release = asyncio.Event(), asyncio.Event()
        mutations = []
        async def callback(current):
            mutations.append(current.id)
            entered.set()
            await release.wait()
            await current.response.edit_message(content="Guardado")
        first, second = interaction(), interaction()
        task = asyncio.create_task(view._scheduled_task(item(callback), first))
        await entered.wait()
        await view._scheduled_task(item(callback), second)
        self.assertEqual(len(mutations), 1)
        self.assertEqual(second.events[0][0], "initial")
        release.set()
        await task
        await view._scheduled_task(item(callback), first)
        self.assertEqual(mutations, [first.id])
        self.assertFalse(runtime._busy)

    async def test_ack_failure_prevents_side_effect_and_releases_gate(self):
        view, i = View(), interaction()
        i.response.defer = AsyncMock(side_effect=TransportError())
        callback = AsyncMock()
        # AsyncMock is intentionally unknown: give it a normal callback wrapper.
        async def run(current):
            await callback(current)
        await view._scheduled_task(item(run), i)
        callback.assert_not_awaited()
        self.assertFalse(runtime._busy)

    async def test_non_setup_public_view_keeps_its_own_protocol(self):
        view, i = View(), interaction()
        del view.owner_id
        async def callback(current):
            await current.response.send_message("Público")
        await view._scheduled_task(item(callback), i)
        self.assertEqual(i.events[0][0], "initial")

    async def test_modal_submit_ack_precedes_refresh_permissions_and_storage(self):
        i = interaction()
        events = i.events
        async def check(current):
            events.append("permissions")
            return True
        async def submit(current):
            events.append("storage")
            await current.response.send_message("Borrador preparado", ephemeral=True)
        modal = NS(guild_id=901,
                   _refresh_timeout=lambda: events.append("refresh_timeout"),
                   _refresh=lambda *a: events.append("refresh"),
                   interaction_check=check, on_submit=submit,
                   on_error=AsyncMock(), stop=lambda: events.append("stop"))
        await Modal._scheduled_task(modal, i, [], {})
        self.assertEqual(events[0], "ack")
        self.assertLess(events.index("permissions"), events.index("storage"))
        self.assertEqual(events[-2][0], "followup")
        modal.on_error.assert_not_awaited()

    async def test_missing_verification_panel_is_status_without_repeated_startup_warning(self):
        from unittest.mock import patch
        from test_safety_regressions import b
        channel = NS(fetch_message=AsyncMock(side_effect=b.discord.NotFound(
            NS(status=404, reason="Not Found"), "Unknown Message")))
        guild = NS(id=901, get_channel=lambda cid: channel)
        with patch.object(b, "guild_config_get", return_value="20:30"), \
             patch.object(b, "guild_config_set") as write:
            status = await b.update_verify_panel(guild)
        self.assertIn("eliminado", status)
        self.assertIn("/verify", status)
        self.assertFalse(status.startswith(("No se pudo", "Advertencia:")))
        write.assert_not_called()


if __name__ == "__main__":
    unittest.main()
