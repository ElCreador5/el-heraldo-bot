"""Sonda de lectura autorizada: nunca imprime reglas, token o miembros."""
from __future__ import annotations
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from custodio_source import load_server_rules


async def check(guild_id):
    snapshot=await load_server_rules(guild_id,os.environ.get('DISCORD_TOKEN',''))
    print('CUSTODIO_RULES_HEALTH '+json.dumps({'status':'VERIFIED_READ_ONLY',
          'rules_count':snapshot.count,'revision':snapshot.revision},sort_keys=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--guild-id',required=True,type=int)
    arguments=parser.parse_args()
    try:
        asyncio.run(check(arguments.guild_id))
    except Exception as exc:
        print('CUSTODIO_RULES_HEALTH '+json.dumps({'status':'UNAVAILABLE','exception':type(exc).__name__}))
        raise SystemExit(1)
