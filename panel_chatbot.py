"""
Telegram admin control bot for the local admin panel.

This bot only exposes panel-management actions through the authenticated
admin web API. It does not collect credentials or handle user login data.
"""
from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, Optional

import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import ADMIN_IDS, ADMIN_PANEL_KEY, ADMIN_PANEL_PORT, BOT_TOKEN

ADMIN_PANEL_BASE_URL = os.getenv(
    "ADMIN_PANEL_BASE_URL",
    f"http://127.0.0.1:{ADMIN_PANEL_PORT}",
)

HTTP_TIMEOUT = aiohttp.ClientTimeout(total=30)


async def _api_get(path: str, key: str) -> Dict[str, Any]:
    url = f"{ADMIN_PANEL_BASE_URL.rstrip('/')}{path}"
    headers = {"X-Admin-Key": key}
    async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json(content_type=None)
            if response.status >= 400:
                raise RuntimeError(data.get("error") or f"Request failed: {response.status}")
            return data


async def _api_post(path: str, key: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f"{ADMIN_PANEL_BASE_URL.rstrip('/')}{path}"
    headers = {"X-Admin-Key": key}
    async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
        async with session.post(url, json=payload or {}, headers=headers) as response:
            data = await response.json(content_type=None)
            if response.status >= 400:
                raise RuntimeError(data.get("error") or f"Request failed: {response.status}")
            return data


def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def _require_admin(update: Update) -> bool:
    user = update.effective_user
    if not user or not _is_admin(user.id):
        if update.message:
            await update.message.reply_text("⛔ You do not have access to this control bot.")
        return False
    return True


def _menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📊 Stats", callback_data="stats")],
            [InlineKeyboardButton("👥 Users", callback_data="users")],
            [InlineKeyboardButton("🔄 Sync", callback_data="syncusers")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
            [InlineKeyboardButton("❓ Help", callback_data="help")],
        ]
    )


async def _send_menu(update: Update, text: str = None):
    message_text = text or (
        "🔧 <b>Panel Control Bot</b>\n\n"
        "Send a command here or tap a button below.\n"
        f"Panel URL: <code>{ADMIN_PANEL_BASE_URL}</code>"
    )
    if update.message:
        await update.message.reply_text(
            message_text,
            reply_markup=_menu_keyboard(),
            parse_mode=ParseMode.HTML,
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            message_text,
            reply_markup=_menu_keyboard(),
            parse_mode=ParseMode.HTML,
        )


async def _run_named_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
    if action == "stats":
        await stats(update, context)
    elif action == "users":
        await users(update, context)
    elif action == "syncusers":
        await syncusers(update, context)
    elif action == "broadcast":
        await broadcast(update, context)
    elif action == "help":
        await help_command(update, context)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update):
        return
    await _send_menu(update)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update):
        return

    try:
        data = await _api_get("/api/stats", ADMIN_PANEL_KEY)
        stats_data = data.get("stats", {})
        text = (
            "📊 <b>Panel Stats</b>\n\n"
            f"Total users: <b>{stats_data.get('total_users', 0)}</b>\n"
            f"Eligible users: <b>{stats_data.get('eligible_users', 0)}</b>\n"
            f"Verified users: <b>{stats_data.get('verified_users', 0)}</b>\n"
            f"Pending: <b>{stats_data.get('pending_users', 0)}</b>\n"
            f"Marked done: <b>{stats_data.get('marked_done_users', 0)}</b>\n"
            f"Active users: <b>{stats_data.get('active_users', 0)}</b>\n"
            f"Total claims: <b>{stats_data.get('total_claims', 0)}</b>\n"
            f"Average level: <b>{float(stats_data.get('average_level', 0)):.1f}</b>\n"
            f"Highest level: <b>{stats_data.get('highest_level', 0)}</b>\n"
            f"Updated: <code>{stats_data.get('last_updated', 'N/A')}</code>"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    except Exception as exc:
        await update.message.reply_text(f"❌ Stats failed: {exc}")


async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update):
        return

    try:
        data = await _api_get("/api/users", ADMIN_PANEL_KEY)
        items = data.get("users", [])[:10]
        if not items:
            await update.message.reply_text("No users found.")
            return

        lines = ["👥 <b>Users</b>\n"]
        for user in items:
            lines.append(
                f"• UID <code>{user.get('bc_uid', 'N/A')}</code> | "
                f"{user.get('bc_username') or user.get('telegram_username') or 'User'} | "
                f"Level {user.get('level_name') or user.get('level', 0)}"
            )
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
    except Exception as exc:
        await update.message.reply_text(f"❌ Users failed: {exc}")


async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update):
        return

    if not context.args:
        await update.message.reply_text("Usage: /refresh <BC.GAME UID>")
        return

    bc_uid = context.args[0].strip()
    try:
        data = await _api_post("/api/refresh-user", ADMIN_PANEL_KEY, {"bc_uid": bc_uid})
        user = data.get("user", {})
        await update.message.reply_text(
            f"✅ Refreshed <code>{bc_uid}</code>\n"
            f"Name: {user.get('bc_username') or 'N/A'}\n"
            f"Level: {user.get('level_name') or 'N/A'}",
            parse_mode=ParseMode.HTML,
        )
    except Exception as exc:
        await update.message.reply_text(f"❌ Refresh failed: {exc}")


