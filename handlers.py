"""
User command handlers for No Mercy Zone Bot
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import *
from messages import *
from utils import check_channel_membership, format_currency, get_ist_time, validate_utr
from config import ADMIN_ID, CHANNEL_URL, UPI_ID, ADMIN_USERNAME
from admin_handlers import handle_tournament_creation_steps

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Check if user is admin first
    if str(user.id) == str(ADMIN_ID):
        # Admin gets special welcome and dashboard
        admin_welcome = f"""👑 Welcome back, Ghost Commander! 🧨

🔥 The Boss has entered the lobby! 
💻 System ready for your commands...
⚡ All servers armed and operational!

Your domain awaits your orders! 💀"""
        
        await update.message.reply_text(admin_welcome)
        
        # Show admin dashboard
        dashboard_msg = get_admin_dashboard_message()
        await update.message.reply_text(dashboard_msg)
        return
    
    # Check if user is banned
    user_data = get_user(user.id)
    if user_data and user_data.get("banned", False):
        await update.message.reply_text("🚫 You are banned from using this bot!")
        return
    
    # Create or get user
    if not user_data:
        user_data = create_user(user.id, user.username, user.first_name)
    
    # Send welcome message
    welcome_msg = get_welcome_message(user.first_name)
    await update.message.reply_text(welcome_msg)
    
    # Check channel membership
    is_member = await check_channel_membership(context.bot, user.id)
    
    if not is_member:
        # Show channel join button
        keyboard = [
            [InlineKeyboardButton("✅ Join Channel", url=CHANNEL_URL)],
            [InlineKeyboardButton("✅ I've Joined", callback_data="check_membership")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        channel_msg = get_channel_join_message()
        await update.message.reply_text(
            channel_msg,
            reply_markup=reply_markup
        )
    else:
        # Show main menu
        await show_main_menu(update, context, user_data)

async def show_main_menu(update, context, user_data):
    """Show main menu to user"""
    menu_msg = get_main_menu_message(user_data["first_name"], user_data["referral_code"])
    
    keyboard = [
        [InlineKeyboardButton("🎮 Active Tournament", callback_data="active_tournament")],
        [InlineKeyboardButton("📜 Terms & Condition", callback_data="terms_condition")],
        [InlineKeyboardButton("👥 Invite Friends", callback_data="invite_friends")],
        [InlineKeyboardButton("📱 Share WhatsApp Status", callback_data="whatsapp_status")],
        [InlineKeyboardButton("📜 Match History", callback_data="match_history")],
        [InlineKeyboardButton("🆘 Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(menu_msg, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(menu_msg, reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_data = get_user(user_id)
    
    if query.data == "check_membership":
        is_member = await check_channel_membership(context.bot, user_id)
        if is_member:
            update_user(user_id, {"is_member": True})
            await show_main_menu(update, context, user_data)
        else:
            await query.edit_message_text(
                "❌ Channel abhi bhi join nahi kiya! Pehle join karo:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Join Channel", url=CHANNEL_URL)],
                    [InlineKeyboardButton("✅ I've Joined", callback_data="check_membership")]
                ])
            )
    
    elif query.data == "active_tournament":
        await show_active_tournaments(update, context)
    
    elif query.data == "terms_condition":
        rules_msg = get_rules_message()
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
        await query.edit_message_text(
            rules_msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == "invite_friends":
        referral_msg = f"""👥 INVITE FRIENDS & EARN FREE ENTRIES

🎯 Your Personal Referral Code: {user_data['referral_code']}

📤 How to Share:
1. Copy your referral code
2. Share with friends
3. When they join using your code, you get free entry!

🔗 Share Link:
https://t.me/YourBotUsername?start={user_data['referral_code']}

💰 Benefits:
• 1 referral = 1 free tournament entry
• Unlimited referrals allowed
• Instant credit on successful referral

🚫 No Mercy Zone mein dost bhi competition hai! 🔥"""
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
        await query.edit_message_text(
            referral_msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == "whatsapp_status":
        status_template = get_whatsapp_status_template(user_data['referral_code'])
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
        await query.edit_message_text(
            f"📱 WHATSAPP STATUS TEMPLATE\n\nCopy and paste this as your WhatsApp status:\n\n{status_template}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == "match_history":
        await show_match_history(update, context)
    
    elif query.data == "help":
        help_msg = get_help_message()
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
        await query.edit_message_text(
            help_msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == "back_to_menu":
        await show_main_menu(update, context, user_data)
    
    elif query.data.startswith("join_tournament_"):
        tournament_id = query.data.replace("join_tournament_", "")
        await handle_tournament_join(update, context, tournament_id)

async def show_active_tournaments(update, context):
    """Show active tournaments"""
    tournaments = get_active_tournaments()
    
    if not tournaments:
        msg = "🚫 Koi active tournament nahi hai abhi!\n\nJaldi hi naya tournament aayega. Channel pe active raho! 🔥"
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
        await update.callback_query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    msg = "🎮 ACTIVE TOURNAMENTS\n\n"
    keyboard = []
    
    for tournament in tournaments:
        tournament_post = get_tournament_post(tournament)
        msg += tournament_post + "\n\n"
        
        keyboard.append([
            InlineKeyboardButton(
                f"✅ Join {tournament['name']}", 
                callback_data=f"join_tournament_{tournament['tournament_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")])
    
    await update.callback_query.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_tournament_join(update, context, tournament_id):
    """Handle tournament join request"""
    user_id = update.effective_user.id
    user_data = get_user(user_id)
    
    # Check if user is confirmed
    if not user_data.get("confirmed", False):
        msg = f"""💰 PAYMENT REQUIRED

