"""Señales nuevas y límites del corpus: evidencia sintética, nunca culpabilidad."""
import json
import unittest
from custodio_detection import KINDS,LocalDetector,mismatched_link
from custodio_evaluation import CORPUS,classify,evaluate
from custodio_taxonomy import BEHAVIORS


class LocalSignalTests(unittest.TestCase):
    def signal(self,detector,number,**fields):
        return detector.inspect(guild_id=1,channel_id=2,actor_id=3,message_id=number,
            now=float(number),content=fields.pop('content',''),kinds=KINDS,**fields)

    def test_single_celebration_and_quotes_cannot_trigger_character_or_emoji_flood(self):
        for text in ['🎉'*80,'x'*180]:
            detector=LocalDetector()
            self.assertFalse(self.signal(detector,1,content=text))
            expected='emoji_flood' if text.startswith('🎉') else 'character_flood'
            self.assertIn(expected,{d.kind for d in self.signal(detector,2,content=text)})
            detector=LocalDetector()
            for number in range(1,8):
                self.assertFalse(self.signal(detector,number,content='> '+text))

    def test_stickers_and_attachments_require_own_bounded_repetition(self):
        detector=LocalDetector()
        for number in range(1,4):
            result=self.signal(detector,number,sticker_ids=[99],attachment_count=8)
        self.assertEqual({d.kind for d in result},{'sticker_repeat','attachment_flood'})
        self.assertEqual(detector.events[-1].stickers,{99})
        self.assertEqual(detector.events[-1].attachments,8)
        self.assertFalse(self.signal(detector,4,sticker_ids=[99],attachment_count=8))

    def test_directed_mentions_require_repeated_target_from_the_same_actor(self):
        detector=LocalDetector()
        for number in range(1,6):
            result=self.signal(detector,number,mention_ids=[77])
        self.assertEqual([d.kind for d in result],['directed_mentions'])
        detector=LocalDetector()
        for number in range(1,8):
            self.assertFalse(self.signal(detector,number,mention_ids=[70+number]))

    def test_masked_destination_is_a_local_difference_without_fetching_or_fraud_accusation(self):
        self.assertTrue(mismatched_link('[https://one.test](https://two.test/page)'))
        self.assertFalse(mismatched_link('[https://one.test](https://www.one.test/page)'))
        self.assertFalse(mismatched_link('[Documentation](https://one.test/page)'))
        for text in ['`[https://one.test](https://two.test)`','> [https://one.test](https://two.test)']:
            self.assertFalse(self.signal(LocalDetector(),1,content=text))

    def test_new_metadata_limits_fail_before_becoming_history(self):
        for fields in [{'sticker_ids':list(range(1,5))},{'mention_ids':[True]},
                       {'attachment_count':11},{'attachment_count':True}]:
            detector=LocalDetector()
            with self.assertRaises(ValueError):self.signal(detector,1,**fields)
            self.assertFalse(detector.events)

    def test_evaluation_runs_all_categories_languages_and_sensitivities_and_keeps_known_misses(self):
        corpus=json.loads(CORPUS.read_text());report=evaluate(corpus)
        groups=report['by_category_locale_sensitivity']
        self.assertEqual({r['category'] for r in groups},set(BEHAVIORS))
        self.assertEqual({r['locale'] for r in groups},{'es-419','en-US','pt-BR'})
        self.assertEqual({r['sensitivity'] for r in groups},{'conservative','balanced','strict'})
        self.assertEqual(report['totals']['fp'],0)
        self.assertGreater(report['totals']['tp'],0)
        self.assertGreater(report['totals']['fn'],0)
        self.assertGreater(report['totals']['human_review'],0)
        self.assertTrue(all(r['recall'] is None for r in groups if not BEHAVIORS[r['category']].kinds))
        misses=[r for r in report['results'] if r['result']=='fn']
        self.assertTrue(all(r['known_limit']=='outside_history_window' for r in misses),misses)


if __name__=='__main__':unittest.main()
