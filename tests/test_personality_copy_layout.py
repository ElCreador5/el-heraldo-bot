"""NH: contrato del texto y controles de Verificación de personalidad."""
import ast
from pathlib import Path
import unittest
SRC=(Path(__file__).resolve().parents[1]/"bot.py").read_text("utf-8")
TREE=ast.parse(SRC)
def get(name):
    return next(n for n in TREE.body if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name)
def body(name):
    return ast.get_source_segment(SRC,get(name))
class PersonalityCopyLayoutTests(unittest.TestCase):
    def test_public_wording_and_conditional_selection(self):
        text=SRC.split("ORIENTATION_EMBED_DETAILS = (",1)[1].split("# --- Tarjeta de condena",1)[0]
        for item in ("al miembro elegir cómo desea participar", "asociado a dicho emoji",
                     "Solo puede conservar una elección", "experiencia personalizada",
                     "no constituye una", "verificación de edad", "**¿Cómo funciona?**"):
            self.assertIn(item,text)
        self.assertIn("if not custom and not personality_allow_change(guild_id)",body("get_orientation_embed_details"))
    def test_admin_help_mentions_one_return_when_required(self):
        s=body("orientation_setup_summary")
        for t in ("**¿Cómo funciona?**", "**Obligatoriedad y reingreso**",
                  "invitación", "de un solo uso", "está activada y es obligatoria",
                  "moderadores y el dueño", "permisos heredados"):
            self.assertIn(t,s)
    def test_button_rows_and_order(self):
        view=get("HeraldoOrientationSetupView")
        b=[]
        for fn in view.body:
            if not isinstance(fn,ast.AsyncFunctionDef):continue
            for d in fn.decorator_list:
                if isinstance(d,ast.Call) and isinstance(d.func,ast.Attribute) and d.func.attr=="button":
                    args={kw.arg:kw.value for kw in d.keywords}
                    b.append((fn.name,ast.literal_eval(args["row"]),ast.literal_eval(args["label"]),args["style"].attr))
        self.assertEqual([x[0] for x in b],["back","activate","deactivate","edit_card","configure_times",
             "toggle_change","toggle_required","edit_dm","save_changes","discard_changes"])
        self.assertEqual([x[1] for x in b],[2,2,2,2,2,3,3,4,4,4])
        self.assertEqual(next(x[3] for x in b if x[0]=="save_changes"),"success")
        self.assertEqual(next(x[3] for x in b if x[0]=="discard_changes"),"danger")
        self.assertIn("Editar DM de recuperación",[x[2] for x in b])
    def test_reentry_still_only_in_automatic_personality(self):
        expel=body("expel")
        self.assertIn("not personality_required(member.guild.id)",expel)
        self.assertLess(expel.index("await send_recovery_dm"),expel.index("await heraldo_kick"))
        self.assertIn("max_uses=1",body("send_recovery_dm"))
    def test_exact_button_labels_are_preserved(self):
        view=get("HeraldoOrientationSetupView")
        actual={n.name:ast.literal_eval(next(kw.value for deco in n.decorator_list if isinstance(deco,ast.Call) and isinstance(deco.func,ast.Attribute) and deco.func.attr=="button" for kw in deco.keywords if kw.arg=="label")) for n in view.body if isinstance(n,ast.AsyncFunctionDef) and any(isinstance(d,ast.Call) and isinstance(d.func,ast.Attribute) and d.func.attr=="button" for d in n.decorator_list)}
        self.assertEqual(actual,{
            "back":"Volver","activate":"Activar","deactivate":"Desactivar",
            "edit_card":"Editar embed","toggle_change":"Cambiar elección",
            "toggle_required":"Expulsar si no elige","edit_dm":"Editar DM de recuperación",
            "configure_times":"Configurar tiempos",
            "save_changes":"Guardar cambios","discard_changes":"Descartar cambios"
        })
        self.assertIn("Cambiar elección: Sí (recomendado)",body("HeraldoOrientationSetupView"))
        self.assertIn("Expulsar si no elige: Sí",body("HeraldoOrientationSetupView"))
if __name__=="__main__":unittest.main()
