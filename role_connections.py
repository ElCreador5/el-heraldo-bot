"""Motor de conexiones de roles basadas en condiciones internas del servidor.

No utiliza OAuth2 ni los Linked Roles de Discord. Evita roles gestionados,
privilegiados y protegidos; no concede roles mientras una condena está activa.
"""
from __future__ import annotations

import asyncio
from contextlib import closing
from dataclasses import dataclass
import json
import sqlite3
from uuid import uuid4

MAX_RULES = 20
MAX_GROUPS = 5
MAX_CONDITIONS = 10
PRIVILEGED = (
    "administrator", "manage_guild", "manage_roles", "manage_channels",
    "manage_webhooks", "ban_members", "kick_members", "moderate_members",
    "manage_messages", "mention_everyone",
)
SCHEMA = """
CREATE TABLE IF NOT EXISTS heraldo_role_connections (
    guild_id INTEGER NOT NULL,
    rule_id TEXT NOT NULL,
    name TEXT NOT NULL,
    target_role_id INTEGER NOT NULL,
    groups_json TEXT NOT NULL,
    groups_mode TEXT NOT NULL CHECK(groups_mode IN ('all', 'any')),
    enabled INTEGER NOT NULL DEFAULT 1,
    revision TEXT NOT NULL,
    PRIMARY KEY (guild_id, rule_id),
    UNIQUE (guild_id, target_role_id)
)
"""
_locks: dict[tuple[int, int], asyncio.Lock] = {}


@dataclass(frozen=True)
class Rule:
    rule_id: str
    name: str
    target_role_id: int
    groups: tuple[dict, ...]
    groups_mode: str
    enabled: bool
    revision: str


def ensure_schema(connect):
    with closing(connect()) as db:
        db.execute(SCHEMA)


def _decode(row):
    return Rule(
        rule_id=str(row[0]), name=str(row[1]), target_role_id=int(row[2]),
        groups=tuple(json.loads(row[3])), groups_mode=str(row[4]),
        enabled=bool(row[5]), revision=str(row[6]),
    )


def list_rules(connect, guild_id: int) -> list[Rule]:
    # Abrir /setup o recibir un evento nunca altera el esquema SQLite.
    # La tabla solo se crea al confirmar el primer guardado.
    with closing(connect()) as db:
        if db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' "
            "AND name='heraldo_role_connections'"
        ).fetchone() is None:
            return []
        rows = db.execute(
            "SELECT rule_id,name,target_role_id,groups_json,groups_mode,enabled,revision "
            "FROM heraldo_role_connections WHERE guild_id=? ORDER BY name,rule_id",
            (guild_id,),
        ).fetchall()
    return [_decode(row) for row in rows]


def get_rule(connect, guild_id, rule_id):
    return next((r for r in list_rules(connect, guild_id) if r.rule_id == rule_id), None)


def validate_groups(groups, groups_mode, target_id):
    if groups_mode not in ("all", "any") or not 1 <= len(groups) <= MAX_GROUPS:
        raise ValueError("invalid_groups")
    dependencies = set()
    clean = []
    for group in groups:
        mode = group.get("mode")
        conditions = group.get("conditions", [])
        if mode not in ("all", "any", "xor", "not", "at_least") or not 1 <= len(conditions) <= MAX_CONDITIONS:
            raise ValueError("invalid_conditions")
        minimum = None
        if mode == "at_least":
            minimum = group.get("min_required")
            if (isinstance(minimum, bool) or not isinstance(minimum, int)
                    or not 1 <= minimum <= len(conditions)):
                raise ValueError("invalid_minimum")
        normalized = []
        seen = set()
        for item in conditions:
            role_id = int(item.get("role_id") or 0)
            op = item.get("op")
            if role_id <= 0 or op not in ("has", "lacks"):
                raise ValueError("invalid_conditions")
            if role_id == target_id:
                raise ValueError("circular_rule")
            pair = (role_id, op)
            if pair in seen:
                raise ValueError("duplicate_condition")
            if (role_id, "has" if op == "lacks" else "lacks") in seen:
                raise ValueError("contradictory_condition")
            seen.add(pair)
            dependencies.add(role_id)
            normalized.append({"role_id": role_id, "op": op})
        normalized_group = {"mode": mode, "conditions": normalized}
        if minimum is not None:
            normalized_group["min_required"] = minimum
        clean.append(normalized_group)
    return clean, dependencies


