"""La actualización retroactiva solo edita embeds antiguos del propio bot."""
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from bot_footer_reconcile import reconcile_existing_bot_footers

class Embed:
    type = "rich"
    def __init__(self, text, icon=""):
        self.footer = SimpleNamespace(text=text, icon_url=icon)
    def copy(self):
        return Embed(self.footer.text, self.footer.icon_url)
    def set_footer(self, *, text, icon_url=None):
        self.footer = SimpleNamespace(text=text, icon_url=icon_url)
    def __len__(self):
        return len(self.footer.text or "")

class Channel:
    def __init__(self, messages):
        self.id, self.messages, self.reads = 12, messages, 0
    def history(self, **kwargs):
        self.reads += 1
        async def iterator():
            for message in self.messages:
                yield message
        return iterator()

class FooterBackfillTests(unittest.IsolatedAsyncioTestCase):
    async def test_only_bot_is_edited_once_per_identity(self):
        name = "El Heraldo Labs 🧪"
        user = SimpleNamespace(id=42, name=name, display_avatar=SimpleNamespace(url="https://img/bot"))
        own = SimpleNamespace(author=SimpleNamespace(id=42),
            embeds=[Embed("El Heraldo's Labs 🧪 · Caso 7")], edit=AsyncMock())
        other = SimpleNamespace(author=SimpleNamespace(id=3),
            embeds=[Embed("Otro")], edit=AsyncMock())
        channel = Channel([own, other])
        guild = SimpleNamespace(id=9, text_channels=[channel], threads=[], me=None)
        bot = SimpleNamespace(user=user, guilds=[guild])
        markers = {}
        def stamp(embed, guild):
            embed.set_footer(text=name+" · Caso 7", icon_url="https://img/bot")
            return embed
        with patch("bot_footer_reconcile.asyncio.sleep", new=AsyncMock()):
            first = await reconcile_existing_bot_footers(bot, stamp, markers.get, markers.__setitem__)
            repeat = await reconcile_existing_bot_footers(bot, stamp, markers.get, markers.__setitem__)
        self.assertEqual(first, {"scanned": 2, "updated": 1, "errors": 0})
        self.assertEqual(repeat["scanned"], 0)
        self.assertEqual(own.edit.await_count, 1)
        other.edit.assert_not_awaited()
        self.assertEqual(channel.reads, 1)
        self.assertEqual(own.edit.await_args.kwargs["embeds"][0].footer.text, name+" · Caso 7")

    async def test_does_not_touch_link_previews(self):
        user = SimpleNamespace(id=42, name="Nombre", display_avatar=SimpleNamespace(url=""))
        embed = Embed("Texto")
        embed.type = "article"
        own = SimpleNamespace(author=SimpleNamespace(id=42), embeds=[embed], edit=AsyncMock())
        channel = Channel([own])
        guild = SimpleNamespace(id=9, text_channels=[channel], threads=[], me=None)
        result = await reconcile_existing_bot_footers(SimpleNamespace(user=user, guilds=[guild]),
                       lambda embed, guild: embed, lambda k: None, lambda k,v: None)
        self.assertEqual(result["updated"], 0)
        own.edit.assert_not_awaited()

if __name__ == "__main__":
    unittest.main()
