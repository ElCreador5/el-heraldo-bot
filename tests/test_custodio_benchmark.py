"""Garantías de la batería de evaluación: no hay entrenamiento automático."""
import unittest

from custodio_benchmark import PUBLIC_CORPORA, LAB_CASES, evaluate_predictions


class CustodioBenchmarkTests(unittest.TestCase):
    def test_sources_are_public_labeled_and_license_declared(self):
        self.assertGreaterEqual(len(PUBLIC_CORPORA), 3)
        for source in PUBLIC_CORPORA:
            self.assertTrue(source["url"].startswith("https://"))
            self.assertIn(source["license"], {"CC0", "CC-BY-4.0"})
            self.assertIn(source["language"], {"en", "es"})

    def test_benchmark_contains_legitimate_ambiguous_and_suspicious_examples(self):
        labels = {c.outcome for c in LAB_CASES}
        self.assertEqual(labels, {"clear", "suspected", "ambiguous"})
        self.assertEqual(len({c.reference for c in LAB_CASES}), len(LAB_CASES))
        self.assertTrue(any(c.category == "report" for c in LAB_CASES))
        self.assertTrue(any(c.category == "appeal" for c in LAB_CASES))
        self.assertTrue(any(c.category == "repetition" for c in LAB_CASES))

    def test_perfect_predictions_have_no_false_positives(self):
        predictions = {c.reference: c.outcome for c in LAB_CASES}
        report = evaluate_predictions(predictions)
        self.assertEqual(report["correct"], report["samples"])
        self.assertEqual(report["false_positive"], 0)
        self.assertEqual(report["missed_suspected"], 0)

    def test_overmoderating_legitimate_posts_is_counted(self):
        predictions = {c.reference: "suspected" for c in LAB_CASES}
        report = evaluate_predictions(predictions)
        self.assertGreater(report["false_positive"], 0)
        self.assertEqual(report["samples"], len(LAB_CASES))

    def test_incomplete_or_invalid_predictions_cannot_claim_success(self):
        with self.assertRaises(ValueError):
            evaluate_predictions({})
        predictions = {c.reference: c.outcome for c in LAB_CASES}
        predictions[LAB_CASES[0].reference] = "ban"
        with self.assertRaises(ValueError):
            evaluate_predictions(predictions)


if __name__ == "__main__":
    unittest.main()