def _dependencies(rule):
    return {int(c["role_id"]) for g in rule.groups for c in g["conditions"]}


def _ordered(rules):
    """Topological order; a connection may depend on another main role."""
    by_target = {r.target_role_id: r for r in rules}
    done, visiting, result = set(), set(), []

    def visit(role_id):
        if role_id in visiting:
            raise ValueError("circular_rule")
        if role_id in done:
            return
        visiting.add(role_id)
        rule = by_target[role_id]
        for source in _dependencies(rule):
            if source in by_target:
                visit(source)
        visiting.remove(role_id)
        done.add(role_id)
        result.append(rule)

    for role_id in by_target:
        visit(role_id)
    return result


def target_safety_reason(guild, role, protected_ids=()):
    """Return a precise, localizable reason when a main role is unsafe.

    Role connections never administer personality, verification, condemnation,
    privileged, managed, or higher-priority roles.
    """
    if role is None or role.guild.id != guild.id:
        return "missing_role"
    if role.id in set(protected_ids):
        return "unsafe_protected"
    if role.is_default():
        return "unsafe_default"
    if role.managed:
        return "unsafe_managed"
    me = getattr(guild, "me", None)
    if me is None:
        return "unsafe_bot_member"
    if not me.guild_permissions.manage_roles:
        return "unsafe_bot_permissions"
    if role >= me.top_role:
        return "unsafe_hierarchy"
    if any(getattr(role.permissions, name, False) for name in PRIVILEGED):
        return "unsafe_privileged"
    return None


def target_is_safe(guild, role, protected_ids=()):
    return target_safety_reason(guild, role, protected_ids) is None


def save_rule(connect, guild, *, name, target_role_id, groups, groups_mode="all",
              rule_id=None, expected_revision=None, protected_ids=()):
    target_id = int(target_role_id)
    clean, dependencies = validate_groups(groups, groups_mode, target_id)
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
        raise ValueError("invalid_name")
    if any(guild.get_role(i) is None for i in dependencies | {target_id}):
        raise ValueError("missing_role")
    unsafe_reason = target_safety_reason(
        guild, guild.get_role(target_id), protected_ids
    )
    if unsafe_reason is not None:
        raise ValueError(unsafe_reason)
    ensure_schema(connect)
    new = Rule(rule_id or uuid4().hex, name.strip(), target_id, tuple(clean),
               groups_mode, True, uuid4().hex)
    # Serialización transaccional frente a dos paneles que guardan simultáneamente.
    with closing(connect()) as db:
        db.execute("BEGIN IMMEDIATE")
        try:
            rows = db.execute(
                "SELECT rule_id,name,target_role_id,groups_json,groups_mode,enabled,revision "
                "FROM heraldo_role_connections WHERE guild_id=?",
                (guild.id,),
            ).fetchall()
            current = [_decode(row) for row in rows]
            old = next((r for r in current if r.rule_id == rule_id), None)
            if rule_id is not None and (old is None or old.revision != expected_revision):
                raise ValueError("stale_rule")
            if rule_id is None and len(current) >= MAX_RULES:
                raise ValueError("rule_limit")
            if any(r.target_role_id == target_id and r.rule_id != rule_id for r in current):
                raise ValueError("duplicate_target")
            proposed = [r for r in current if r.rule_id != rule_id] + [new]
            _ordered(proposed)
            if old is None:
                db.execute(
                    "INSERT INTO heraldo_role_connections "
                    "(guild_id,rule_id,name,target_role_id,groups_json,groups_mode,enabled,revision) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (guild.id, new.rule_id, new.name, target_id, json.dumps(clean),
                     groups_mode, 1, new.revision),
                )
            else:
                db.execute(
                    "UPDATE heraldo_role_connections SET name=?,target_role_id=?,"
                    "groups_json=?,groups_mode=?,revision=? "
                    "WHERE guild_id=? AND rule_id=?",
                    (new.name, target_id, json.dumps(clean), groups_mode,
                     new.revision, guild.id, rule_id),
                )
            db.execute("COMMIT")
        except Exception:
            db.execute("ROLLBACK")
            raise
    return new