Tournament join karne ke liye pehle payment karo:

1. UPI ID: {UPI_ID}
2. Amount pay karo
3. Screenshot bhejo {ADMIN_USERNAME} ko
4. /paid command use karke UTR enter karo
5. Admin approval ke baad join kar sakte ho

🚫 No payment, no entry! 🔥"""
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="active_tournament")]]
        await update.callback_query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Join tournament
    success = join_tournament(user_id, tournament_id)
    
    if success:
        msg = "✅ Successfully joined tournament!\n\nRoom details milenge match time pe. Ready raho! 🔥"
    else:
        msg = "❌ Tournament join nahi ho saka. Admin se contact karo."
    
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="active_tournament")]]
    await update.callback_query.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_match_history(update, context):
    """Show user's match history"""
    user_id = update.effective_user.id
    user_data = get_user(user_id)
    
    tournaments_joined = user_data.get("tournaments_joined", [])
    
    if not tournaments_joined:
        msg = "📜 Abhi tak koi tournament join nahi kiya!\n\nPehla tournament join karo aur history banao! 🎮"
    else:
        msg = f"📜 *YOUR TOURNAMENT HISTORY*\n\n"
        msg += f"🎮 Total Tournaments: {len(tournaments_joined)}\n"
        msg += f"💰 Total Spent: {format_currency(user_data.get('total_spent', 0))}\n"
        msg += f"🏆 Total Earned: {format_currency(user_data.get('total_earned', 0))}\n\n"
        msg += "Recent tournaments will be shown here..."
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
    await update.callback_query.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def paid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /paid command"""
    user_id = update.effective_user.id
    
    # Don't process if admin is sending the command
    if str(user_id) == str(ADMIN_ID):
        await update.message.reply_text("👑 Admin detected! Payment verification skipped.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ UTR number missing!\n\nUse: /paid <UTR_NUMBER>\nExample: /paid 123456789012"
        )
        return
    
    utr = context.args[0]
    
    if not validate_utr(utr):
        await update.message.reply_text(
            "❌ Invalid UTR number!\nUTR should be at least 10 digits."
        )
        return
    
    # Create payment request
    user_data = get_user(user_id)
    
    msg = f"""✅ Payment request submitted!

UTR: `{utr}`
Status: Pending admin approval

{ADMIN_USERNAME} will verify and confirm shortly. 
Notification milega confirmation ke baad! 🔥"""
    
    await update.message.reply_text(msg, parse_mode='Markdown')
    
    # Forward to admin (but not if admin sent it)
    admin_msg = f"""💰 *PAYMENT VERIFICATION REQUEST*

👤 User: {user_data.get('first_name', 'Unknown')} (@{user_data.get('username', 'no_username')})
🆔 User ID: `{user_id}`
🧾 UTR: `{utr}`

Use: /confirm {user_id} or /decline {user_id}"""
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_msg,
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Failed to forward payment to admin: {e}")

async def match_history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /matchhistory command"""
    await show_match_history(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_msg = get_help_message()
    await update.message.reply_text(help_msg, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages"""
    user_id = update.effective_user.id
    
    # Check if admin is in tournament creation process
    if str(user_id) == str(ADMIN_ID):
        if await handle_tournament_creation_steps(update, context):
            return
    
    # Check if user is trying to interact without joining channel
    is_member = await check_channel_membership(context.bot, user_id)
    
    if not is_member:
        msg = "❌ Pehle channel join karo!\n\n/start command use karo."
        await update.message.reply_text(msg)
        return
    
    # Default response
    await update.message.reply_text(
        "🤖 Command samajh nahi aaya!\n\nMenu use karo ya /help dekho."
    )

async def aihost_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /aihost command for AI tournament suggestion"""
    if not context.args:
        await update.message.reply_text(
            "🤖 AI TOURNAMENT SUGGESTIONS\n\n"
            "Usage: /aihost <type>\n\n"
            "Available types:\n"
            "• /aihost solo - AI solo tournament suggestion\n"
            "• /aihost duo - AI duo tournament suggestion\n"
            "• /aihost squad - AI squad tournament suggestion\n\n"
            "AI analysis ke saath smart suggestions! 🧠"
        )
        return

    mode = context.args[0].lower()
    suggestion = get_ai_tournament_suggestion(mode)

    await update.message.reply_text(suggestion)
