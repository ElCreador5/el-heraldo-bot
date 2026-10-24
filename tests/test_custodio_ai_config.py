"""Regresiones de configuración IA: sin red, modelos, Discord ni DB."""
import unittest

from custodio_ai_config import CustodioAIConfig, prepare_rule_analysis


class CustodioAIConfigTests(unittest.TestCase):
    def test_safe_defaults(self):
        config = CustodioAIConfig().validate()
        self.assertFalse(config.enabled)
        self.assertFalse(config.allow_sanctions)
        self.assertTrue(config.require_human_approval)

    def test_no_background_analysis(self):
        with self.assertRaises(ValueError):
            CustodioAIConfig(allow_background_analysis=True).validate()

    def test_no_access_to_messages_or_sanctions(self):
        for override in ({"allow_messages": True}, {"allow_sanctions": True},
                         {"allow_auto_rule_edit": True}, {"allow_user_profiles": True}):
            with self.subTest(override=override), self.assertRaises(ValueError):
                CustodioAIConfig(**override).validate()

    def test_no_enable_without_verified_provider(self):
        with self.assertRaises(ValueError):
            CustodioAIConfig(enabled=True).validate()

    def test_activation_never_happens_automatically(self):
        conf = CustodioAIConfig()
        self.assertEqual(prepare_rule_analysis(config=conf, rules_active=True,
                         administrator_requested=False, text="No spam")["status"], "blocked")

    def test_rules_must_be_active(self):
        response = prepare_rule_analysis(config=CustodioAIConfig(),
                    rules_active=False, administrator_requested=True, text="No spam")
        self.assertEqual(response["reason"], "server_rules_inactive")

    def test_manual_fallback_without_model(self):
        response = prepare_rule_analysis(config=CustodioAIConfig(),
                    rules_active=True, administrator_requested=True, text="No spam")
        self.assertEqual(response["status"], "manual_review")

    def test_enabled_config_prepares_but_does_not_execute(self):
        conf = CustodioAIConfig(enabled=True, provider="local", model="candidate").validate()
        response = prepare_rule_analysis(config=conf, rules_active=True,
                        administrator_requested=True, text="No spam")
        self.assertEqual(response["status"], "prepared_not_executed")
        self.assertTrue(response["approval_required"])

    def test_long_text_rejected(self):
        conf = CustodioAIConfig(enabled=True, provider="local", model="candidate")
        response = prepare_rule_analysis(config=conf, rules_active=True,
                        administrator_requested=True, text="X" * 6001)
        self.assertEqual(response["reason"], "rules_too_long")


if __name__ == "__main__":
    unittest.main()
