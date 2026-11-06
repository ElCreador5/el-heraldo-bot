"""Offline checks for the level-up-style role synchronization panel PNG."""
from io import BytesIO
import unittest

from PIL import Image

from sync_progress_card import HEIGHT, WIDTH, render_sync_card


def labels():
    return {
        "count": "{checked} / {total} miembros revisados",
        "unknown_count": "{checked} miembros revisados",
        "estimated": "Progreso estimado",
        "unknown": "Total no disponible",
        "added": "agregados",
        "removed": "retirados",
        "failed": "errores",
    }


def card(**overrides):
    values = {
        "title": "Conexiones de roles",
        "state": "Sincronizando miembros",
        "checked": 575,
        "total": 923,
        "added": 4,
        "removed": 3,
        "failed": 1,
        "labels": labels(),
    }
    values.update(overrides)
    return render_sync_card(**values)


class SyncProgressCardTests(unittest.TestCase):
    def test_png_dimensions_and_rounded_progress_track(self):
        data = card()
        self.assertLess(len(data), 250_000)
        image = Image.open(BytesIO(data)).convert("RGB")
        self.assertEqual(image.size, (WIDTH, HEIGHT))
        # Rounded track has a blue fill on the left and gray on the right.
        self.assertEqual(image.getpixel((100, 194)), (104, 117, 247))
        self.assertEqual(image.getpixel((891, 194)), (60, 62, 76))
        self.assertNotEqual(image.getpixel((0, 0)), image.getpixel((200, 100)))

    def test_unknown_total_has_moving_segment_without_percent(self):
        unknown = Image.open(BytesIO(card(total=None))).convert("RGB")
        stale = Image.open(BytesIO(card(checked=1200))).convert("RGB")
        self.assertEqual(unknown.size, (WIDTH, HEIGHT))
        self.assertEqual(stale.size, (WIDTH, HEIGHT))
        # An indeterminate indicator is not a full or empty bar.
        colors = [unknown.getpixel((x, 194)) for x in range(60, 900, 25)]
        self.assertIn((104, 117, 247), colors)
        self.assertIn((60, 62, 76), colors)

    def test_all_locales_and_zero_member_bars_render(self):
        for state, title in [
            ("Sincronizando miembros", "Conexiones de roles"),
            ("Syncing members", "Role connections"),
            ("Sincronizando membros", "Conexões de cargos"),
        ]:
            data = card(title=title, state=state, checked=0)
            self.assertTrue(data.startswith(bytes.fromhex("89504e470d0a1a0a")))


if __name__ == "__main__":
    unittest.main()
