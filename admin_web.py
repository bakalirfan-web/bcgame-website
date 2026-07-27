"""
Local web admin panel for the BC.GAME bonus bot.
"""
import asyncio
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from aiohttp import web
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import RetryAfter

from admin import mark_user_done
from api import fetch_bcgame_user
from config import (
    ADMIN_PANEL_HOST,
    ADMIN_PANEL_KEY,
    ADMIN_PANEL_PORT,
    BOT_TOKEN,
    BROADCAST_BATCH_SIZE,
    DATABASE_PATH,
)
from database import Database

PANEL_FILE = Path(__file__).with_name("admin_panel.html")


@web.middleware
async def cors_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        response = web.Response(status=204)
    else:
        try:
            response = await handler(request)
        except web.HTTPException as exc:
            response = exc

    origin = request.headers.get("Origin")
    response.headers["Access-Control-Allow-Origin"] = origin or "*"
    response.headers["Vary"] = "Origin"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Admin-Key"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


def _auth_ok(request: web.Request, payload: dict = None) -> bool:
    key = request.headers.get("X-Admin-Key") or request.query.get("key")
    if payload:
        key = key or payload.get("key")
    return bool(ADMIN_PANEL_KEY and key == ADMIN_PANEL_KEY)


def _json_error(message: str, status: int = 400):
    return web.json_response({"ok": False, "error": message}, status=status)


async def _read_json(request: web.Request) -> dict:
    try:
        return await request.json()
    except Exception:
        return {}


async def _require_json_auth(request: web.Request):
    payload = await _read_json(request)
    if not _auth_ok(request, payload):
        return payload, _json_error("Unauthorized", 401)
    return payload, None


async def index(request: web.Request):
    return web.FileResponse(PANEL_FILE)


async def api_stats(request: web.Request):
    if not _auth_ok(request):
        return _json_error("Unauthorized", 401)
    await Database.update_statistics()
    return web.json_response({"ok": True, "stats": await Database.get_statistics()})


async def api_users(request: web.Request):
    if not _auth_ok(request):
        return _json_error("Unauthorized", 401)
    search = request.query.get("search") or ""
    users = await Database.get_admin_users(search=search)
    return web.json_response({"ok": True, "users": users})


async def api_public_profile(request: web.Request):
    """Testing endpoint for profile pages to fetch a UID without third-party proxies."""
    bc_uid = str(request.match_info.get("uid") or request.query.get("uid") or "").strip()
    if not bc_uid:
        return _json_error("BC.GAME UID is required.")

    try:
        data = await fetch_bcgame_user(bc_uid)
        if not data:
            return _json_error("Profile not found.", 404)
        return web.json_response({"ok": True, "data": data})
    except Exception as e:
        return _json_error(f"Profile fetch failed: {e}", 502)


async def _refresh_user_from_bcgame(bc_uid: str):
    user = await Database.get_user_by_bc_uid(bc_uid)
    if not user:
        raise web.HTTPNotFound(text="User not found.")

    bc_data = await fetch_bcgame_user(bc_uid)
    if not bc_data:
        raise web.HTTPBadGateway(text="BC.GAME profile not found or API failed.")

    saved = await Database.save_user(
        telegram_id=user["telegram_id"],
        bc_uid=bc_uid,
        bc_data=bc_data,
        username=user.get("username"),
    )
    if not saved:
        raise web.HTTPInternalServerError(text="Failed to save refreshed profile.")

    refreshed = await Database.get_user_by_bc_uid(bc_uid)
    return Database.serialize_admin_user(refreshed)


async def api_refresh_user(request: web.Request):
    payload, error = await _require_json_auth(request)
    if error:
        return error

    bc_uid = str(payload.get("bc_uid") or "").strip()
    if not bc_uid:
        return _json_error("BC.GAME UID is required.")

    try:
        user = await _refresh_user_from_bcgame(bc_uid)
    except web.HTTPException as e:
        return _json_error(e.text or e.reason, e.status)
    except Exception as e:
        return _json_error(f"Refresh failed: {e}", 502)

    return web.json_response({"ok": True, "user": user})


