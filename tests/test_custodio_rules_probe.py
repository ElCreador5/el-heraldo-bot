import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "tools" / "custodio_rules_probe.py"
spec = importlib.util.spec_from_file_location("custodio_rules_probe", MODULE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

class RulesProbeTests(unittest.TestCase):
    def test_reads_only_terms_without_other_question_values(self):
        paths = []
        def reader(path, token):
            paths.append(path)
            if path.endswith("/member-verification"):
                return 200, {"form_fields": [
                    {"field_type": "TERMS", "values": ["Regla A", "Regla B"]},
                    {"field_type": "TEXT_INPUT", "values": ["dato privado"]},
                ]}
            return 200, {"features": ["MEMBER_VERIFICATION_GATE_ENABLED"]}
        result = probe.evaluate("test-token", reader=reader)
        self.assertTrue(result["screening_enabled"])
        self.assertEqual(result["rules"], ["Regla A", "Regla B"])
        self.assertEqual(result["rules_count"], 2)
        self.assertEqual(len(paths), 2)
        self.assertTrue(all(p.startswith("/guilds/1557230352802644040") for p in paths))

    def test_rejected_endpoint_does_not_invent_rules(self):
        def reader(path, token):
            if path.endswith("/member-verification"):
                return 403, {"code": 50013}
            return 200, {"features": ["COMMUNITY"]}
        result = probe.evaluate("test-token", reader=reader)
        self.assertFalse(result["screening_enabled"])
        self.assertEqual(result["verification_http"], 403)
        self.assertEqual(result["discord_error_code"], 50013)
        self.assertEqual(result["rules"], [])

    def test_unavailable_guild_and_api_report_unknown(self):
        result = probe.evaluate("test-token", reader=lambda path, token: (0, {}))
        self.assertIsNone(result["screening_enabled"])
        self.assertEqual(result["rules_count"], 0)

if __name__ == "__main__":
    unittest.main()
