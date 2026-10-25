"""Pruebas de observación sin supervisión real ni sanciones."""
import unittest
from custodio_observe import ObserveBuffer, MAX_TRACKED_PATTERNS


class ObserveTests(unittest.TestCase):
    def test_no_explicit_rule_never_observes(self):
        detector = ObserveBuffer()
        for i in range(1, 6):
            self.assertIsNone(detector.inspect(guild_id=1,channel_id=2,actor_id=3,
                message_id=i,timestamp=i,content="Mensaje repetido"))

    def test_identical_text_requires_three_distinct_messages(self):
        detector = ObserveBuffer()
        args=dict(guild_id=1,channel_id=2,actor_id=3,content="Hola a todos",approved_rule_number=2)
        self.assertIsNone(detector.inspect(**args,message_id=1,timestamp=1))
        self.assertIsNone(detector.inspect(**args,message_id=2,timestamp=2))
        event=detector.inspect(**args,message_id=3,timestamp=3)
        self.assertEqual(event.kind,"identical_text_repetition")
        self.assertEqual(event.action,"report_only")
        self.assertEqual(event.rule_number,2)
        self.assertIsNone(detector.inspect(**args,message_id=3,timestamp=4))

    def test_bounded_patterns(self):
        detector = ObserveBuffer()
        for actor in range(1, MAX_TRACKED_PATTERNS + 11):
            detector.inspect(guild_id=1, channel_id=2, actor_id=actor,
                             message_id=actor, timestamp=actor,
                             content="Texto repetido", approved_rule_number=1)
        self.assertLessEqual(len(detector._events), MAX_TRACKED_PATTERNS)

    def test_time_window_and_actor_boundaries(self):
        detector=ObserveBuffer()
        base=dict(guild_id=1,channel_id=2,content="Texto repetido",approved_rule_number=1)
        self.assertIsNone(detector.inspect(**base,actor_id=3,message_id=1,timestamp=0))
        self.assertIsNone(detector.inspect(**base,actor_id=4,message_id=2,timestamp=1))
        self.assertIsNone(detector.inspect(**base,actor_id=3,message_id=3,timestamp=100))

if __name__ == "__main__":
    unittest.main()