async def api_send_message(request: web.Request):
    payload, error = await _require_json_auth(request)
    if error:
        return error

    bc_uid = str(payload.get("bc_uid") or "").strip()
    text = str(payload.get("text") or "").strip()
    if not bc_uid or not text:
        return _json_error("BC.GAME UID and message text are required.")

    user = await Database.get_user_by_bc_uid(bc_uid)
    if not user:
        return _json_error("User not found.", 404)

    try:
        await _ensure_bot_ready(request.app)
        bot = request.app["bot"]
        msg = await bot.send_message(
            chat_id=user["telegram_id"],
            text=text,
            parse_mode=ParseMode.HTML,
        )
        await Database.record_bot_message(user["telegram_id"], msg.message_id)
        return web.json_response({"ok": True, "message_id": msg.message_id})
    except Exception as e:
        return _json_error(f"Telegram send failed: {e}", 502)


async def api_mark_done(request: web.Request):
    payload, error = await _require_json_auth(request)
    if error:
        return error

    bc_uid = str(payload.get("bc_uid") or "").strip()
    if not bc_uid:
        return _json_error("BC.GAME UID is required.")

    user = await Database.get_user_by_bc_uid(bc_uid)
    if not user:
        return _json_error("User not found.", 404)

    try:
        await _ensure_bot_ready(request.app)
        result = await mark_user_done(request.app["bot"], user)
    except Exception as e:
        return _json_error(f"Mark Done failed: {e}", 502)

    return web.json_response({
        "ok": True,
        "deleted_messages": result.get("deleted_messages", 0),
        "notified": result.get("notified", False),
        "error": result.get("error"),
        "bc_uid": bc_uid,
    })


def _user_label(user: dict) -> str:
    bc_username = user.get("bc_username") or user.get("telegram_username") or "User"
    return f"{bc_username} | UID {user.get('bc_uid')} | {user.get('level_name')} | TG {user.get('telegram_id')}"


async def _broadcast_job(app: web.Application, job_id: str, text: str):
    users = await Database.get_admin_users()
    job = app["broadcast_jobs"][job_id]
    job["total"] = len(users)
    latest_batch = []
    try:
        await _ensure_bot_ready(app)
    except Exception as e:
        job["status"] = "failed"
        job["errors"].append(f"Telegram init failed: {e}")
        job["updated_at"] = datetime.now().isoformat(timespec="seconds")
        return
    bot = app["bot"]

    for user in users:
        try:
            msg = await bot.send_message(
                chat_id=user["telegram_id"],
                text=text,
                parse_mode=ParseMode.HTML,
            )
            await Database.record_bot_message(user["telegram_id"], msg.message_id)
            job["sent"] += 1
            latest_batch.append(_user_label(user))
        except RetryAfter as e:
            await asyncio.sleep(float(e.retry_after) + 1)
            try:
                msg = await bot.send_message(
                    chat_id=user["telegram_id"],
                    text=text,
                    parse_mode=ParseMode.HTML,
                )
                await Database.record_bot_message(user["telegram_id"], msg.message_id)
                job["sent"] += 1
                latest_batch.append(_user_label(user))
            except Exception as retry_error:
                job["failed"] += 1
                job["errors"].append(f"{user.get('bc_uid')}: {retry_error}")
        except Exception as e:
            job["failed"] += 1
            job["errors"].append(f"{user.get('bc_uid')}: {e}")

        if job["sent"] and job["sent"] % BROADCAST_BATCH_SIZE == 0:
            job["latest_batch"] = latest_batch[-BROADCAST_BATCH_SIZE:]
            job["updated_at"] = datetime.now().isoformat(timespec="seconds")

        await asyncio.sleep(0.05)

    job["latest_batch"] = latest_batch[-BROADCAST_BATCH_SIZE:]
    job["status"] = "complete"
    job["updated_at"] = datetime.now().isoformat(timespec="seconds")


