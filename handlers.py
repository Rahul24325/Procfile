"""
User command handlers for No Mercy Zone Bot
Fixed tournament-specific payment system
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
        admin_welcome = f"""ðŸ‘‘ Welcome back, Ghost Commander! ðŸ§¨

ðŸ”¥ The Boss has entered the lobby! 
ðŸ’» System ready for your commands...
âš¡ All servers armed and operational!

Your domain awaits your orders! ðŸ’€"""
        
        await update.message.reply_text(admin_welcome)
        
        # Show admin dashboard
        dashboard_msg = get_admin_dashboard_message()
        await update.message.reply_text(dashboard_msg)
        return
    
    # Check if user is banned
    user_data = get_user(user.id)
    if user_data and user_data.get("banned", False):
        await update.message.reply_text("ðŸš« You are banned from using this bot!")
        return
    
    # Create or get user
    if not user_data:
        user_data = create_user(user.id, user.username, user.first_name)
    
    # Send welcome message
    welcome_msg = get_welcome_message(user.first_name)
    await update.message.reply_text(welcome_msg)
    
    # Check channel membership
    is_member = check_channel_membership(context.bot, user.id)
    
    if not is_member:
        # Show channel join button
        keyboard = [
            [InlineKeyboardButton("âœ… Join Channel", url=CHANNEL_URL)],
            [InlineKeyboardButton("âœ… I've Joined", callback_data="check_membership")]
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
        [InlineKeyboardButton("ðŸŽ® Active Tournament", callback_data="active_tournament")],
        [InlineKeyboardButton("ðŸ“œ Terms & Condition", callback_data="terms_condition")],
        [InlineKeyboardButton("ðŸ‘¥ Invite Friends", callback_data="invite_friends")],
        [InlineKeyboardButton("ðŸ“± Share WhatsApp Status", callback_data="whatsapp_status")],
        [InlineKeyboardButton("ðŸ“œ Match History", callback_data="match_history")],
        [InlineKeyboardButton("ðŸ†˜ Help", callback_data="help")]
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
        is_member = check_channel_membership(context.bot, user_id)
        if is_member:
            update_user(user_id, {"is_member": True})
            await show_main_menu(update, context, user_data)
        else:
            await query.edit_message_text(
                "âŒ Channel abhi bhi join nahi kiya! Pehle join karo:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("âœ… Join Channel", url=CHANNEL_URL)],
                    [InlineKeyboardButton("âœ… I've Joined", callback_data="check_membership")]
                ])
            )
    
    elif query.data == "active_tournament":
        await show_active_tournaments(update, context)
    
    elif query.data == "terms_condition":
        rules_msg = get_rules_message()
        keyboard = [[InlineKeyboardButton("ðŸ”™ Back to Menu", callback_data="back_to_menu")]]
        await query.edit_message_text(
            rules_msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == "invite_friends":
        referral_msg = f"""ðŸ‘¥ INVITE FRIENDS & EARN FREE ENTRIES

ðŸŽ¯ Your Personal Referral Code: {user_data['referral_code']}

ðŸ“¤ How to Share:
1. Copy your referral code
2. Share with friends
3. When they join using your code, you get free entry!

ðŸ”— Share Link:
https://t.me/YourBotUsername?start={user_data['referral_code']}

ðŸ’° Benefits:
â€¢ 1 referral = 1 free tournament entry
â€¢ Unlimited referrals allowed
â€¢ Instant credit on successful referral

