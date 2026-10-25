import unittest
from datetime import datetime, timezone
from heraldo_evidence import LiteralEvidence, make_evidence_embeds

class EvidenceTests(unittest.TestCase):
    def test_literal_content(self):
        e = LiteralEvidence(actor='member', guild='guild', channel='channel', occurred_at=datetime.now(timezone.utc), verbatim='Exact text', rule_number=1, rule_quote='Exact rule')
        result = make_evidence_embeds(e, footer='Lab')
        self.assertEqual(result[0].fields[-1].value, 'Exact text')
        self.assertEqual(result[-1].fields[0].value, 'Exact rule')

    def test_original_is_optional(self):
        e = LiteralEvidence(actor='member', guild='guild', channel='channel', occurred_at=datetime.now(timezone.utc), verbatim='Exact text', original_exists=False)
        result = make_evidence_embeds(e, footer='Lab')
        self.assertNotIn('Original disponible', [f.name for f in result[0].fields])

if __name__ == '__main__':
    unittest.main()