async def api_broadcast(request: web.Request):
    payload, error = await _require_json_auth(request)
    if error:
        return error

    text = str(payload.get("text") or "").strip()
    if not text:
        return _json_error("Broadcast text is required.")

    job_id = uuid4().hex[:12]
    request.app["broadcast_jobs"][job_id] = {
        "id": job_id,
        "status": "running",
        "total": 0,
        "sent": 0,
        "failed": 0,
        "latest_batch": [],
        "errors": [],
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    asyncio.create_task(_broadcast_job(request.app, job_id, text))
    return web.json_response({"ok": True, "job": request.app["broadcast_jobs"][job_id]})


async def api_broadcast_status(request: web.Request):
    if not _auth_ok(request):
        return _json_error("Unauthorized", 401)
    job_id = request.match_info["job_id"]
    job = request.app["broadcast_jobs"].get(job_id)
    if not job:
        return _json_error("Broadcast job not found.", 404)
    return web.json_response({"ok": True, "job": job})


async def _sync_users_job(app: web.Application, job_id: str):
    users = await Database.get_admin_users()
    job = app["sync_jobs"][job_id]
    job["total"] = len(users)

    for user in users:
        bc_uid = str(user.get("bc_uid") or "").strip()
        if not bc_uid:
            job["failed"] += 1
            continue

        try:
            refreshed = await _refresh_user_from_bcgame(bc_uid)
            job["synced"] += 1
            job["latest"] = {
                "bc_uid": bc_uid,
                "bc_username": refreshed.get("bc_username"),
                "level_name": refreshed.get("level_name"),
                "vip_tier": refreshed.get("vip_tier"),
            }
        except Exception as e:
            job["failed"] += 1
            job["errors"].append(f"{bc_uid}: {e}")
            job["errors"] = job["errors"][-10:]

        job["updated_at"] = datetime.now().isoformat(timespec="seconds")
        await asyncio.sleep(0.2)

    job["status"] = "complete"
    job["updated_at"] = datetime.now().isoformat(timespec="seconds")


async def api_sync_users(request: web.Request):
    payload, error = await _require_json_auth(request)
    if error:
        return error

    job_id = uuid4().hex[:12]
    request.app["sync_jobs"][job_id] = {
        "id": job_id,
        "status": "running",
        "total": 0,
        "synced": 0,
        "failed": 0,
        "latest": None,
        "errors": [],
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    asyncio.create_task(_sync_users_job(request.app, job_id))
    return web.json_response({"ok": True, "job": request.app["sync_jobs"][job_id]})


async def api_sync_status(request: web.Request):
    if not _auth_ok(request):
        return _json_error("Unauthorized", 401)
    job_id = request.match_info["job_id"]
    job = request.app["sync_jobs"].get(job_id)
    if not job:
        return _json_error("Sync job not found.", 404)
    return web.json_response({"ok": True, "job": job})


async def create_app(bot=None) -> web.Application:
    if not Database.db_path:
        await Database.init(DATABASE_PATH)

    owns_bot = bot is None
    bot = bot or Bot(BOT_TOKEN)

    app = web.Application(middlewares=[cors_middleware])
    app["bot"] = bot
    app["owns_bot"] = owns_bot
    app["runtime"] = {"bot_initialized": not owns_bot}
    app["broadcast_jobs"] = {}
    app["sync_jobs"] = {}
    app.add_routes([
        web.get("/", index),
        web.get("/api/stats", api_stats),
        web.get("/api/users", api_users),
        web.get("/api/public-profile/{uid}", api_public_profile),
        web.post("/api/refresh-user", api_refresh_user),
        web.post("/api/send-message", api_send_message),
        web.post("/api/mark-done", api_mark_done),
        web.post("/api/broadcast", api_broadcast),
        web.get("/api/broadcast/{job_id}", api_broadcast_status),
        web.post("/api/sync-users", api_sync_users),
        web.get("/api/sync-users/{job_id}", api_sync_status),
    ])
    app.on_cleanup.append(cleanup_app)
    return app


async def _ensure_bot_ready(app: web.Application):
    if app["runtime"].get("bot_initialized"):
        return
    await app["bot"].initialize()
    app["runtime"]["bot_initialized"] = True


async def cleanup_app(app: web.Application):
    if app.get("owns_bot") and app["runtime"].get("bot_initialized"):
        await app["bot"].shutdown()


async def start_admin_web(bot=None):
    app = await create_app(bot=bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, ADMIN_PANEL_HOST, ADMIN_PANEL_PORT)
    await site.start()
    return runner


async def stop_admin_web(runner):
    if runner:
        await runner.cleanup()


def main():
    async def run():
        runner = await start_admin_web()
        print(f"Admin panel running at http://{ADMIN_PANEL_HOST}:{ADMIN_PANEL_PORT}/")
        try:
            while True:
                await asyncio.sleep(3600)
        finally:
            await stop_admin_web(runner)

    asyncio.run(run())


if __name__ == "__main__":
    main()