ðŸš« No Mercy Zone mein dost bhi competition hai! ðŸ”¥"""
        
        keyboard = [[InlineKeyboardButton("ðŸ”™ Back to Menu", callback_data="back_to_menu")]]
        await query.edit_message_text(
            referral_msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == "whatsapp_status":
        status_template = get_whatsapp_status_template(user_data['referral_code'])
        keyboard = [[InlineKeyboardButton("ðŸ”™ Back to Menu", callback_data="back_to_menu")]]
        await query.edit_message_text(
            f"ðŸ“± WHATSAPP STATUS TEMPLATE\n\nCopy and paste this as your WhatsApp status:\n\n{status_template}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == "match_history":
        await show_match_history(update, context)
    
    elif query.data == "help":
        help_msg = get_help_message()
        keyboard = [[InlineKeyboardButton("ðŸ”™ Back to Menu", callback_data="back_to_menu")]]
        await query.edit_message_text(
            help_msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == "back_to_menu":
        await show_main_menu(update, context, user_data)
    
    elif query.data.startswith("join_tournament_"):
        tournament_id = query.data.replace("join_tournament_", "")
        await handle_tournament_join(update, context, tournament_id)
    
    elif query.data.startswith("pay_for_tournament_"):
        tournament_id = query.data.replace("pay_for_tournament_", "")
        await show_payment_instructions(update, context, tournament_id)

async def show_active_tournaments(update, context):
    """Show active tournaments"""
    tournaments = get_active_tournaments()
    
    if not tournaments:
        msg = "ðŸš« Koi active tournament nahi hai abhi!\n\nJaldi hi naya tournament aayega. Channel pe active raho! ðŸ”¥"
        keyboard = [[InlineKeyboardButton("ðŸ”™ Back to Menu", callback_data="back_to_menu")]]
        await update.callback_query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    msg = "ðŸŽ® ACTIVE TOURNAMENTS\n\n"
    keyboard = []
    
    for tournament in tournaments:
        tournament_post = get_tournament_post(tournament)
        msg += tournament_post + "\n\n"
        
        keyboard.append([
            InlineKeyboardButton(
                f"âœ… Join {tournament['name']}", 
                callback_data=f"join_tournament_{tournament['tournament_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("ðŸ”™ Back to Menu", callback_data="back_to_menu")])
    
    await update.callback_query.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_tournament_join(update, context, tournament_id):
    """Handle tournament join request - Fixed to check tournament-specific payment"""
    user_id = update.effective_user.id
    user_data = get_user(user_id)
    tournament = get_tournament(tournament_id)
    
    if not tournament:
        msg = "âŒ Tournament nahi mila! Koi technical issue hai."
        keyboard = [[InlineKeyboardButton("ðŸ”™ Back", callback_data="active_tournament")]]
        await update.callback_query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Check if user has already joined this tournament
    if is_user_joined_tournament(user_id, tournament_id):
        msg = f"âœ… Aap already joined ho {tournament['name']} mein!\n\nRoom details milenge match time pe. Ready raho! ðŸ”¥"
        keyboard = [[InlineKeyboardButton("ðŸ”™ Back", callback_data="active_tournament")]]
        await update.callback_query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Check if user has paid for this specific tournament
    if not has_paid_for_tournament(user_id, tournament_id):
        # Check for free entries from referrals
        free_entries = user_data.get("free_entries", 0)
        
        if free_entries > 0:
            # Use free entry
            success = join_tournament_with_free_entry(user_id, tournament_id)
            if success:
                msg = f"âœ… Free entry use karke join ho gaye!\n\nðŸŽ® Tournament: {tournament['name']}\nðŸ’° Free entries remaining: {free_entries - 1}\n\nRoom details milenge match time pe! ðŸ”¥"
            else:
                msg = "âŒ Technical issue! Admin se contact karo."
        else:
            # Show payment required message
            msg = f"""ðŸ’° PAYMENT REQUIRED

ðŸŽ® Tournament: {tournament['name']}
ðŸ’µ Entry Fee: {format_currency(tournament.get('entry_fee', 50))}

Tournament join karne ke liye payment karo:

1. UPI ID: {UPI_ID}
2. Amount pay karo: {format_currency(tournament.get('entry_fee', 50))}
3. Screenshot bhejo {ADMIN_USERNAME} ko
4. /paid {tournament_id} <UTR> command use karo
5. Admin approval ke baad join kar sakte ho

âš ï¸ Har tournament ke liye alag payment karna hoga!
ðŸš« No payment, no entry! ðŸ”¥"""
            
            keyboard = [
                [InlineKeyboardButton("ðŸ’³ Payment Instructions", callback_data=f"pay_for_tournament_{tournament_id}")],
                [InlineKeyboardButton("ðŸ”™ Back", callback_data="active_tournament")]
            ]
            await update.callback_query.edit_message_text(
                msg,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
    else:
        # User has paid, join tournament
        success = join_tournament(user_id, tournament_id)
        if success:
            msg = f"âœ… Successfully joined {tournament['name']}!\n\nRoom details milenge match time pe. Ready raho! ðŸ”¥"
        else:
            msg = "âŒ Tournament join nahi ho saka. Admin se contact karo."
    
    keyboard = [[InlineKeyboardButton("ðŸ”™ Back", callback_data="active_tournament")]]
    await update.callback_query.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_payment_instructions(update, context, tournament_id):
    """Show detailed payment instructions for specific tournament"""
    tournament = get_tournament(tournament_id)
    
    if not tournament:
        await update.callback_query.edit_message_text("âŒ Tournament not found!")
        return
    
    msg = f"""ðŸ’³ PAYMENT INSTRUCTIONS

ðŸŽ® Tournament: {tournament['name']}
ðŸ’µ Entry Fee: {format_currency(tournament.get('entry_fee', 50))}

ðŸ“‹ Payment Steps:
1ï¸âƒ£ UPI ID: `{UPI_ID}`
2ï¸âƒ£ Amount: `{tournament.get('entry_fee', 50)}`
3ï¸âƒ£ Payment karne ke baad UTR note karo
4ï¸âƒ£ Screenshot bhejo {ADMIN_USERNAME} ko
5ï¸âƒ£ Command use karo: `/paid {tournament_id} <YOUR_UTR>`

Example: `/paid {tournament_id} 123456789012`

âš ï¸ Important:
â€¢ Exact amount pay karo
â€¢ UTR galat nahi hona chahiye
â€¢ Screenshot jaruri hai verification ke liye
â€¢ Har tournament ke liye alag payment

