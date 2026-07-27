"""
Admin Commands Module - Complete Rewrite
"""
import asyncio
import html
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import RetryAfter

from config import (
    ADMIN_IDS,
    ADMIN_PANEL_PUBLIC_URL,
    BROADCAST_BATCH_SIZE,
    DONE_BANNER_URL,
    WEBAPP_URL,
)
from database import Database
import logging

logger = logging.getLogger(__name__)

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS

def _admin_menu_markup() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("📝 Send Message", callback_data="admin_send_message"),
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
        ],
        [
            InlineKeyboardButton("✅ Mark Done", callback_data="admin_mark_done"),
            InlineKeyboardButton("👥 Users", callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton("⏳ Pending", callback_data="admin_pending"),
            InlineKeyboardButton("📊 Statistics", callback_data="admin_stats"),
        ],
    ]

    if ADMIN_PANEL_PUBLIC_URL:
        keyboard.append([InlineKeyboardButton("🌐 Web Admin Panel", url=ADMIN_PANEL_PUBLIC_URL)])

    return InlineKeyboardMarkup(keyboard)

def _reset_admin_flow(context: ContextTypes.DEFAULT_TYPE):
    context.user_data['admin_flow'] = None
    context.user_data['admin_step'] = None
    context.user_data['admin_payload'] = {}
    context.user_data['target_user_id'] = None
    context.user_data['target_bc_uid'] = None

def _display_user(user: dict) -> str:
    bc_uid = user.get('bc_uid') or 'N/A'
    bc_data = Database._safe_bc_data(user)
    bc_username = bc_data.get('name') or user.get('username') or 'User'
    level_name = user.get('level_name') or f"VIP {user.get('level', 0)}"
    done = "Done" if int(user.get('marked_done') or 0) else "Active"
    return f"{html.escape(str(bc_username))} | UID {html.escape(str(bc_uid))} | {html.escape(str(level_name))} | {done}"

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show enhanced admin panel"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ You don't have admin access.")
        return

    await update.message.reply_text(
        "🔧 <b>Admin Panel</b>\n\n"
        "Send Message is unchanged. Broadcast now runs in the background with progress updates.",
        reply_markup=_admin_menu_markup(),
        parse_mode=ParseMode.HTML
    )

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel callbacks"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.message.edit_text("⛔ You don't have admin access.")
        return
    
    action = query.data
    
    if action == "admin_stats":
        await show_statistics(query, context)
    elif action == "admin_refresh_stats":
        await refresh_data(query, context)
    elif action == "admin_pending":
        await show_pending_verifications(query, context)
    elif action == "admin_broadcast":
        await start_broadcast(query, context)
    elif action == "admin_send_message":
        await start_send_message(query, context)
    elif action == "admin_mark_done":
        await start_mark_done(query, context)
    elif action == "admin_users":
        await show_users(query, context)
    elif action == "admin_back":
        await show_admin_menu(query, context)
    elif action.startswith("user_"):
        await show_user_details(query, context)
    elif action.startswith("show_errors_"):
        await show_verification_errors(query, context)

