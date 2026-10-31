"""Comprobaciones de la activación de registros al asignar el canal oficial."""
import ast
from pathlib import Path
import unittest


SOURCE = ast.parse((Path(__file__).resolve().parents[1] / "bot.py").read_text(encoding="utf-8"))


def get_function(name):
    return next(node for node in SOURCE.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == name)


class TestLogChannelActivation(unittest.TestCase):
    def test_channel_setter_activa_todos_los_registros_de_miembros(self):
        setter = get_function("set_log_channel_id")
        loops = [node for node in ast.walk(setter) if isinstance(node, ast.For)]
        loops = [node for node in loops if isinstance(node.iter, ast.Name)
                 and node.iter.id == "MEMBER_LOG_EVENTS"]
        self.assertEqual(len(loops), 1)
        loop = loops[0]
        self.assertTrue(any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "guild_config_set"
            and len(node.args) >= 3
            and isinstance(node.args[2], ast.Constant)
            and node.args[2].value == "1"
            for node in ast.walk(loop)
        ))

    def test_eventos_conservan_canales_individuales(self):
        channel = get_function("log_member_channel_id")
        text = ast.unparse(channel)
        self.assertIn("log_member.channel.{event_key}", text)
        self.assertIn("get_log_channel_id(guild_id)", text)

    def test_configuracion_y_comando_usan_la_misma_activacion(self):
        apply = get_function("_setup_apply_system_channel")
        self.assertIn("set_log_channel_id(channel.id, guild.id)", ast.unparse(apply))
        confirm = next(node for node in SOURCE.body if isinstance(node, ast.ClassDef)
                       and node.name == "HeraldoLogChannelConfirmView")
        self.assertIn("set_log_channel_id(channel.id, self.guild_id)", ast.unparse(confirm))


if __name__ == "__main__":
    unittest.main()
