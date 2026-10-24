"""Pruebas de decisiones del simulador aislado; NO son pruebas de Discord."""
import unittest
from custodio_dry_run import CustodioDryRun, Scenario


class CustodioDryRunTests(unittest.TestCase):
    def setUp(self):
        self.engine = CustodioDryRun()

    def decide(self, ident, **options):
        return self.engine.evaluate(Scenario(incident_id=ident, **options))

    def test_imagen_aislada_no_es_spam_probado(self):
        d = self.decide("imagen-1", evidence_clear=False)
        self.assertEqual(d.action, "human_review")
        self.assertEqual(d.warning_points, 0)

    def test_oleada_colectiva_solo_aviso_autorizado(self):
        d = self.decide("oleada-1")
        self.assertEqual(d.action, "educational_notice")
        self.assertEqual(d.warning_points, 0)

    def test_discusion_ambigua_requiere_humano(self):
        self.assertTrue(self.decide("discusion", evidence_clear=False).review)

    def test_fue_un_error_cierre_educativo(self):
        d = self.decide("reconocido", requested="educational_close",
                        authorized_actions=("educational_close",), recognized_error=True)
        self.assertEqual(d.warning_points, 0)

    def test_doble_advertencia_solo_si_todos_los_requisitos(self):
        base = {"requested": "formal_warning",
                "authorized_actions": ("formal_warning",),
                "recognized_error": True, "repeated_conduct": True}
        self.assertEqual(self.decide("sin-aprobacion", **base).warning_points, 1)
        self.assertEqual(self.decide("con-aprobacion", double_warning_approved=True, **base).warning_points, 2)

    def test_exento_no_se_sanciona_automaticamente(self):
        d = self.decide("exento", exempt=True, requested="formal_warning",
                        authorized_actions=("formal_warning",))
        self.assertTrue(d.review)
        self.assertEqual(d.warning_points, 0)

    def test_apelacion_no_se_ejecuta_como_sancion(self):
        d = self.decide("apelacion", requested="void_warning",
                        authorized_actions=("void_warning",))
        self.assertTrue(d.review)

    def test_redelivery_no_repite_una_decision(self):
        original = self.decide("mismo-incidente")
        retry = self.decide("mismo-incidente", requested="formal_warning",
                            authorized_actions=("formal_warning",))
        self.assertIs(original, retry)

    def test_cumplimiento_es_administrativo_no_sancion_automatica(self):
        d = self.decide("sancion-terminada", requested="mark_linked_warnings_served",
                        authorized_actions=("mark_linked_warnings_served",))
        self.assertTrue(d.review)

    def test_reglas_inactivas_impiden_accion(self):
        self.assertEqual(self.decide("sin-reglas", rules_active=False).action, "none")

    def test_regla_no_cubre_conducta(self):
        self.assertTrue(self.decide("no-cubierto", rule_applies=False).review)

    def test_eliminacion_solo_con_autorizacion(self):
        denied = self.decide("borrado-denegado", requested="delete_message")
        allowed = self.decide("borrado-autorizado", requested="delete_message",
                              authorized_actions=("delete_message",))
        self.assertTrue(denied.review)
        self.assertEqual(allowed.action, "delete_message")

    def test_incidente_sin_id_es_rechazado(self):
        with self.assertRaises(ValueError):
            self.decide("")


if __name__ == "__main__":
    unittest.main()
