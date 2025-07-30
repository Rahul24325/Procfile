"""
Payment-related handlers for BGMI Tournament Bot
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import *
from utils.helpers import get_ist_time
import logging

logger = logging.getLogger(__name__)

class PaymentHandlers:
    def __init__(self, db):
        self.db = db
    
    async def show_payment_instructions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, tournament_id):
        """Show payment instructions for tournament"""
        tournament = await self.db.get_tournament(tournament_id)
        if not tournament:
            await update.callback_query.answer("❌ Tournament not found!")
            return
        
        payment_msg = f"""💰 **PAYMENT INSTRUCTIONS**

🏆 **Tournament:** {tournament['name']}
💸 **Entry Fee:** ₹{tournament['entry_fee']}

📱 **UPI Payment Details:**
🆔 **UPI ID:** `{UPI_ID}`
💵 **Amount:** ₹{tournament['entry_fee']}
📝 **Note:** {tournament['name']} - @{update.effective_user.username}

📋 **Payment Steps:**
1. 📱 Open any UPI app (PhonePe, GPay, Paytm)
2. 💰 Send ₹{tournament['entry_fee']} to: `{UPI_ID}`
3. 📸 Take screenshot of payment confirmation
4. 📤 Send screenshot to @Ghost_Commander
5. 🔢 Copy UTR/Transaction ID from screenshot
6. 📝 Use /paid command with UTR number
7. ⌛ Wait for admin confirmation

⚠️ **IMPORTANT:**
• Include tournament name in payment note
• Keep UTR number ready
• Payment must be completed 1 hour before tournament
• No refunds after room details are shared
• Contact @# database.py (inside your MongoDB class)

async def save_payment(self, payment_data):
    await self.payments.insert_one(payment_data)

async def get_payment(self, user_id, tournament_id=None):
    query = {"user_id": user_id}
    if tournament_id:
        query["tournament_id"] = tournament_id
    return await self.payments.find_one(query)

async def get_tournament(self, tournament_id):
    return await self.tournaments.find_one({"tournament_id": tournament_id}) if payment fails

