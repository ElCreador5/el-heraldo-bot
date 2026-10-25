import unittest
from pathlib import Path

SRC = (Path(__file__).resolve().parents[1] / 'custodio_reports.py').read_text('utf-8')

class LiteralReportTests(unittest.TestCase):
    def test_private_destination(self):
        self.assertIn('_get_safe_existing(guild, report_channel_id)', SRC)
        self.assertIn('allowed_mentions=discord.AllowedMentions.none()', SRC)

    def test_copy_survives_original_deletion(self):
        self.assertIn('async def unlink_deleted_original(', SRC)
        self.assertIn('field.name != "Original disponible"', SRC)
        self.assertIn('embed.add_field(name=field.name, value=field.value', SRC)

if __name__ == '__main__':
    unittest.main()
