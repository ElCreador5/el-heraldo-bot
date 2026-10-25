import unittest
from datetime import datetime, timezone
from heraldo_evidence import LiteralEvidence, make_evidence_embeds, discord_local_timestamp

class EvidenceTests(unittest.TestCase):
    def test_literal_content(self):
        e = LiteralEvidence(actor='member', guild='guild', channel='channel', occurred_at=datetime.now(timezone.utc), verbatim='Exact text', rule_number=1, rule_quote='Exact rule')
        result = make_evidence_embeds(e, footer='Lab')
        self.assertEqual(result[0].fields[-1].value, 'Exact text')
        self.assertEqual(result[-1].fields[0].value, 'Exact rule')

    def test_dynamic_timestamp_uses_actual_instant(self):
        from datetime import timedelta
        at_utc = datetime(2026, 10, 25, 18, 35, tzinfo=timezone.utc)
        at_local = at_utc.astimezone(timezone(timedelta(hours=-4)))
        self.assertEqual(discord_local_timestamp(at_utc), discord_local_timestamp(at_local))
        evidence = LiteralEvidence(actor='member', guild='guild', channel='channel',
                                   occurred_at=at_local, verbatim='Exact text')
        embeds = make_evidence_embeds(evidence, footer='Lab')
        displayed = next(field.value for field in embeds[0].fields if field.name == 'Fecha y hora')
        self.assertEqual(displayed, discord_local_timestamp(at_utc))
        self.assertTrue(displayed.startswith('<t:'))
        self.assertTrue(displayed.endswith(':F>'))

    def test_original_is_optional(self):
        e = LiteralEvidence(actor='member', guild='guild', channel='channel', occurred_at=datetime.now(timezone.utc), verbatim='Exact text', original_exists=False)
        result = make_evidence_embeds(e, footer='Lab')
        self.assertNotIn('Original disponible', [f.name for f in result[0].fields])

if __name__ == '__main__':
    unittest.main()