async def sendmsg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update):
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /sendmsg <BC.GAME UID> <message>")
        return

    bc_uid = context.args[0].strip()
    text = " ".join(context.args[1:]).strip()
    try:
        data = await _api_post("/api/send-message", ADMIN_PANEL_KEY, {"bc_uid": bc_uid, "text": text})
        await update.message.reply_text(
            f"✅ Message sent to <code>{bc_uid}</code>\nMessage ID: <code>{data.get('message_id')}</code>",
            parse_mode=ParseMode.HTML,
        )
    except Exception as exc:
        await update.message.reply_text(f"❌ Send failed: {exc}")


async def markdone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update):
        return

    if not context.args:
        await update.message.reply_text("Usage: /markdone <BC.GAME UID>")
        return

    bc_uid = context.args[0].strip()
    try:
        data = await _api_post("/api/mark-done", ADMIN_PANEL_KEY, {"bc_uid": bc_uid})
        await update.message.reply_text(
            f"✅ Marked done: <code>{bc_uid}</code>\n"
            f"Deleted messages: <b>{data.get('deleted_messages', 0)}</b>\n"
            f"Notified: <b>{data.get('notified', False)}</b>",
            parse_mode=ParseMode.HTML,
        )
    except Exception as exc:
        await update.message.reply_text(f"❌ Mark done failed: {exc}")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update):
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return

    text = " ".join(context.args).strip()
    try:
        data = await _api_post("/api/broadcast", ADMIN_PANEL_KEY, {"text": text})
        job = data.get("job", {})
        await update.message.reply_text(
            f"✅ Broadcast started\nJob: <code>{job.get('id')}</code>\nTotal: <b>{job.get('total', 0)}</b>",
            parse_mode=ParseMode.HTML,
        )
    except Exception as exc:
        await update.message.reply_text(f"❌ Broadcast failed: {exc}")


async def syncusers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update):
        return

    try:
        data = await _api_post("/api/sync-users", ADMIN_PANEL_KEY, {})
        job = data.get("job", {})
        await update.message.reply_text(
            f"✅ Sync started\nJob: <code>{job.get('id')}</code>\nTotal: <b>{job.get('total', 0)}</b>",
            parse_mode=ParseMode.HTML,
        )
    except Exception as exc:
        await update.message.reply_text(f"❌ Sync failed: {exc}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update):
        return

    await update.message.reply_text(
        """
<b>Panel control commands</b>
/start - Show panel control info
/stats - Show panel statistics
/users - Show recent users
/refresh <uid> - Refresh a BC.GAME user
/sendmsg <uid> <message> - Send a direct message
/markdone <uid> - Mark a user done
/broadcast <message> - Broadcast to all users
/syncusers - Refresh all users from BC.GAME
        """.strip(),
        parse_mode=ParseMode.HTML,
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    if not await _require_admin(update):
        return

    await query.answer()
    action = query.data or ""
    if action in {"stats", "users", "syncusers", "broadcast", "help"}:
        await _run_named_action(update, context, action)
        return

    await _send_menu(update)


async def text_command_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update):
        return

    text = (update.message.text or "").strip()
    if not text:
        return

    lowered = text.lower()
    if lowered in {"menu", "start", "panel"}:
        await _send_menu(update)
        return

    if lowered in {"help", "stats", "users", "syncusers", "broadcast"}:
        command = lowered
        if command == "help":
            await help_command(update, context)
            return
        if command == "stats":
            await stats(update, context)
            return
        if command == "users":
            await users(update, context)
            return
        if command == "syncusers":
            await syncusers(update, context)
            return
        if command == "broadcast":
            await broadcast(update, context)
            return

    if lowered.startswith("refresh "):
        context.args = text.split()[1:]
        await refresh(update, context)
        return

    if lowered.startswith("sendmsg "):
        parts = text.split(maxsplit=2)
        context.args = parts[1:]
        await sendmsg(update, context)
        return

    if lowered.startswith("markdone "):
        context.args = text.split()[1:]
        await markdone(update, context)
        return

    if lowered.startswith("broadcast "):
        context.args = text.split(maxsplit=1)[1].split()
        await broadcast(update, context)
        return

    await _send_menu(
        update,
        "I did not recognize that command. Use /help or tap a button below.",
    )


def build_app() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("users", users))
    app.add_handler(CommandHandler("refresh", refresh))
    app.add_handler(CommandHandler("sendmsg", sendmsg))
    app.add_handler(CommandHandler("markdone", markdone))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("syncusers", syncusers))
    app.add_handler(CallbackQueryHandler(menu_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_command_router))
    return app


async def main():
    app = build_app()
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
