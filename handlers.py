# handlers.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database import *
from messages import *
from utils import check_channel_membership, format_currency, get_ist_time, validate_utr
from config import ADMIN_ID, CHANNEL_URL, UPI_ID, ADMIN_USERNAME
from admin_handlers import handle_tournament_creation_steps
from database import get_ai_tournament_suggestion


# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        START_MESSAGE.format(name=update.effective_user.first_name),
        parse_mode=ParseMode.MARKDOWN,
    )


# /join command
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Please provide the Tournament ID to join.\nUsage: `/join <TournamentID>`", parse_mode=ParseMode.MARKDOWN)
        return

    tournament_id = args[0]
    user_id = update.effective_user.id

    # Check if tournament exists
    tournament = db.tournaments.find_one({"tournament_id": tournament_id})
    if not tournament:
        await update.message.reply_text("❌ Invalid Tournament ID.")
        return

    # Check if user already joined
    if tournament_id in db.users.find_one({"user_id": user_id})["tournaments_joined"]:
        await update.message.reply_text("✅ You have already joined this tournament.")
        return

    # Add user to tournament
    db.users.update_one(
        {"user_id": user_id},
        {"$addToSet": {"tournaments_joined": tournament_id}}
    )

    await update.message.reply_text(f"✅ Successfully joined Tournament `{tournament_id}`!", parse_mode=ParseMode.MARKDOWN)


# /aihost command - AI Suggestion
async def aihost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args

    if not args:
        await update.message.reply_text(
            """🤖 *AI TOURNAMENT SUGGESTIONS*

📌 Usage: /aihost <type>

Available Types:
• /aihost solo – AI Solo Tournament Suggestion
• /aihost duo – AI Duo Tournament Suggestion
• /aihost squad – AI Squad Tournament Suggestion

🧠 AI analysis ke saath smart profit-based suggestions pao!""",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    type_arg = args[0].lower()
    if type_arg not in ["solo", "duo", "squad"]:
        await update.message.reply_text("❌ Invalid type! Please use `solo`, `duo`, or `squad`.", parse_mode=ParseMode.MARKDOWN)
        return

    suggestion = get_ai_tournament_suggestion(type_arg)
    await update.message.reply_text(
        f"🤖 *AI Suggestion for {type_arg.capitalize()} Tournament:*\n\n{suggestion}",
        parse_mode=ParseMode.MARKDOWN
    )


# /profile command
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.users.find_one({"user_id": user_id})

    if not user:
        await update.message.reply_text("❌ Profile not found. Please use /start first.")
        return

    tournaments = user.get("tournaments_joined", [])
    balance = user.get("balance", 0)

    text = f"""👤 *Your Profile*

🆔 ID: `{user_id}`
💰 Balance: ₹{balance}
🏆 Tournaments Joined: {len(tournaments)}

🗓️ Last Active: {get_ist_time()}
"""
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
