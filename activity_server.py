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

async def sdk_module(req):
    """Same-origin proxy for the pinned official SDK bundle.

    Discord Activities block unmapped third-party script origins. The SDK is
    retrieved from one fixed upstream; no caller-controlled URL is accepted.
    """
    import re
    requested = req.match_info.get("module", "")
    if not re.fullmatch(r"[\w@./-]{1,180}", requested) or ".." in requested:
        raise web.HTTPNotFound()
    upstream = "https://esm.sh/" + requested
    if requested == "@discord/embedded-app-sdk@2.5.0":
        upstream += "?bundle&target=es2022"
    async with req.app["session"].get(upstream, allow_redirects=True) as res:
        if res.status != 200:
            raise web.HTTPBadGateway(text="sdk_upstream_unavailable")
        source = await res.text()
    # esm.sh sometimes returns a small re-export module referring to an
    # absolute /... path; keep these module imports on our mapped origin.
    source = re.sub(r'(from\s*["\\x27]|import\s*\(\s*["\\x27])/', r'\1/sdk/', source)
    return web.Response(text=source, content_type="application/javascript",
                        headers={"Cache-Control": "public, max-age=3600",
                                 "X-Content-Type-Options": "nosniff"})

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


async def publish(req):
    """Secure, one-confirmation publish or persistent schedule on the real bot."""
    from datetime import datetime, timedelta, timezone
    import secrets
    from autofeed_embed_builder import validate_data, has_content
    from autofeed_setup import repeat_parts
    from message_publish import publish_message
    import message_autofeeds as feeds

    guild, member = await authorize(req)
    now = time.monotonic()
    key = (guild.id, member.id)
    last = req.app["rate"].get(key, 0)
    if now < last:
        return reply({"error": "slow_down"}, 429)
    req.app["rate"][key] = now + 5
    try:
        raw = await req.json()
        if not isinstance(raw, dict):
            raise ValueError("invalid_json")
        cid = raw.get("channel_id")
        if not isinstance(cid, str) or not cid.isdigit():
            raise ValueError("invalid_channel")
        channel = guild.get_channel(int(cid))
        if not isinstance(channel, discord.TextChannel):
            raise ValueError("invalid_channel")
        user_perms = channel.permissions_for(member)
        bot_perms = channel.permissions_for(guild.me)
        if not (user_perms.view_channel and user_perms.send_messages
                and bot_perms.view_channel and bot_perms.send_messages and bot_perms.embed_links):
            raise ValueError("channel_permissions")
        text = raw.get("message", "")
        if not isinstance(text, str) or len(text) > 1900:
            raise ValueError("invalid_message")
        visual = validate_data(raw["embed"]) if raw.get("embed") is not None else None
        if not text.strip() and not has_content(visual):
            raise ValueError("empty_message")
        rid = raw.get("role_id")
        if rid is not None and (not isinstance(rid, str) or not rid.isdigit()):
            raise ValueError("invalid_role")
        role = guild.get_role(int(rid)) if rid else None
        if rid and (role is None or not role.mentionable):
            raise ValueError("role_not_mentionable")
        iso = raw.get("scheduled_at")
        due = None
        if iso is not None:
            if not isinstance(iso, str) or len(iso) > 40:
                raise ValueError("invalid_date")
            due = datetime.fromisoformat(iso.replace("Z", "+00:00"))
            if due.tzinfo is None:
                raise ValueError("invalid_date")
            due = due.astimezone(timezone.utc)
            if due <= datetime.now(timezone.utc) + timedelta(minutes=1):
                raise ValueError("date_must_be_future")
        units = raw.get("repeat") or {}
        if not isinstance(units, dict):
            raise ValueError("invalid_repeat")
        values = [units.get(k, 0) for k in ("months", "days", "hours", "minutes")]
        if not all(type(v) is int for v in values):
            raise ValueError("invalid_repeat")
        parts = repeat_parts(*values)
        if parts and due is None:
            raise ValueError("repeat_needs_date")
        job = {
            "id": secrets.token_hex(6), "guild": guild.id,
            "author": member.id, "requester": member.id, "channel": channel.id,
            "role": role.id if role else None, "text": text.strip(), "embed": visual,
            "start": due.isoformat() if due else None, "zone": "America/Santo_Domingo",
            "repeat": "custom" if parts else "ninguna", "repeat_parts": parts,
            "autofeed": True, "paused": False, "template": None,
        }
        feeds.referenced_mentions(guild, job)
    except (ValueError, KeyError, TypeError) as exc:
        return reply({"error": str(exc)[:120]}, 400)

    if job["start"] is None:
        try:
            sent = await publish_message(req.app["host"], guild, channel, job)
        except discord.HTTPException:
            # An ambiguous Discord response must never trigger a duplicate retry.
            return reply({"error": "delivery_uncertain_check_channel"}, 502)
        return reply({"status": "published", "message_id": str(sent.id)})
    try:
        feeds.persist_schedule(req.app["host"], guild.id, member, job)
    except ValueError as exc:
        return reply({"error": "schedule_" + str(exc)[:80]}, 409)
    return reply({"status": "scheduled", "id": job["id"]})

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
        app.router.add_get("/sdk/{module:.*}", sdk_module)
        app.router.add_get("/health", health)
        app.router.add_get("/api/config", config)
        app.router.add_post("/api/token", oauth)
        app.router.add_get("/api/options", options)
        app["rate"] = {}
        app.router.add_post("/api/messages", publish)
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
