"""Contrato EJECUTABLE de diseño de Modo Custodio.

No importa bot.py, no se conecta a Discord ni ejecuta sanciones.
Estas pruebas validan una matriz de escenarios aprobados; NO validan todavía
el motor de Custodio (pendiente de implementación y adaptador de integración).
"""
import unittest

SCENARIOS = {
    "imagen_repetida_horas": {
        "rules_active": True, "rule_covers_behavior": True,
        "evidence_sufficient": False, "action": "none", "warnings": 0,
        "delete": False, "automatic": False,
    },
    "saturacion_colectiva": {
        "rules_active": True, "rule_covers_behavior": True,
        "evidence_sufficient": True, "action": "educational_notice",
        "warnings": 0, "delete": False, "automatic": True,
        "grouped_incident": True, "notice_count": 1,
    },
    "discusion_ambigua": {
        "rules_active": True, "rule_covers_behavior": True,
        "evidence_sufficient": False, "action": "human_review",
        "warnings": 0, "delete": False, "automatic": False,
    },
    "reconocimiento_de_error": {
        "rules_active": True, "rule_covers_behavior": True,
        "evidence_sufficient": True, "action": "educational_close",
        "warnings": 0, "delete": False, "automatic": True,
        "acknowledgement": True,
    },
    "reincidencia_reconocida_autorizada": {
        "rules_active": True, "rule_covers_behavior": True,
        "evidence_sufficient": True, "action": "formal_warning",
        "warnings": 2, "delete": False, "automatic": True,
        "acknowledgement": True, "repeat_verified": True,
        "double_warning_authorized": True, "incident_count": 1,
    },
    "rol_exento": {
        "rules_active": True, "rule_covers_behavior": True,
        "evidence_sufficient": True, "action": "human_review",
        "warnings": 0, "delete": False, "automatic": False,
        "exempt": True,
    },
    "apelacion_aceptada": {
        "rules_active": True, "rule_covers_behavior": True,
        "evidence_sufficient": True, "action": "void_warning",
        "warnings": 0, "delete": False, "automatic": False,
        "prior_warning_active_after": False,
    },
    "discord_reintento": {
        "rules_active": True, "rule_covers_behavior": True,
        "evidence_sufficient": True, "action": "no_second_execution",
        "warnings": 0, "delete": False, "automatic": False,
        "incident_count": 1, "execution_count": 1,
    },
    "sancion_cumplida": {
        "rules_active": True, "rule_covers_behavior": True,
        "evidence_sufficient": True, "action": "mark_linked_warnings_served",
        "warnings": 0, "delete": False, "automatic": False,
        "served_cycle_active": 0, "served_cycle_history": 5,
    },
    "reglas_inactivas": {
        "rules_active": False, "rule_covers_behavior": True,
        "evidence_sufficient": True, "action": "none",
        "warnings": 0, "delete": False, "automatic": False,
    },
    "norma_sin_cobertura": {
        "rules_active": True, "rule_covers_behavior": False,
        "evidence_sufficient": True, "action": "human_review",
        "warnings": 0, "delete": False, "automatic": False,
    },
}


class CustodioDesignContractTests(unittest.TestCase):
    """Comprueba la coherencia del CONTRATO, no del runtime del bot."""

    def test_all_approved_situations_have_a_scenario(self):
        self.assertGreaterEqual(len(SCENARIOS), 8)
        self.assertTrue({"imagen_repetida_horas", "saturacion_colectiva",
                         "discusion_ambigua", "reconocimiento_de_error",
                         "rol_exento", "apelacion_aceptada", "discord_reintento",
                         "sancion_cumplida"}.issubset(SCENARIOS))

    def test_no_automatic_penalty_without_clear_active_rule_and_evidence(self):
        for name, case in SCENARIOS.items():
            with self.subTest(name=name):
                if not (case["rules_active"] and case["rule_covers_behavior"]
                        and case["evidence_sufficient"]):
                    self.assertEqual(case["warnings"], 0)
                    self.assertFalse(case["delete"])

    def test_exempt_role_is_not_automatically_sanctioned(self):
        for name, case in SCENARIOS.items():
            if case.get("exempt"):
                with self.subTest(name=name):
                    self.assertFalse(case["automatic"])
                    self.assertEqual(case["warnings"], 0)

    def test_double_warning_is_conditional_and_single_incident(self):
        for name, case in SCENARIOS.items():
            if case["warnings"] > 1:
                with self.subTest(name=name):
                    self.assertTrue(case.get("repeat_verified"))
                    self.assertTrue(case.get("double_warning_authorized"))
                    self.assertEqual(case.get("incident_count"), 1)

    def test_collective_notices_and_discord_retries_do_not_duplicate(self):
        self.assertEqual(SCENARIOS["saturacion_colectiva"]["notice_count"], 1)
        self.assertEqual(SCENARIOS["discord_reintento"]["execution_count"], 1)

    def test_served_warnings_keep_history_but_not_active_points(self):
        case = SCENARIOS["sancion_cumplida"]
        self.assertEqual(case["served_cycle_active"], 0)
        self.assertEqual(case["served_cycle_history"], 5)

    @unittest.skip("Aceptación real en Discord pendiente; el motor y los adaptadores se verifican sin red en test_custodio_runtime_integration y test_custodio_discipline_integration")
    def test_live_custodio_engine_contract(self):
        pass


if __name__ == "__main__":
    unittest.main()
