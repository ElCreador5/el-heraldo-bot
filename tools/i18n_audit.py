"""Inventario estático de literales de presentación y uso real de catálogos.

No confunde existencia de una clave con cobertura. Los contratos técnicos
revisados se registran por archivo, ámbito y hash; nuevas cadenas fallan CI.
"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HUMAN = re.compile(r'[áéíóúñÁÉÍÓÚÑ¿¡]|\b(?:el|la|los|las|para|sin|con|del|selecciona|guardar|volver|cancelar|cerrar|publicar|no|sí|activo|desactivado|miembro|canal|servidor)\b', re.I)
SQL = ('SELECT ', 'INSERT ', 'UPDATE ', 'DELETE ', 'CREATE ', 'ALTER ', 'PRAGMA ', 'WITH ', 'DROP ', 'ON ', 'WHERE ', 'AND ', 'FROM ', 'VALUES ', 'BEGIN ', 'ORDER BY ', ') VALUES ')


def findings(source, filename):
    tree = ast.parse(source)
    parents = {id(c): n for n in ast.walk(tree) for c in ast.iter_child_nodes(n)}
    result = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        value = node.value
        if re.match(r'^(?:text|setup|language|common|access|personality|suggestion)\.', value):
            continue
        natural = HUMAN.search(value) or re.search(r'[A-Za-zÁÉÍÓÚÑáéíóúñ]{2,}\s+[A-Za-zÁÉÍÓÚÑáéíóúñ]{2,}', value)
        owner = parents.get(id(node))
        if isinstance(owner, ast.keyword) and owner.arg in {'label', 'title', 'description', 'placeholder', 'content', 'text'}:
            natural = natural or re.search(r'[A-Za-zÁÉÍÓÚÑáéíóúñ]{2,}', value)
        if not natural or value.lstrip().startswith(SQL):
            continue
        if len(value) < 2:
            continue
        parent = parents.get(id(node))
        if isinstance(parent, ast.Expr):
            continue
        if isinstance(parent, ast.Dict) and node in parent.keys:
            continue
        ancestors, current = [], parent
        while current is not None:
            ancestors.append(current)
            current = parents.get(id(current))
        calls = [n for n in ancestors if isinstance(n, ast.Call)]
        call_names = [ast.unparse(n.func) for n in calls]
        if any(name == 'print'
               or name in {'re.compile', 're.sub', 're.search', 're.match', 're.fullmatch', 're.findall', 're.split'} for name in call_names):
            continue
        # Discord's global command schema is not a per-server message.
        if any(name.endswith(('.command', '.describe', '.Group', '.Choice')) for name in call_names):
            continue
        scope = '.'.join(n.name for n in reversed(ancestors)
                         if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)))
        fingerprint = hashlib.sha256((filename+'\0'+scope+'\0'+value).encode()).hexdigest()[:20]
        result.append({'id': fingerprint, 'file': filename, 'scope': scope, 'line': node.lineno, 'text': value})
    return result


def audit(root=ROOT):
    found = []
    used = set()
    for file in sorted(root.glob('*.py')):
        if file.name.startswith('test') or file.name == 'heraldo_i18n.py':
            continue
        raw = file.read_text(encoding='utf-8')
        found.extend(findings(raw, file.name))
        for node in ast.walk(ast.parse(raw)):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value.startswith(('text.', 'setup.', 'language.', 'common.', 'access.', 'personality.', 'suggestion.', 'input.', 'footer.')):
                    used.add(node.value)
    return {'literals': found, 'used_keys': sorted(used)}


if __name__ == '__main__':
    report = audit()
    approved = json.loads((ROOT/'locales/technical_literals.json').read_text()) if (ROOT/'locales/technical_literals.json').exists() else {}
    unresolved = [x for x in report['literals'] if x['id'] not in approved]
    print(json.dumps({'used_keys': len(report['used_keys']), 'unresolved_literals': unresolved}, ensure_ascii=False, indent=2))
    raise SystemExit(bool(unresolved))
