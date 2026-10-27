"""Fichas de investigación: procedencia, límites y capacidad declarada verificable."""
import json
from pathlib import Path
import unittest
from custodio_detection import KINDS

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'data/custodio_taxonomy.json').read_text())


class TaxonomyTests(unittest.TestCase):
    def test_every_entry_has_a_stable_id_and_complete_reviewable_record(self):
        required = {'id','version','name','family','description','positive_synthetic_example',
                    'negative_synthetic_example','observable_signals','context_and_polysemy',
                    'reasonable_exceptions','applicable_languages','events_permissions',
                    'required_rule','method','threshold_context','resource_cost','privacy',
                    'false_positives','false_negatives','justified_confidence','capability',
                    'automatic_action','human_review_required','implementation','sources'}
        identifiers = [row['id'] for row in DATA['behaviors']]
        self.assertTrue(identifiers)
        self.assertEqual(len(identifiers), len(set(identifiers)))
        for row in DATA['behaviors']:
            with self.subTest(behavior=row['id']):
                self.assertTrue(required <= set(row))
                self.assertTrue(all(row[key] not in ('', [], None) for key in required))
                self.assertEqual(set(row['name']), {'es-419','en-US','pt-BR'})
                self.assertTrue(set(row['sources']) <= set(DATA['source_types']))

    def test_existing_signal_claims_match_implemented_mechanisms(self):
        for row in DATA['behaviors']:
            if row['implementation'] == 'existing_signal':
                self.assertTrue(set(row['method']) <= KINDS, row['id'])
            if row['implementation'] == 'review_only':
                self.assertEqual(row['method'], ['review_only'])
                self.assertEqual(row['automatic_action'], 'Ninguna; revisión humana.')

    def test_observation_never_claims_automatic_sanctions_or_semantic_certainty(self):
        for row in DATA['behaviors']:
            self.assertIs(row['human_review_required'], True, row['id'])
            if row['implementation'] != 'review_only':
                self.assertIn('sin sanción automática', row['automatic_action'])
                self.assertIn('no prueba culpabilidad', row['justified_confidence'])

    def test_documented_sources_have_distinct_evidence_types_and_public_urls(self):
        kinds = set()
        for source in DATA['source_types'].values():
            self.assertTrue(source['url'].startswith('https://'))
            self.assertTrue(source['use'])
            kinds.add(source['type'])
        self.assertIn('estudio primario', kinds)
        self.assertIn('experiencia pública ilustrativa', kinds)
        self.assertTrue(any('oficial' in kind for kind in kinds))
