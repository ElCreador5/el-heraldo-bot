"""Inventario estático reproducible. No importa el bot ni se conecta a Discord."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inventory():
    result = {'scope': 'Código Python versionado en raíz y pruebas; sin ejecutar el bot.',
              'symbols': [], 'interaction_sites': [], 'tests': []}
    for path in sorted(ROOT.glob('*.py')) + sorted((ROOT / 'tests').glob('test_*.py')):
        source = path.read_text(encoding='utf-8')
        tree = ast.parse(source)
        relative = path.relative_to(ROOT).as_posix()
        testing = path.name.startswith('test_')

        def visit(node, parents=()):
            is_definition = isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            next_parents = parents
            if is_definition:
                name = '.'.join((*parents, node.name))
                decorators = [ast.unparse(x) for x in node.decorator_list]
                bases = [ast.unparse(x) for x in node.bases] if isinstance(node, ast.ClassDef) else []
                tags = []
                if any('.command(' in x or '.context_menu(' in x for x in decorators):
                    tags.append('command')
                if any('.button(' in x or '.select(' in x for x in decorators):
                    tags.append('component_callback')
                if any('.listen(' in x or x.endswith('.event') for x in decorators):
                    tags.append('event')
                if any('tasks.loop(' in x for x in decorators):
                    tags.append('scheduled_loop')
                if any('View' in x or 'Modal' in x for x in bases):
                    tags.append('view_or_modal')
                if node.name in ('on_submit', 'interaction_check', 'on_timeout', 'on_error'):
                    tags.append('interaction_hook')
                entry = dict(file=relative, line=node.lineno, name=name, tags=tags,
                             decorators=decorators, bases=bases)
                if testing:
                    if node.name.startswith('test_'):
                        result['tests'].append(entry)
                else:
                    result['symbols'].append(entry)
                next_parents = (*parents, node.name)
            if not testing and isinstance(node, ast.Call):
                function = ast.unparse(node.func)
                if any(x in function for x in ('discord.ui.', 'create_task', 'add_view', 'add_listener', 'add_command')):
                    result['interaction_sites'].append(dict(file=relative, line=node.lineno,
                        owner='.'.join(parents), call=function))
            for child in ast.iter_child_nodes(node):
                visit(child, next_parents)
        visit(tree)
    return result


if __name__ == '__main__':
    data = inventory()
    folder = ROOT / 'audit'
    folder.mkdir(exist_ok=True)
    (folder / 'INVENTARIO.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    selected = [x for x in data['symbols'] if x['tags']]
    lines = ['# Inventario de superficies de El Heraldo', '',
             'Generado por `python tools/audit_inventory.py`. Las líneas corresponden al código de esta rama.',
             'Incluye todas las definiciones y sitios dinámicos en INVENTARIO.json. Una referencia de prueba no acredita cobertura ni ejecución en Discord.', '',
             '| Archivo:línea | Símbolo | Tipo |', '| --- | --- | --- |']
    lines += [f"| {x['file']}:{x['line']} | `{x['name']}` | {', '.join(x['tags'])} |" for x in selected]
    lines += ['', '## Pruebas disponibles', '']
    lines += [f"- `{x['file']}:{x['line']}` — `{x['name']}`" for x in data['tests']]
    (folder / 'INVENTARIO.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    counts = {tag: sum(tag in x['tags'] for x in data['symbols'])
              for tag in ('command', 'component_callback', 'event', 'scheduled_loop', 'view_or_modal', 'interaction_hook')}
    print(json.dumps(dict(counts, definitions=len(data['symbols']), dynamic_sites=len(data['interaction_sites']), tests=len(data['tests']))))
