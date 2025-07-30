""" User command handlers for No Mercy Zone Bot """

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup from telegram.ext import ContextTypes from telegram.constants import ParseMode from database import * from messages import * from utils import check_channel_membership, format_currency, get_ist_time, validate_utr from config import ADMIN_ID, CHANNEL_URL, UPI_ID, ADMIN_USERNAME from admin_handlers import handle_tournament_creation_steps

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE): """Handle /start command""" user = update.effective_user chat_id = update.effective_chat.id

if str(user.id) == str(ADMIN_ID):
    admin_welcome = f"""👑 Welcome back, Ghost Commander! 🧨

🔥 The Boss has entered the lobby! 💻 System ready for your commands... ⚡ All servers armed and operational!

Your domain awaits your orders! 💀""" await update.message.reply_text(admin_welcome) dashboard_msg = get_admin_dashboard_message() await update.message.reply_text(dashboard_msg) return

user_data = get_user(user.id)
if user_data and user_data.get("banned", False):
    await update.message.reply_text("🚫 You are banned from using this bot!")
    return

if not user_data:
    user_data = create_user(user.id, user.username, user.first_name)

welcome_msg = get_welcome_message(user.first_name)
await update.message.reply_text(welcome_msg)

is_member = await check_channel_membership(context.bot, user.id)

if not is_member:
    keyboard = [
        [InlineKeyboardButton("✅ Join Channel", url=CHANNEL_URL)],
        [InlineKeyboardButton("✅ I've Joined", callback_data="check_membership")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    channel_msg = get_channel_join_message()
    await update.message.reply_text(channel_msg, reply_markup=reply_markup)
else:
    await show_main_menu(update, context, user_data)

async def show_main_menu(update, context, user_data): menu_msg = get_main_menu_message(user_data["first_name"], user_data["referral_code"]) keyboard = [ [InlineKeyboardButton("🎮 Active Tournament", callback_data="active_tournament")], [InlineKeyboardButton("📜 Terms & Condition", callback_data="terms_condition")], [InlineKeyboardButton("👥 Invite Friends", callback_data="invite_friends")], [InlineKeyboardButton("📱 Share WhatsApp Status", callback_data="whatsapp_status")], [InlineKeyboardButton("📜 Match History", callback_data="match_history")], [InlineKeyboardButton("🆘 Help", callback_data="help")] ] reply_markup = InlineKeyboardMarkup(keyboard) if update.message: await update.message.reply_text(menu_msg, reply_markup=reply_markup) else: await update.callback_query.edit_message_text(menu_msg, reply_markup=reply_markup)

async def handle_tournament_join(update, context, tournament_id): user_id = update.effective_user.id user_data = get_user(user_id)

if not user_data.get("confirmed", False):
    msg = f"""💰 PAYMENT REQUIRED

Tournament join karne ke liye pehle payment karo:

1. UPI ID: {UPI_ID}


2. Amount pay karo


3. Screenshot bhejo {ADMIN_USERNAME} ko


4. /paid command use karke UTR enter karo


5. Admin approval ke baad join kar sakte ho



🚫 No payment, no entry! 🔥""" keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="active_tournament")]] await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard)) return

tournament = get_tournament(tournament_id)
if not tournament:
    await update.callback_query.edit_message_text("❌ Tournament not found.")
    return

entry_fee = tournament.get("entry_fee", 0)
if tournament_id in user_data.get("tournaments_joined", []):
    await update.callback_query.edit_message_text("⚠️ Aap pehle hi is tournament me entry le chuke ho.")
    return

if user_data.get("balance", 0) < entry_fee:
    await update.callback_query.edit_message_text("❌ Aapke paas tournament join karne ke liye balance nahi hai.")
    return

db.users.update_one({"user_id": user_id}, {"$inc": {"balance": -entry_fee}})
db.users.update_one({"user_id": user_id}, {"$addToSet": {"tournaments_joined": tournament_id}})

await update.callback_query.edit_message_text("✅ Successfully joined tournament!\n\nRoom details milenge match time pe. Ready raho! 🔥")

async def aihost(update: Update, context: ContextTypes.DEFAULT_TYPE): args = context.args

if not args:
    await update.message.reply_text(
        """🤖 *AI TOURNAMENT SUGGESTIONS*

📌 Usage: /aihost <type>

Available Types: • /aihost solo – AI Solo Tournament Suggestion
• /aihost duo – AI Duo Tournament Suggestion
• /aihost squad – AI Squad Tournament Suggestion

🧠 AI analysis ke saath smart profit-based suggestions pao!""", parse_mode=ParseMode.MARKDOWN ) return

type_arg = args[0].lower()
if type_arg not in ["solo", "duo", "squad"]:
    await update.message.reply_text("❌ Invalid type! Please use `solo`, `duo`, or `squad`.", parse_mode=ParseMode.MARKDOWN)
    return

await update.message.reply_text("🧠 AI is thinking... please wait ⏳")
prompt = f"Give me a profitable tournament idea for BGMI in {type_arg} mode with entry fees, rules, and admin profit analysis."
ai_response = context.bot.openai.ask(prompt)

await update.message.reply_text(f"✅ *AI Suggestion:*\n\n{ai_response}", parse_mode=ParseMode.MARKDOWN)
