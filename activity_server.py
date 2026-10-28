"""Serve El Heraldo's first-party Discord Activity from the Lab worker.

The Activity shares the existing bot and database; it never exposes the bot
token to JavaScript and never writes to SQLite without the bot's scheduler.
"""
import os
from pathlib import Path
import time
from aiohttp import web, ClientSession, ClientTimeout
import discord

ROOT = Path(__file__).resolve().parent / "activity"
API = "https://discord.com/api/v10"
CACHE = {}

def reply(data, status=200):
    return web.json_response(data, status=status, headers={"Cache-Control": "no-store"})

def verify_origin(req):
    origin = req.headers.get("Origin", "")
    if not origin:
        return
    bot = req.app["bot"]
    application_id = str(bot.application_id or (bot.user.id if bot.user else ""))
    allowed = {"https://" + req.host, "http://" + req.host,
               "https://" + application_id + ".discordsays.com"}
    if origin not in allowed:
        raise web.HTTPForbidden(text="invalid_origin")

async def index(req):
    return web.FileResponse(ROOT / "index.html", headers={"Cache-Control": "no-store"})

async def css(req):
    return web.FileResponse(ROOT / "style.css")

async def javascript(req):
    return web.FileResponse(ROOT / "main.js", headers={"Cache-Control": "no-store"})

async def health(req):
    return reply({"status": "ok", "configured": bool(os.getenv("DISCORD_ACTIVITY_CLIENT_SECRET"))})

async def config(req):
    bot = req.app["bot"]
    return reply({"client_id": str(bot.application_id or bot.user.id),
                  "ready": bool(os.getenv("DISCORD_ACTIVITY_CLIENT_SECRET")),
                  "stage": "Lab"})

async def oauth(req):
    verify_origin(req)
    secret = os.getenv("DISCORD_ACTIVITY_CLIENT_SECRET")
    if not secret:
        return reply({"error": "oauth_not_configured"}, 503)
    obj = await req.json()
    code = obj.get("code")
    if not isinstance(code, str) or not 2 <= len(code) <= 300:
        return reply({"error": "invalid_code"}, 400)
    app_id = str(req.app["bot"].application_id or req.app["bot"].user.id)
    async with req.app["session"].post(API + "/oauth2/token", data={
        "client_id": app_id,
        "client_secret": secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "https://127.0.0.1",
    }) as resp:
        if resp.status != 200:
            return reply({"error": "discord_oauth_failed"}, 401)
        data = await resp.json()
    return reply({"access_token": data["access_token"], "expires_in": data.get("expires_in", 3600)})

async def authorize(req):
    verify_origin(req)
    bearer = req.headers.get("Authorization", "")
    if not bearer.startswith("Bearer ") or len(bearer) > 1500:
        raise web.HTTPUnauthorized(text="login_required")
    token = bearer[7:]
    now = time.monotonic()
    entry = CACHE.get(token)
    if entry and entry[1] > now:
        user_id = entry[0]
    else:
        async with req.app["session"].get(API + "/users/@me",
              headers={"Authorization": bearer}) as resp:
            if resp.status != 200:
                raise web.HTTPUnauthorized(text="login_required")
            user_id = int((await resp.json())["id"])
        CACHE[token] = (user_id, now + 30)
        if len(CACHE) > 250:
            for key, val in list(CACHE.items()):
                if val[1] < now:
                    CACHE.pop(key, None)
    raw = req.query.get("guild_id", "")
    if not raw.isdigit():
        raise web.HTTPBadRequest(text="guild_id_required")
    guild = req.app["bot"].get_guild(int(raw))
    if guild is None:
        raise web.HTTPForbidden(text="guild_not_found")
    try:
        member = await guild.fetch_member(user_id)
    except (discord.NotFound, discord.Forbidden):
        raise web.HTTPForbidden(text="member_not_found")
    if not member.guild_permissions.manage_guild:
        raise web.HTTPForbidden(text="manage_guild_required")
    return guild, member

async def options(req):
    guild, member = await authorize(req)
    me = guild.me
    channels = []
    for channel in guild.text_channels:
        a, b = channel.permissions_for(member), channel.permissions_for(me)
        if a.view_channel and a.send_messages and b.view_channel and b.send_messages and b.embed_links:
            channels.append({"id": str(channel.id), "name": channel.name})
    roles = [{"id": str(role.id), "name": role.name, "mentionable": role.mentionable}
             for role in guild.roles if not role.is_default()]
    return reply({"guild": {"id": str(guild.id), "name": guild.name},
                  "channels": channels[:500], "roles": roles[:250]})

def install(host):
    bot = host["bot"]
    state = {"runner": None}
    async def ready():
        if state["runner"] is not None or os.getenv("DISCORD_ACTIVITY_WEB_ENABLED") != "1":
            return
        session = ClientSession(timeout=ClientTimeout(total=15))
        app = web.Application(client_max_size=24_000)
        app["session"] = session
        app["bot"] = bot
        app["host"] = host
        app.router.add_get("/", index)
        app.router.add_get("/assets/style.css", css)
        app.router.add_get("/assets/main.js", javascript)
        app.router.add_get("/health", health)
        app.router.add_get("/api/config", config)
        app.router.add_post("/api/token", oauth)
        app.router.add_get("/api/options", options)
        runner = web.AppRunner(app)
        try:
            await runner.setup()
            await web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", "8080"))).start()
        except Exception:
            await runner.cleanup()
            await session.close()
            raise
        state["runner"] = runner
        print("ACTIVITY_WEB status=LISTENING mode=Lab")
    bot.add_listener(ready, "on_ready")
