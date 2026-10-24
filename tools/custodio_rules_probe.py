"""Sonda aislada de solo lectura para Server Rules de Heraldo's Lab.

No se importa por bot.py; ejecutar solo con las credenciales de El Heraldo Test.
No modifica reglas, miembros, roles, SQLite ni mensajes de Discord.
"""
from __future__ import annotations
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

GUILD_ID = "1557230352802644040"
API_ROOT = "https://discord.com/api/v10"
MAX_RESPONSE_BYTES = 64 * 1024

def get_discord(path: str, token: str, *, opener=urlopen) -> tuple[int, dict]:
    """GET limitado sin registrar cabeceras ni credenciales."""
    req = Request(
        API_ROOT + path,
        method="GET",
        headers={
            "Authorization": "Bot " + token,
            "Accept": "application/json",
            "User-Agent": "ElHeraldo-Custodio-LabProbe/1.0",
        },
    )
    try:
        response = opener(req, timeout=12)
    except HTTPError as exc:
        try:
            payload = json.loads(exc.read(MAX_RESPONSE_BYTES))
        except (ValueError, TypeError):
            payload = {}
        return exc.code, payload if isinstance(payload, dict) else {}
    except (URLError, TimeoutError, OSError):
        return 0, {}
    try:
        with response:
            status = int(response.status)
            payload = json.loads(response.read(MAX_RESPONSE_BYTES))
    except (ValueError, TypeError, OSError):
        return 0, {}
    return status, payload if isinstance(payload, dict) else {}

def evaluate(token: str, *, reader=get_discord) -> dict:
    guild_status, guild = reader(f"/guilds/{GUILD_ID}", token)
    features = guild.get("features") if guild_status == 200 else None
    enabled = ("MEMBER_VERIFICATION_GATE_ENABLED" in features) if isinstance(features, list) else None
    screening_status, verification = reader(f"/guilds/{GUILD_ID}/member-verification", token)
    fields = verification.get("form_fields") if screening_status == 200 else None
    terms = [f for f in fields if isinstance(f, dict) and f.get("field_type") == "TERMS"] if isinstance(fields, list) else []
    rules = [rule[:300] for field in terms for rule in (field.get("values") or []) if isinstance(rule, str)]
    return {
        "probe": "CUSTODIO_LAB_READ_ONLY",
        "guild_http": guild_status,
        "screening_enabled": enabled,
        "verification_http": screening_status,
        "discord_error_code": verification.get("code") if isinstance(verification.get("code"), int) else None,
        "terms_fields": len(terms),
        "rules_count": len(rules),
        "rules": rules,
    }

def main() -> int:
    token = os.environ.get("DISCORD_TOKEN", "")
    if not token:
        print("CUSTODIO_LAB_RESULT:" + json.dumps({"status": "test_bot_token_missing"}))
        return 0
    print("CUSTODIO_LAB_RESULT:" + json.dumps(evaluate(token), ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