ðŸ”¥ Payment confirm hone ke baad instant join ho jaoge!"""
    
    keyboard = [[InlineKeyboardButton("ðŸ”™ Back", callback_data=f"join_tournament_{tournament_id}")]]
    await update.callback_query.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_match_history(update, context):
    """Show user's match history"""
    user_id = update.effective_user.id
    user_data = get_user(user_id)
    
    tournaments_joined = user_data.get("tournaments_joined", [])
    tournament_payments = user_data.get("tournament_payments", {})
    
    if not tournaments_joined:
        msg = "ðŸ“œ Abhi tak koi tournament join nahi kiya!\n\nPehla tournament join karo aur history banao! ðŸŽ®"
    else:
        msg = f"ðŸ“œ *YOUR TOURNAMENT HISTORY*\n\n"
        msg += f"ðŸŽ® Total Tournaments: {len(tournaments_joined)}\n"
        msg += f"ðŸ’° Total Spent: {format_currency(user_data.get('total_spent', 0))}\n"
        msg += f"ðŸ† Total Earned: {format_currency(user_data.get('total_earned', 0))}\n"
        msg += f"ðŸ†“ Free Entries: {user_data.get('free_entries', 0)}\n\n"
        
        msg += "ðŸ’³ *PAYMENT STATUS BY TOURNAMENT:*\n"
        for tournament_id in tournaments_joined:
            tournament = get_tournament(tournament_id)
            if tournament:
                payment_status = "âœ… Paid" if tournament_id in tournament_payments else "ðŸ†“ Free Entry"
                msg += f"â€¢ {tournament['name']}: {payment_status}\n"
    
    keyboard = [[InlineKeyboardButton("ðŸ”™ Back to Menu", callback_data="back_to_menu")]]
    await update.callback_query.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def paid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /paid command - Modified to accept tournament ID"""
    user_id = update.effective_user.id
    
    # Don't process if admin is sending the command
    if str(user_id) == str(ADMIN_ID):
        await update.message.reply_text("ðŸ‘‘ Admin detected! Payment verification skipped.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "âŒ Command format galat hai!\n\nUse: /paid <TOURNAMENT_ID> <UTR_NUMBER>\nExample: /paid TOUR001 123456789012\n\nTournament ID tournament details mein milega."
        )
        return
    
    tournament_id = context.args[0]
    utr = context.args[1]
    
    # Validate tournament exists
    tournament = get_tournament(tournament_id)
    if not tournament:
        await update.message.reply_text(
            f"âŒ Invalid tournament ID: {tournament_id}\n\nActive tournaments check karo aur sahi ID use karo."
        )
        return
    
    if not validate_utr(utr):
        await update.message.reply_text(
            "âŒ Invalid UTR number!\nUTR should be at least 10 digits."
        )
        return
    
    # Check if already paid for this tournament
    if has_paid_for_tournament(user_id, tournament_id):
        await update.message.reply_text(
            f"âœ… Aap already paid ho {tournament['name']} ke liye!\n\nDirect join kar sakte ho."
        )
        return
    
    # Create tournament-specific payment request
    user_data = get_user(user_id)
    
    # Store pending payment request
    create_payment_request(user_id, tournament_id, utr, tournament.get('entry_fee', 50))
    
    msg = f"""âœ… Payment request submitted!

ðŸŽ® Tournament: {tournament['name']}
ðŸ’µ Amount: {format_currency(tournament.get('entry_fee', 50))}
ðŸ§¾ UTR: `{utr}`
ðŸ“Š Status: Pending admin approval

{ADMIN_USERNAME} will verify and confirm shortly. 
Notification milega confirmation ke baad! ðŸ”¥

âš ï¸ Tournament join karne ke liye approval wait karo."""
    
    await update.message.reply_text(msg, parse_mode='Markdown')
    
    # Forward to admin
    admin_msg = f"""ðŸ’° *TOURNAMENT PAYMENT VERIFICATION REQUEST*

ðŸ‘¤ User: {user_data.get('first_name', 'Unknown')} (@{user_data.get('username', 'no_username')})
ðŸ†” User ID: `{user_id}`
ðŸŽ® Tournament: {tournament['name']} (`{tournament_id}`)
ðŸ’µ Amount: {format_currency(tournament.get('entry_fee', 50))}
ðŸ§¾ UTR: `{utr}`

Use: /confirm {user_id} {tournament_id} or /decline {user_id} {tournament_id}"""
    
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

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:  # Added null check
        return
        
    await query.answer()
    
    user_id = update.effective_user.id
    user_data = get_user(user_id)
    
    if not user_data:  # Added user data validation
        await query.edit_message_text("âŒ User data not found! Please use /start command.")
        return

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages"""
    user_id = update.effective_user.id
    
    # Check if admin is in tournament creation process
    if str(user_id) == str(ADMIN_ID):
        if await handle_tournament_creation_steps(update, context):
            return
    
    # Check if user is trying to interact without joining channel
    is_member = check_channel_membership(context.bot, user_id)
    
    if not is_member:
        msg = "âŒ Pehle channel join karo!\n\n/start command use karo."
        await update.message.reply_text(msg)
        return
    
    # Default response
    await update.message.reply_text(
        "ðŸ¤– Command samajh nahi aaya!\n\nMenu use karo ya /help dekho."
    )
