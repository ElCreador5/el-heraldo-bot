"""Análisis real y de solo lectura en Lab; sin DB, mensajes ni activación.

Se ejecuta explícitamente en el contenedor previo al despliegue autorizado.
Solo publica metadatos, nunca reglas, respuestas del modelo o credenciales.
"""
from __future__ import annotations
import asyncio
from collections import Counter
import json
import os
from pathlib import Path
import sys
import time
import aiohttp

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from custodio_ai_runtime import MODEL
from custodio_rule_analysis import analyze,BUDGET
from custodio_source import load_server_rules
from tools.custodio_rules_probe import GUILD_ID,API_ROOT

PROJECT='747a1ee0-cdab-4ad5-8e45-a6ddfccc9b61'
ENVIRONMENT='71b77daf-9092-4af0-913f-32c57367fff3'


async def context(token):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
        async def get(resource):
            async with session.get(API_ROOT+f'/guilds/{GUILD_ID}/'+resource,
                    headers={'Authorization':'Bot '+token},allow_redirects=False) as response:
                if response.status!=200:
                    raise ValueError('discord_context_unavailable')
                chunks=bytearray()
                async for chunk in response.content.iter_chunked(4096):
                    chunks.extend(chunk)
                    if len(chunks)>131072:
                        raise ValueError('discord_context_size_limit')
                value=json.loads(chunks)
                if type(value) is not list:
                    raise ValueError('discord_context_invalid')
                return value
        channels=await get('channels');roles=await get('roles')
    return ({int(item['id']):item['name'] for item in channels if item.get('type')==0},
            {int(item['id']) for item in roles})


async def probe(*,loader=load_server_rules,context_loader=context,analyzer=analyze):
    if os.environ.get('RAILWAY_PROJECT_ID')!=PROJECT or os.environ.get('RAILWAY_ENVIRONMENT_ID')!=ENVIRONMENT:
        return {'status':'LAB_ONLY_GUARD'},False
    token=os.environ.get('DISCORD_TOKEN','')
    if not token:
        return {'status':'BOT_CREDENTIAL_UNAVAILABLE'},False
    start=time.monotonic()
    try:
        snapshot=await loader(int(GUILD_ID),token)
        if snapshot.guild_id != int(GUILD_ID):
            raise ValueError('foreign_guild_snapshot')
        channels,roles=await context_loader(token)
        class Monitor:
            requests=0
            async def take(self,cost,deadline):
                await BUDGET.take(cost,deadline)
                self.requests+=1
        monitor=Monitor()
        plan=await analyzer(snapshot,administrator_requested=True,channels=channels,role_ids=roles,
                            maximum_seconds=225,budget=monitor)
        counts=Counter(rule.status for rule in plan.rules)
        invalid=sum(rule.status=='unavailable' or 'invalid_interpretation' in rule.limitations for rule in plan.rules)
        success=monitor.requests>0 and invalid==0
        return {'status':'AUTHENTIC_RULE_ANALYSIS_VALIDATED' if success else 'AUTHENTIC_RULE_ANALYSIS_PARTIAL',
            'input':'authentic_discord_server_rules','model':MODEL,'rules':snapshot.count,
            'revision':snapshot.revision,'states':dict(counts),
            'requests_reserved':monitor.requests,'invalid_or_unavailable_rules':invalid,
            'saved':False,'enabled_changed':False,'discord_interactive':False,
            'elapsed_ms':round((time.monotonic()-start)*1000)},success
    except Exception as exc:
        return {'status':'ANALYSIS_UNAVAILABLE','exception':type(exc).__name__,
                'elapsed_ms':round((time.monotonic()-start)*1000)},False


def main():
    result,success=asyncio.run(probe())
    print('CUSTODIO_ANALYSIS_HEALTH '+json.dumps(result,sort_keys=True))
    return 0 if success else 1


if __name__=='__main__':
    raise SystemExit(main())
