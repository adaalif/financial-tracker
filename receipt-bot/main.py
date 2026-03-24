import os
from telegram.ext import Application, MessageHandler, filters
from config import TELEGRAM_BOT_TOKEN
from utils.logger import setup_logging, get_logger

# Real handler module integration
from bot.handlers import handle_receipt_photo

def main() -> None:
    # 1. Initialize structured JSON logging
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Starting up Receipt Processor Bot...")

    # 2. Build the Telegram application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # 3. Register handlers
    # Bind the internal handler to ANY incoming message that contains a PHOTO
    application.add_handler(MessageHandler(filters.PHOTO, handle_receipt_photo))
    
    logger.info("Bot is initialized and polling for messages...")
    
    # 4. Start polling
    application.run_polling()

if __name__ == "__main__":
    main()
