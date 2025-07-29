#!/usr/bin/env python3
"""
🚫 No Mercy Zone Bot 🚫
BGMI Tournament Management Bot with Payment Processing
"""

import logging
import os
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import *
from handlers import *
from admin_handlers import *
from database import init_database

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Start the bot."""
    # Initialize database
    init_database()
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Register handlers
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("paid", paid_command))
    application.add_handler(CommandHandler("matchhistory", match_history_command))
    
    # Admin command handlers
    application.add_handler(CommandHandler("host", host_command))
    application.add_handler(CommandHandler("aihost", ai_host_command))
    application.add_handler(CommandHandler("active", active_tournaments_command))
    application.add_handler(CommandHandler("droproom", drop_room_command))
    application.add_handler(CommandHandler("listplayers", list_players_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("datavault", data_vault_command))
    application.add_handler(CommandHandler("special", special_command))
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("confirm", confirm_payment_command))
    application.add_handler(CommandHandler("decline", decline_payment_command))
    application.add_handler(CommandHandler("approve_ai", approve_ai_command))
    application.add_handler(CommandHandler("aianalytics", ai_analytics_command))
    application.add_handler(CommandHandler("dashboard", admin_dashboard_command))
    
    # Callback query handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Run the bot
    logger.info("🚫 No Mercy Zone Bot starting...")
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == '__main__':
    main()
