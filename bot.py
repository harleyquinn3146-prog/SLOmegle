import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN
import database as db
from handlers import (
    start, 
    button_handler, 
    handle_message, 
    handle_edit, 
    delete_command,
    next_command,
    stop_command,
    language_command
)
from admin import stats_command, broadcast_command

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def create_app():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Initialize database on startup
    async def post_init(application: Application):
        await db.init_db()
        
        # Set Bot Commands
        from telegram import BotCommand
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("next", "Find next partner"),
            BotCommand("stop", "End current chat"),
            BotCommand("language", "Change language / භාෂාව වෙනස් කරන්න"),
            BotCommand("broadcast", "Admin Broadcast (Admin only)"),
            BotCommand("stats", "Bot Stats (Admin only)")
        ]
        await application.bot.set_my_commands(commands)
        
        # Set Chat Menu Button
        from telegram import MenuButtonCommands
        await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    
    app.post_init = post_init
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("next", next_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("delete", delete_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    # Handle edited messages
    app.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE, handle_edit))
    # Update filter to accept all types of messages except commands
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    
    return app

def main():
    app = create_app()
    logger.info("Bot started with polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
