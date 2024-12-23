import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from src.bot.telegram_bot import KurisuBot
from src.bot.handlers import CommandHandlers
from config.config import config

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    # Initialize bot and handlers
    bot = KurisuBot()
    handlers = CommandHandlers(bot)
    
    # Create application
    application = Application.builder().token(config.TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("add_task", handlers.add_task))
    application.add_handler(CommandHandler("list_tasks", handlers.list_tasks))
    application.add_handler(CommandHandler("complete_task", handlers.complete_task))
    application.add_handler(CommandHandler("pause_notifications", handlers.pause_notifications))
    application.add_handler(CommandHandler("resume_notifications", handlers.resume_notifications))
    
    # Add message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    # Start the bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)