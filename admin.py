import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS
import database as db

logger = logging.getLogger(__name__)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to view bot statistics."""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ You are not authorized to use this command.")
        return
    
    stats = await db.get_stats()
    
    message = (
        f"📊 **Bot Statistics**\n\n"
        f"👥 Total Users: {stats['total_users']}\n"
        f"💬 Active Chats: {stats['active_chats']}\n"
        f"🔍 In Queue: {stats['in_queue']}"
    )
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin command to broadcast a message to all users.
    Usage:
    1. Reply to a message with /broadcast to send that message (text, photo, video, etc.)
    2. /broadcast <message> to send text
    """
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ You are not authorized to use this command.")
        return
    
    # Get target users (in production, fetch from DB)
    # For now, we'll just simulate or use a small list if available
    # Since we don't have a 'all_users' table easily accessible in this snippet, 
    # we'll assume the admin knows what they are doing or we fetch from stats
    
    # Fetch all users from user_settings (best approximation of total users)
    # Note: This might be slow if there are many users. In prod, use a generator or batching.
    try:
        if db.DB_TYPE == "sqlite":
            async with db.aiosqlite.connect(db.DB_PATH) as conn:
                async with conn.execute("SELECT user_id FROM user_settings") as cursor:
                    users = [row[0] for row in await cursor.fetchall()]
        else:
            # Supabase
            resp = db.supabase.table('user_settings').select('user_id').execute()
            users = [row['user_id'] for row in resp.data]
    except Exception as e:
        await update.message.reply_text(f"⚠️ Failed to fetch users: {e}")
        return

    if not users:
        await update.message.reply_text("⚠️ No users found to broadcast to.")
        return

    message_to_send = None
    is_reply = False
    
    if update.message.reply_to_message:
        is_reply = True
        message_to_send = update.message.reply_to_message
        confirm_msg = "this message (copy)"
    elif context.args:
        message_to_send = " ".join(context.args)
        confirm_msg = f"message: '{message_to_send}'"
    else:
        await update.message.reply_text(
            "Usage:\n"
            "1. Reply to a message with /broadcast\n"
            "2. /broadcast <message>"
        )
        return
    
    await update.message.reply_text(f"📢 Starting broadcast to {len(users)} users...\nContent: {confirm_msg}")
    
    success_count = 0
    fail_count = 0
    
    for uid in users:
        try:
            if is_reply:
                await message_to_send.copy(chat_id=uid)
            else:
                await context.bot.send_message(chat_id=uid, text=message_to_send, parse_mode='Markdown')
            success_count += 1
        except Exception as e:
            fail_count += 1
            # logger.error(f"Failed to broadcast to {uid}: {e}")
            
    await update.message.reply_text(
        f"✅ Broadcast complete!\n"
        f"Success: {success_count}\n"
        f"Failed: {fail_count}"
    )
    
    logger.info(f"Admin {user_id} broadcasted to {success_count} users (failed {fail_count})")