🕘 **Payment Deadline:** {(tournament['datetime'] - get_ist_time()).seconds // 3600} hours remaining"""

        keyboard = [
            [InlineKeyboardButton("📱 Copy UPI ID", callback_data=f"copy_upi_{tournament_id}")],
            [InlineKeyboardButton("📸 Payment Done - Submit UTR", callback_data=f"submit_utr_{tournament_id}")],
            [InlineKeyboardButton("📞 Contact Admin", url="https://t.me/@Ghost_Commander")],
            [InlineKeyboardButton("🔙 Back to Tournament", callback_data=f"join_tournament_{tournament_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            payment_msg,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def submit_utr_prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE, tournament_id):
        """Prompt user to submit UTR number"""
        tournament = await self.db.get_tournament(tournament_id)
        if not tournament:
            await update.callback_query.answer("❌ Tournament not found!")
            return
        
        # Set user state for UTR submission
        context.user_data['state'] = 'waiting_utr'
        context.user_data['tournament_id'] = tournament_id
        
        utr_msg = f"""🔢 **SUBMIT UTR NUMBER**

🏆 **Tournament:** {tournament['name']}
💰 **Amount:** ₹{tournament['entry_fee']}

📝 **Instructions:**
1. Find UTR/Transaction ID in your payment app
2. Copy the 12-digit number (e.g., 123456789012)
3. Type /paid followed by UTR number
4. Example: `/paid 123456789012`

📱 **Where to find UTR:**
• **PhonePe:** Transaction Details > UTR
• **GPay:** Transaction > Transaction ID
• **Paytm:** Payment Details > Order ID
• **Bank Apps:** Transaction Receipt > UTR

⚠️ **Make sure to:**
• Send correct UTR number
• Don't include extra spaces
• Screenshot already sent to @Ghost_Commander

Type your command now: `/paid YOUR_UTR_NUMBER`"""

        await update.callback_query.edit_message_text(
            utr_msg,
            parse_mode='Markdown'
        )
    
    async def paid_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /paid command"""
        user = update.effective_user
        
        if not context.args:
            await update.message.reply_text(
                "❌ **Invalid Format!**\n\n"
                "Correct usage: `/paid YOUR_UTR_NUMBER`\n"
                "Example: `/paid 123456789012`\n\n"
                "📝 UTR number should be 12 digits from your payment app.",
                parse_mode='Markdown'
            )
            return
        
        utr_number = context.args[0]
        
        # Validate UTR format (12 digits)
        if not utr_number.isdigit() or len(utr_number) != 12:
            await update.message.reply_text(
                "❌ **Invalid UTR Format!**\n\n"
                "UTR number should be exactly 12 digits.\n"
                "Check your payment app and try again.\n\n"
                "Example: `/paid 123456789012`",
                parse_mode='Markdown'
            )
            return
        
        # Get tournament ID from user state
        tournament_id = context.user_data.get('tournament_id')
        tournament = None
        
        if tournament_id:
            tournament = await self.db.get_tournament(tournament_id)
        
        # Save payment information
        payment_data = {
            'user_id': user.id,
            'username': user.username,
            'utr_number': utr_number,
            'tournament_id': tournament_id,
            'tournament_name': tournament['name'] if tournament else 'Unknown',
            'amount': tournament['entry_fee'] if tournament else 0,
            'confirmed': False,
            'created_at': get_ist_time()
        }
        
        payment_id = await self.db.save_payment(payment_data)
        
        if payment_id:
            confirmation_msg = f"""✅ **Payment Submitted Successfully!**

🎮 **Tournament:** {tournament['name'] if tournament else 'General'}
👨‍💼 **Player:** @{user.username or user.first_name}
🔢 **UTR Number:** `{utr_number}`
💰 **Amount:** ₹{tournament['entry_fee'] if tournament else 'N/A'}
🕘 **Submitted:** {get_ist_time().strftime('%d/%m/%Y %H:%M')}

⏳ **Status:** Pending Admin Verification

📋 **Next Steps:**
1. ✅ Payment submitted to admin queue
2. 🔍 Admin will verify your payment
3. ✅ You'll get confirmation notification
4. 🎮 Room details will be sent before tournament

⚠️ **Important:**
• Keep your phone active for notifications
• Join https://t.me/NoMercyZoneBG for updates
• Contact # database.py (inside your MongoDB class)

async def save_payment(self, payment_data):
    await self.payments.insert_one(payment_data)

async def get_payment(self, user_id, tournament_id=None):
    query = {"user_id": user_id}
    if tournament_id:
        query["tournament_id"] = tournament_id
    return await self.payments.find_one(query)

async def get_tournament(self, tournament_id):
    return await self.tournaments.find_one({"tournament_id": tournament_id}) if delayed

🎯 **Get Ready!** Tournament prep starts now!"""

            keyboard = [
                [InlineKeyboardButton("📊 Check Payment Status", callback_data="payment_status")],
                [InlineKeyboardButton("📞 Contact Admin", url="https://t.me/Owner_ji_bgmi")],
                [InlineKeyboardButton("🔙 Main Menu", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                confirmation_msg,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            # Notify admin about new payment
            try:
                admin_msg = f"""💰 **NEW PAYMENT RECEIVED**

👨‍💼 **Player:** @{user.username or user.first_name}
🆔 **User ID:** {user.id}
🎮 **Tournament:** {tournament['name'] if tournament else 'General'}
💵 **Amount:** ₹{tournament['entry_fee'] if tournament else 'N/A'}
🔢 **UTR:** `{utr_number}`
🕘 **Time:** {get_ist_time().strftime('%d/%m/%Y %H:%M')}

Use: `/confirm @{user.username or user.first_name}` to approve"""

                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=admin_msg,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to notify admin: {e}")
            
            # Clear user state
            context.user_data.clear()
        else:
            await update.message.reply_text(
                "❌ **Payment Submission Failed!**\n\n"
                "Please try again or contact admin.",
                parse_mode='Markdown'
            )
    
    async def process_utr_number(self, update: Update, context: ContextTypes.DEFAULT_TYPE, utr_number):
        """Process UTR number from text message"""
        # This is called when user is in 'waiting_utr' state
        # Validate and process the UTR
        
        if not utr_number.isdigit() or len(utr_number) != 12:
            await update.message.reply_text(
                "❌ **Invalid UTR Format!**\n\n"
                "Please type: `/paid YOUR_12_DIGIT_UTR`\n"
                "Example: `/paid 123456789012`",
                parse_mode='Markdown'
            )
            return
        
        # Simulate /paid command
        context.args = [utr_number]
        await self.paid_command(update, context)
    
    async def show_payment_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's payment status"""
        user = update.effective_user
        
        # Get latest payment
        payment = await self.db.get_payment(user.id)
        
        if not payment:
            status_msg = """💳 **PAYMENT STATUS**

❌ **No payments found!**

🎮 **To make a payment:**
1. Join a tournament
2. Follow payment instructions
3. Submit UTR number
4. Wait for confirmation

📋 **Need Help?**
Contact @Ghost_Commander"""
        else:
            status = "✅ Confirmed" if payment.get('confirmed', False) else "⏳ Pending"
            status_emoji = "✅" if payment.get('confirmed', False) else "⏳"
            
            status_msg = f"""💳 **PAYMENT STATUS**

{status_emoji} **Status:** {status}
🎮 **Tournament:** {payment.get('tournament_name', 'General')}
💰 **Amount:** ₹{payment.get('amount', 0)}
🔢 **UTR:** `{payment.get('utr_number', 'N/A')}`
🕘 **Submitted:** {payment.get('created_at', get_ist_time()).strftime('%d/%m/%Y %H:%M')}

"""
            
            if payment.get('confirmed', False):
                status_msg += """✅ **Payment Confirmed!**
🎮 Room details will be sent before tournament.
📢 Stay tuned for announcements!"""
            else:
                status_msg += """⏳ **Verification Pending**
🔍 Admin is reviewing your payment.
📞 Contact admin @Ghost_Commander if urgent."""
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh Status", callback_data="payment_status")],
            [InlineKeyboardButton("📞 Contact Admin", url="https://t.me/Owner_ji_bgmi")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                status_msg,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                status_msg,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    async def show_payment_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's payment history"""
        user = update.effective_user
        
        # Get all payments for user
        payments = await self.db.payments.find({'user_id': user.id}).sort('created_at', -1).to_list(length=20)
        
        if not payments:
            history_msg = """📜 **PAYMENT HISTORY**

❌ **No payment history found!**

Start participating in tournaments to build your payment history."""
        else:
            history_msg = f"""📜 **PAYMENT HISTORY**

👨‍💼 **Player:** @{user.username or user.first_name}
📊 **Total Payments:** {len(payments)}

📈 **Recent Transactions:**

"""
            
            total_amount = 0
            for i, payment in enumerate(payments[:10], 1):  # Show last 10
                status = "✅" if payment.get('confirmed', False) else "⏳"
                amount = payment.get('amount', 0)
                total_amount += amount if payment.get('confirmed', False) else 0
                date = payment.get('created_at', get_ist_time()).strftime('%d/%m')
                tournament = payment.get('tournament_name', 'General')[:20]
                
                history_msg += f"{i}. {status} ₹{amount} - {tournament} ({date})\n"
            
            history_msg += f"\n💰 **Total Confirmed:** ₹{total_amount}"
            history_msg += f"\n🎮 **Tournaments Played:** {len([p for p in payments if p.get('confirmed')])}"
        
        keyboard = [
            [InlineKeyboardButton("💳 Current Status", callback_data="payment_status")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            history_msg,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