def delete_rule(connect, guild_id, rule_id, expected_revision):
    ensure_schema(connect)
    with closing(connect()) as db:
        result = db.execute(
            "DELETE FROM heraldo_role_connections WHERE guild_id=? AND rule_id=? AND revision=?",
            (guild_id, rule_id, expected_revision),
        )
        return result.rowcount == 1


def switch_rule(connect, guild_id, rule_id, revision, enabled):
    ensure_schema(connect)
    with closing(connect()) as db:
        result = db.execute(
            "UPDATE heraldo_role_connections SET enabled=?,revision=? "
            "WHERE guild_id=? AND rule_id=? AND revision=?",
            (int(enabled), uuid4().hex, guild_id, rule_id, revision),
        )
        return result.rowcount == 1


def _group_matches(group, held):
    """Evaluate validated group modes without changing existing AND/OR semantics."""
    values = [
        (int(c["role_id"]) in held) if c["op"] == "has"
        else (int(c["role_id"]) not in held)
        for c in group["conditions"]
    ]
    mode = group["mode"]
    if mode == "all":
        return all(values)
    if mode == "any":
        return any(values)
    if mode == "xor":
        # Exactly one, NOT odd-number parity.
        return sum(values) == 1
    if mode == "not":
        # Negate the entire AND-group, not each condition individually.
        return not all(values)
    if mode == "at_least":
        minimum = group.get("min_required")
        return (type(minimum) is int and 1 <= minimum <= len(values)
                and sum(values) >= minimum)
    # Fail closed for unsupported or corrupted stored modes.
    return False


def matches(rule, held):
    held = set(held)
    groups = [_group_matches(group, held) for group in rule.groups]
    if rule.groups_mode == "all":
        return all(groups)
    if rule.groups_mode == "any":
        return any(groups)
    return False


async def reconcile_member(member, *, connect, protected_ids=(), blocked=None):
    """Idempotente: ordena dependencias y limita cambios a roles seguros."""
    if member.bot or (blocked is not None and blocked(member)):
        return 0, 0
    guild = member.guild
    rules = _ordered([r for r in list_rules(connect, guild.id) if r.enabled])
    if not rules:
        return 0, 0
    key = (guild.id, member.id)
    lock = _locks.setdefault(key, asyncio.Lock())
    async with lock:
        if blocked is not None and blocked(member):
            return 0, 0
        latest = guild.get_member(member.id)
        if latest is not None:
            member = latest
        held = {role.id for role in member.roles}
        added = removed = 0
        for rule in rules:
            role = guild.get_role(rule.target_role_id)
            # Nunca convertir una regla previa en un mecanismo de escalada de permisos.
            if not target_is_safe(guild, role, protected_ids):
                continue
            satisfies = matches(rule, held)
            try:
                if satisfies and role.id not in held:
                    await member.add_roles(role, reason="El Heraldo: conexión de roles")
                    held.add(role.id)
                    added += 1
                elif not satisfies and role.id in held:
                    await member.remove_roles(role, reason="El Heraldo: conexión de roles")
                    held.remove(role.id)
                    removed += 1
            except Exception as exc:
                print(f"ROLE_CONNECTIONS status=UPDATE_FAILED guild={guild.id} "
                      f"exception={type(exc).__name__}", flush=True)
        return added, removed


async def synchronize(guild, *, connect, protected_ids=(), blocked=None, limit=None, progress=None):
    """Barrido explícito completo; nunca se ejecuta al guardar una regla."""
    checked = added = removed = 0
    exceeded = False
    async for member in guild.fetch_members(limit=(limit + 1 if limit is not None else None)):
        if limit is not None and checked >= limit:
            exceeded = True
            break
        checked += 1
        a, r = await reconcile_member(
            member, connect=connect, protected_ids=protected_ids, blocked=blocked
        )
        added += a
        removed += r
        if progress is not None:
            await progress(checked, added, removed)
    return checked, added, removed, exceeded