async def show_verification_errors(query, context):
    """Show verification error options for admin"""
    user_id = int(query.data.replace("show_errors_", ""))
    
    # Store user_id in context for error handling
    context.user_data['pending_verification_user'] = user_id
    
    keyboard = [
        [InlineKeyboardButton("❌ Incorrect Email", callback_data=f"verify_error_email")],
        [InlineKeyboardButton("❌ Incorrect Phone", callback_data=f"verify_error_phone")],
        [InlineKeyboardButton("❌ 2FA Issue", callback_data=f"verify_error_2fa")],
        [InlineKeyboardButton("❌ 2FA Reused", callback_data=f"verify_error_2fa_reuse")],
        [InlineKeyboardButton("« Back", callback_data="admin_pending")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        f"⚠️ <b>Select Verification Error</b>\n\n"
        f"User ID: <code>{user_id}</code>\n\n"
        f"Select the error type to send to user:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def show_pending_verifications(query, context):
    """Show users pending verification with admin controls"""
    pending_users = await Database.get_pending_verifications()
    
    if not pending_users:
        keyboard = [[InlineKeyboardButton("« Back", callback_data="admin_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            "✅ No pending verifications",
            reply_markup=reply_markup
        )
        return
    
    text = f"⏳ <b>Pending Verifications</b> ({len(pending_users)})\n\n"
    
    for user in pending_users[:10]:  # Show first 10
        username = user.get('username', 'Unknown')
        telegram_id = user.get('telegram_id')
        bc_uid = user.get('bc_uid')
        level = user.get('level', 0)
        
        text += f"👤 {username} (ID: {telegram_id})\n"
        text += f"   UID: {bc_uid} | Level: {level}\n\n"
    
    keyboard = []
    for user in pending_users[:5]:  # Buttons for first 5
        telegram_id = user.get('telegram_id')
        username = user.get('username', 'Unknown')
        keyboard.append([
            InlineKeyboardButton(
                f"✅ Verify {username}",
                callback_data=f"verify_user_{telegram_id}"
            ),
            InlineKeyboardButton(
                f"❌ Error",
                callback_data=f"show_errors_{telegram_id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("« Back", callback_data="admin_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def show_user_details(query, context):
    """Show detailed user information with verification options"""
    user_id = int(query.data.replace("user_", "").split("_")[0])
    
    user_data = await Database.get_user_by_telegram_id(user_id)
    
    if not user_data:
        await query.message.edit_text("❌ User not found")
        return
    
    username = user_data.get('username', 'Unknown')
    bc_uid = user_data.get('bc_uid')
    level = user_data.get('level', 0)
    verified = user_data.get('verified', 0)
    verification_status = user_data.get('verification_status', '')
    
    text = (
        f"👤 <b>User Details</b>\n\n"
        f"Username: <b>{username}</b>\n"
        f"Telegram ID: <code>{user_id}</code>\n"
        f"BC.GAME UID: <code>{bc_uid}</code>\n"
        f"Level: <b>{level}</b>\n"
        f"Verified: <b>{'Yes' if verified else 'No'}</b>\n"
    )
    
    if verification_status:
        text += f"Status: <i>{verification_status}</i>\n"
    
    keyboard = []
    
    if not verified:
        keyboard.append([
            InlineKeyboardButton("✅ Verify User", callback_data=f"verify_user_{user_id}")
        ])
        keyboard.append([
            InlineKeyboardButton("❌ Verification Errors", callback_data=f"show_errors_{user_id}")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton("🔓 Revoke Verification", callback_data=f"revoke_verify_{user_id}")
        ])
    
    keyboard.append([InlineKeyboardButton("« Back", callback_data="admin_pending")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def show_statistics(query, context):
    """Show bot statistics"""
    await Database.update_statistics()
    stats = await Database.get_statistics()
    top_levels = stats.get('top_levels') or []
    top_level_text = "No level data yet"
    if top_levels:
        top_level_text = "\n".join(
            f"• {html.escape(str(item.get('level_name', 'VIP 0')))}: <b>{item.get('count', 0)}</b>"
            for item in top_levels
        )
    
    text = (
        "📊 <b>Bot Statistics</b>\n\n"
        f"👥 Total Users: <b>{stats.get('total_users', 0)}</b>\n"
        f"🎯 Eligible Users: <b>{stats.get('eligible_users', 0)}</b>\n"
        f"✅ Verified Users: <b>{stats.get('verified_users', 0)}</b>\n"
        f"⏳ Pending Verification: <b>{stats.get('pending_users', 0)}</b>\n"
        f"🏁 Marked Done: <b>{stats.get('marked_done_users', 0)}</b>\n"
        f"🟢 Active Users: <b>{stats.get('active_users', 0)}</b>\n"
        f"🎁 Total Claims: <b>{stats.get('total_claims', 0)}</b>\n"
        f"⭐ Average Level: <b>{float(stats.get('average_level', 0)):.1f}</b>\n"
        f"🏆 Highest Level: <b>{stats.get('highest_level', 0)}</b>\n\n"
        f"<b>Top Levels</b>\n{top_level_text}\n\n"
        f"📅 Last Updated: <code>{stats.get('last_updated', 'N/A')}</code>"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh_stats")],
        [InlineKeyboardButton("« Back", callback_data="admin_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def show_users(query, context):
    """Show user list"""
    users = await Database.get_all_users()
    
    if not users:
        text = "📭 No users found."
    else:
        text = f"👥 <b>User List</b> ({len(users)} users)\n\n"
        for i, user in enumerate(users[:15], 1):  # Show first 15
            verified_status = "✅" if user.get('verified', 0) else "⏳"
            done_status = "🏁" if int(user.get('marked_done') or 0) else "🟢"
            bc_data = Database._safe_bc_data(user)
            bc_username = bc_data.get('name') or user.get('username', 'Unknown')
            level_display = user.get('level_name') or f"VIP {user.get('level', 0)}"
            text += (
                f"{i}. {verified_status}{done_status} <b>{html.escape(str(bc_username))}</b>\n"
                f"   TG: <code>{user.get('telegram_id')}</code> | @{html.escape(str(user.get('username') or 'N/A'))}\n"
                f"   UID: <code>{html.escape(str(user.get('bc_uid', 'N/A')))}</code> | {html.escape(str(level_display))}\n\n"
            )
        
        if len(users) > 15:
            text += f"\n... and {len(users) - 15} more users. Use the web admin panel for the full scroll list."
    
    keyboard = [[InlineKeyboardButton("« Back", callback_data="admin_back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def start_broadcast(query, context):
    """Start broadcast mode"""
    await query.message.edit_text(
        "📢 <b>Broadcast</b>\n\n"
        "Step 1/3: Send an image, or type <code>skip</code>.",
        parse_mode=ParseMode.HTML
    )
    context.user_data['admin_flow'] = 'broadcast'
    context.user_data['admin_step'] = 'await_image'
    context.user_data['admin_payload'] = {}

async def start_send_message(query, context):
    """Start send message to a specific user by BC UID"""
    await query.message.edit_text(
        "📝 <b>Send Message</b>\n\n"
        "Enter the BC.GAME UID of the recipient:",
        parse_mode=ParseMode.HTML
    )
    context.user_data['admin_flow'] = 'send_message'
    context.user_data['admin_step'] = 'await_uid'
    context.user_data['admin_payload'] = {}

async def start_mark_done(query, context):
    """Start mark-done flow for a user"""
    await query.message.edit_text(
        "✅ <b>Mark User Done</b>\n\n"
        "Enter the BC.GAME UID. I will mark the user as done, clear tracked bot messages, "
        "and send the congratulations banner button.",
        parse_mode=ParseMode.HTML
    )
    context.user_data['admin_flow'] = 'mark_done'
    context.user_data['admin_step'] = 'await_uid'
    context.user_data['admin_payload'] = {}

def _is_skip(text: str) -> bool:
    if not text:
        return False
    return text.strip().lower() in {"skip", "scip"}

def _parse_buttons(text: str):
    if not text:
        return []
    buttons = []
    for raw in text.split(','):
        if '|' not in raw:
            return None
        label, url = raw.split('|', 1)
        label = label.strip()
        url = url.strip()
        if not label or not url:
            return None
        buttons.append(InlineKeyboardButton(label, url=url))
    return buttons

async def _send_composed_message(bot, chat_id: int, payload: dict):
    text = payload.get('text')
    photo = payload.get('photo')
    buttons = payload.get('buttons') or []
    reply_markup = InlineKeyboardMarkup([[b] for b in buttons]) if buttons else None

    if photo:
        msg = await bot.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=text or "",
            parse_mode=ParseMode.HTML if text else None,
            reply_markup=reply_markup
        )
    else:
        body = text if text is not None else " "
        msg = await bot.send_message(
            chat_id=chat_id,
            text=body,
            parse_mode=ParseMode.HTML if text else None,
            reply_markup=reply_markup
        )

    await Database.record_bot_message(chat_id, msg.message_id)
    return msg

async def _send_done_congratulations(bot, user_data: dict):
    telegram_id = user_data.get('telegram_id')
    bc_uid = user_data.get('bc_uid')
    bc_data = Database._safe_bc_data(user_data)
    username = bc_data.get('name') or user_data.get('username') or 'User'
    text = (
        f"🎉 <b>Congratulations, {html.escape(str(username))}!</b>\n\n"
        "Your bonus request is completed. Tap the button below to view your reward."
    )
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 View Bonus", web_app=WebAppInfo(url=DONE_BANNER_URL))]
    ])

    try:
        msg = await bot.send_photo(
            chat_id=telegram_id,
            photo=DONE_BANNER_URL,
            caption=text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    except Exception:
        msg = await bot.send_message(
            chat_id=telegram_id,
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )

    await Database.record_bot_message(telegram_id, msg.message_id)
    return msg

async def _clear_tracked_user_messages(bot, telegram_id: int) -> int:
    deleted = 0
    message_ids = await Database.get_bot_messages(telegram_id)
    for message_id in message_ids:
        try:
            await bot.delete_message(chat_id=telegram_id, message_id=message_id)
            deleted += 1
        except Exception as e:
            logger.warning(f"Failed to delete message {message_id} for {telegram_id}: {e}")
    await Database.clear_bot_messages(telegram_id)
    return deleted

async def _mark_user_done_and_notify(update: Update, context: ContextTypes.DEFAULT_TYPE, user_data: dict):
    telegram_id = user_data.get('telegram_id')
    bc_uid = user_data.get('bc_uid')
    if not telegram_id:
        await update.message.reply_text("❌ User record has no Telegram ID.")
        return

    result = await mark_user_done(context.bot, user_data)
    deleted = result.get('deleted_messages', 0)
    notify_line = "Congratulations banner sent."
    if not result.get('notified'):
        notify_line = f"Marked done, but notification failed: {result.get('error')}"

    await update.message.reply_text(
        f"✅ Marked UID {bc_uid} as done.\n"
        f"Cleared {deleted} tracked bot messages.\n"
        f"{notify_line}"
    )

async def mark_user_done(bot, user_data: dict) -> dict:
    """Mark a user done, clear tracked bot messages, and send the done banner."""
    telegram_id = user_data.get('telegram_id')
    await Database.set_marked_done(telegram_id, 1)
    deleted = await _clear_tracked_user_messages(bot, telegram_id)
    notified = True
    error = None
    try:
        await _send_done_congratulations(bot, user_data)
    except Exception as e:
        notified = False
        error = str(e)
        logger.error(f"Marked user {telegram_id} done, but failed to send congratulations: {e}")
    await Database.update_statistics()
    return {
        'deleted_messages': deleted,
        'notified': notified,
        'error': error,
    }

def _broadcast_progress_text(total: int, success_count: int, fail_count: int, latest_batch: list, done: bool = False) -> str:
    status = "✅ <b>Broadcast Complete</b>" if done else "📢 <b>Broadcast Running</b>"
    sent_lines = "\n".join(
        f"• {html.escape(item)}"
        for item in latest_batch
    ) or "No successful sends in this batch."
    return (
        f"{status}\n\n"
        f"Total users: <b>{total}</b>\n"
        f"Sent: <b>{success_count}</b>\n"
        f"Failed: <b>{fail_count}</b>\n"
        f"Updated: <code>{datetime.now().strftime('%H:%M:%S')}</code>\n\n"
        f"<b>Latest batch</b>\n{sent_lines}"
    )

async def _run_broadcast_job(bot, users: list, payload: dict, status_chat_id: int, status_message_id: int):
    total = len(users)
    success_count = 0
    fail_count = 0
    latest_batch = []

    if not users:
        await bot.edit_message_text(
            chat_id=status_chat_id,
            message_id=status_message_id,
            text="📢 Broadcast cancelled: no users found."
        )
        return

    for user in users:
        label = _display_user(user)
        try:
            await _send_composed_message(bot, user['telegram_id'], payload)
            success_count += 1
            latest_batch.append(label)
        except RetryAfter as e:
            await asyncio.sleep(float(e.retry_after) + 1)
            try:
                await _send_composed_message(bot, user['telegram_id'], payload)
                success_count += 1
                latest_batch.append(label)
            except Exception as retry_error:
                logger.error(f"Failed to send to {user['telegram_id']} after retry: {retry_error}")
                fail_count += 1
        except Exception as e:
            logger.error(f"Failed to send to {user['telegram_id']}: {e}")
            fail_count += 1

        if success_count and success_count % BROADCAST_BATCH_SIZE == 0:
            try:
                await bot.edit_message_text(
                    chat_id=status_chat_id,
                    message_id=status_message_id,
                    text=_broadcast_progress_text(total, success_count, fail_count, latest_batch[-BROADCAST_BATCH_SIZE:]),
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                logger.warning(f"Failed to edit broadcast progress: {e}")

        await asyncio.sleep(0.05)

    try:
        await bot.edit_message_text(
            chat_id=status_chat_id,
            message_id=status_message_id,
            text=_broadcast_progress_text(total, success_count, fail_count, latest_batch[-BROADCAST_BATCH_SIZE:], done=True),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.warning(f"Failed to edit final broadcast progress: {e}")

async def _prompt_step(update: Update, step: str):
    if step == 'await_image':
        await update.message.reply_text(
            "Step 1/3: Send an image, or type <code>skip</code>.",
            parse_mode=ParseMode.HTML
        )
    elif step == 'await_text':
        await update.message.reply_text(
            "Step 2/3: Send the text, or type <code>skip</code>.",
            parse_mode=ParseMode.HTML
        )
    elif step == 'await_buttons':
        await update.message.reply_text(
            "Step 3/3: Send buttons as <code>Label|URL, Label2|URL2</code>, or type <code>skip</code>.",
            parse_mode=ParseMode.HTML
        )

async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin input for send/broadcast/mark-done flows"""
    if not is_admin(update.effective_user.id):
        return

    flow = context.user_data.get('admin_flow')
    step = context.user_data.get('admin_step')
    payload = context.user_data.get('admin_payload') or {}

    if not flow or not step:
        return

    if step == 'await_uid':
        if not update.message.text or not update.message.text.strip().isdigit():
            await update.message.reply_text("❌ Enter a numeric BC.GAME UID.")
            return

        bc_uid = update.message.text.strip()
        user_data = await Database.get_user_by_bc_uid(bc_uid)
        if not user_data:
            await update.message.reply_text("❌ User not found for that BC.GAME UID.")
            return

        if flow == 'mark_done':
            await _mark_user_done_and_notify(update, context, user_data)
            _reset_admin_flow(context)
            return

        context.user_data['target_user_id'] = user_data.get('telegram_id')
        context.user_data['target_bc_uid'] = bc_uid
        context.user_data['admin_step'] = 'await_image'
        await _prompt_step(update, 'await_image')
        return

    if step == 'await_image':
        if update.message.photo:
            payload['photo'] = update.message.photo[-1].file_id
        elif update.message.text and _is_skip(update.message.text):
            payload['photo'] = None
        else:
            await update.message.reply_text("❌ Send a photo, or type <code>skip</code>.", parse_mode=ParseMode.HTML)
            return

        context.user_data['admin_payload'] = payload
        context.user_data['admin_step'] = 'await_text'
        await _prompt_step(update, 'await_text')
        return

    if step == 'await_text':
        if update.message.text and not _is_skip(update.message.text):
            payload['text'] = update.message.text
        elif update.message.text and _is_skip(update.message.text):
            payload['text'] = None
        else:
            await update.message.reply_text("❌ Send text, or type <code>skip</code>.", parse_mode=ParseMode.HTML)
            return

        context.user_data['admin_payload'] = payload
        context.user_data['admin_step'] = 'await_buttons'
        await _prompt_step(update, 'await_buttons')
        return

    if step == 'await_buttons':
        if update.message.text and _is_skip(update.message.text):
            payload['buttons'] = []
        elif update.message.text:
            buttons = _parse_buttons(update.message.text)
            if buttons is None:
                await update.message.reply_text(
                    "❌ Invalid button format. Use <code>Label|URL, Label2|URL2</code> or type <code>skip</code>.",
                    parse_mode=ParseMode.HTML
                )
                return
            payload['buttons'] = buttons
        else:
            await update.message.reply_text("❌ Send button text, or type <code>skip</code>.", parse_mode=ParseMode.HTML)
            return

        context.user_data['admin_payload'] = payload

        if flow == 'broadcast':
            users = await Database.get_all_users()
            status_msg = await update.message.reply_text(
                f"📢 Broadcast queued for {len(users)} users.\n"
                f"I will update this message every {BROADCAST_BATCH_SIZE} successful sends."
            )
            context.application.create_task(
                _run_broadcast_job(
                    context.bot,
                    users,
                    dict(payload),
                    status_msg.chat_id,
                    status_msg.message_id
                )
            )
        else:
            target_user_id = context.user_data.get('target_user_id')
            target_bc_uid = context.user_data.get('target_bc_uid')
            if not target_user_id:
                await update.message.reply_text("❌ Session expired. Please try again.")
                return

            try:
                await _send_composed_message(context.bot, target_user_id, payload)
                await update.message.reply_text(
                    f"✅ Sent to user UID {target_bc_uid}"
                )
            except Exception as e:
                await update.message.reply_text(f"❌ Failed to send: {e}")

        _reset_admin_flow(context)
        return

async def show_admin_menu(query, context):
    """Show main admin menu"""
    await query.message.edit_text(
        "🔧 <b>Admin Panel</b>\n\n"
        "Send Message is unchanged. Broadcast now runs in the background with progress updates.",
        reply_markup=_admin_menu_markup(),
        parse_mode=ParseMode.HTML
    )

async def refresh_data(query, context):
    """Refresh database statistics"""
    await Database.update_statistics()
    await show_statistics(query, context)
