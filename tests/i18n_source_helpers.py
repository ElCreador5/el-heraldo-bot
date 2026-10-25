"""Vista semántica española para las regresiones AST anteriores a i18n.

Revierte exclusivamente las llamadas de presentación y sus contextos. No se
usa en las pruebas de cobertura/i18n, que examinan y ejecutan el código real.
Permite conservar los controles de permisos, sanciones y persistencia previos.
"""
import ast
import json
import re
from string import Formatter
from functools import lru_cache
from pathlib import Path
import heraldo_i18n


class SourcePresentation(ast.NodeTransformer):
    def visit_Call(self, node):
        node = self.generic_visit(node)
        if (node.args and isinstance(node.args[0], ast.Constant)
                and ((isinstance(node.func, ast.Name) and node.func.id == '_i18n_variants')
                     or (isinstance(node.func, ast.Attribute) and node.func.attr == 'variants'
                         and isinstance(node.func.value, ast.Name) and node.func.value.id == 'i18n'))):
            return ast.copy_location(ast.Tuple(elts=[ast.Constant(value)
                for value in sorted(heraldo_i18n.variants(node.args[0].value))], ctx=ast.Load()), node)
        if not (isinstance(node.func, ast.Name) and node.func.id == '_t'
                and node.args and isinstance(node.args[0], ast.Constant)):
            return node
        template = heraldo_i18n.CATALOGS['es-419'].messages[node.args[0].value]
        if not node.keywords:
            return ast.copy_location(ast.Constant(template), node)
        values = {kw.arg: kw.value for kw in node.keywords}
        parts = []
        for literal, field, spec, conversion in Formatter().parse(template):
            if literal:
                parts.append(ast.Constant(literal))
            if field:
                expression = values[field]
                if isinstance(expression, ast.JoinedStr) and len(expression.values) == 1:
                    parts.append(expression.values[0])
                else:
                    parts.append(ast.FormattedValue(expression, -1))
        return ast.copy_location(ast.JoinedStr(parts), node)

    def visit_FunctionDef(self, node):
        node.decorator_list = [x for x in node.decorator_list
                               if not (isinstance(x, ast.Name) and x.id == '_i18n_context')]
        return self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_With(self, node):
        if (len(node.items) == 1 and isinstance(node.items[0].context_expr, ast.Call)
                and isinstance(node.items[0].context_expr.func, ast.Name)
                and node.items[0].context_expr.func.id == '_i18n_guild'):
            return [self.visit(item) for item in node.body]
        return self.generic_visit(node)


@lru_cache(maxsize=64)
def semantic_source(source):
    if 'from heraldo_i18n import text as _t' not in source:
        return source
    tree = ast.parse(source)
    parents = {id(child): parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == '_t']
    chosen = {id(node) for node in calls}
    lines = source.splitlines(keepends=True)
    offsets, position = [], 0
    for line in lines:
        offsets.append(position)
        position += len(line.encode())
    original = source.encode()
    edits = []
    for node in calls:
        parent = parents.get(id(node))
        while parent is not None and id(parent) not in chosen:
            parent = parents.get(id(parent))
        if parent is not None:
            continue
        first = offsets[node.lineno-1] + node.col_offset
        last = offsets[node.end_lineno-1] + node.end_col_offset
        segment = original[first:last].decode()
        result = SourcePresentation().visit(ast.parse(segment, mode='eval')).body
        rendered = (json.dumps(result.value, ensure_ascii=False)
                    if isinstance(result, ast.Constant) else ast.unparse(ast.fix_missing_locations(result)))
        first = offsets[node.lineno-1] + node.col_offset
        last = offsets[node.end_lineno-1] + node.end_col_offset
        edits.append((first, last, rendered.encode()))
    raw = source.encode()
    for first, last, replacement in sorted(edits, reverse=True):
        raw = raw[:first] + replacement + raw[last:]
    source = raw.decode()
    source = re.sub(r'^ *@_i18n_context\n', '', source, flags=re.M)
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    contexts = [node for node in ast.walk(tree) if isinstance(node, ast.With)
                and len(node.items) == 1 and isinstance(node.items[0].context_expr, ast.Call)
                and isinstance(node.items[0].context_expr.func, ast.Name)
                and node.items[0].context_expr.func.id == '_i18n_guild']
    for node in sorted(contexts, key=lambda node: node.lineno, reverse=True):
        lines[node.lineno-1:node.end_lineno] = [line[4:] for line in lines[node.lineno:node.end_lineno]]
    return ''.join(lines)


def source_text(path, *args, **kwargs):
    path = Path(path)
    raw = path.read_text(*args, **kwargs)
    if path.suffix == '.py' and path.resolve().parent == Path(__file__).resolve().parents[1]:
        return semantic_source(raw)
    return raw
