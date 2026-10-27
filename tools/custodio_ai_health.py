"""Una inferencia real con regla sintética; sin Discord, SQLite ni secretos en salida."""
from __future__ import annotations
import asyncio
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from custodio_ai_runtime import AIUnavailable, MODEL, analyze_rule
from custodio_core import RulesSnapshot


async def check():
    rule = "Está prohibido enviar mensajes repetidos que saturen los canales."
    snapshot = RulesSnapshot(1, (rule,), sha256(rule.encode()).hexdigest())
    started = time.monotonic()
    result = {"model": MODEL, "input": "synthetic_rule", "max_requests": 1}
    try:
        proposal = await analyze_rule(snapshot, 0, administrator_requested=True)
        result.update(status="REAL_INFERENCE_VALIDATED", schema_validated=True,
                      exact_quote_validated=True,
                      clarification_requested=proposal["needs_clarification"])
    except AIUnavailable as exc:
        result.update(status="UNAVAILABLE", reason=str(exc))
    except Exception as exc:
        result.update(status="UNAVAILABLE", exception=type(exc).__name__)
    result["elapsed_ms"] = round((time.monotonic() - started) * 1000)
    print("CUSTODIO_AI_HEALTH " + json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "REAL_INFERENCE_VALIDATED" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(check()))
