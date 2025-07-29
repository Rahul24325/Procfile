"""
Admin command handlers for No Mercy Zone Bot
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import *
from messages import get_admin_dashboard_message, get_tournament_post
from utils import *
from config import ADMIN_ID, ENTRY_FEES, PRIZE_POOLS, TOURNAMENT_MAPS
import random
from datetime import datetime, timedelta

async def admin_dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /dashboard command for admin"""
    user_id = update.effective_user.id
    
    if not await is_admin(user_id):
        await update.message.reply_text("❌ Admin only command!")
        return
    
    dashboard_msg = get_admin_dashboard_message()
    await update.message.reply_text(dashboard_msg)

async def is_admin(user_id):
    """Check if user is admin"""
    return str(user_id) == str(ADMIN_ID)

async def host_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /host command for creating tournaments"""
    user_id = update.effective_user.id
    
    if not await is_admin(user_id):
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args:
        msg = """🎮 *TOURNAMENT HOSTING*

Usage: /host <type>

Available types:
• `/host solo` - Create solo tournament
• `/host duo` - Create duo tournament  
• `/host squad` - Create squad tournament

Interactive step-by-step creation! 👑"""
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        return
    
    tournament_type = context.args[0].lower()
    
    if tournament_type not in ['solo', 'duo', 'squad']:
        await update.message.reply_text("❌ Invalid tournament type! Use: solo, duo, or squad")
        return
    
    # Start interactive tournament creation
    context.user_data['creating_tournament'] = {
        'type': tournament_type,
        'step': 'name'
    }
    
    await update.message.reply_text(
        f"🎮 Creating {tournament_type.upper()} tournament...\n\n"
        f"Step 1/6: Enter tournament name:"
    )

async def create_tournament_interactive(update, context, tournament_type):
    """Create tournament interactively - fallback for direct creation"""
    # Generate tournament data
    next_time = get_next_tournament_time()
    
    tournament_names = {
        'solo': ['HEADSHOT KING CHALLENGE', 'SOLO SUPREMACY', 'LONE WOLF BATTLE'],
        'duo': ['DYNAMIC DUOS', 'PARTNER POWER', 'DUO DOMINATION'],
        'squad': ['ROYALE RUMBLE', 'SQUAD SHOWDOWN', 'TEAM TITANS']
    }
    
    tournament_data = {
        'name': random.choice(tournament_names[tournament_type]),
        'type': tournament_type,
        'date': next_time['date'],
        'time': next_time['time'],
        'map': random.choice(TOURNAMENT_MAPS),
        'entry_fee': ENTRY_FEES[tournament_type],
        'prize_type': 'rank_based',
        'prize_info': get_prize_info(tournament_type, 'rank_based')
    }
    
    # Create tournament in database
    created_tournament = create_tournament(tournament_data)
    
    # Generate tournament post
    tournament_post = get_tournament_post(created_tournament)
    
    # Schedule room notification 10 minutes before
    schedule_room_notification(created_tournament)
    
    msg = f"""✅ *TOURNAMENT CREATED SUCCESSFULLY!*

{tournament_post}

Tournament ID: `{created_tournament['tournament_id']}`

🎯 Tournament ready for participants!
⏰ Room details will be available 10 minutes before match starts.
Room details: Use /droproom command."""
    
    await update.message.reply_text(msg, parse_mode='Markdown')
    
    # Auto-post to channel
    from config import CHANNEL_ID
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    try:
        channel_msg = f"""{tournament_post}

⏰ Room ID & Password will be shared 10 minutes before match starts!"""
        
        # Add join button
        keyboard = [[InlineKeyboardButton("🎮 JOIN TOURNAMENT", callback_data=f"join_tournament_{created_tournament['tournament_id']}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=channel_msg,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        await update.message.reply_text("✅ Tournament posted to channel automatically!")
    except Exception as e:
        await update.message.reply_text(f"✅ Tournament created! ❌ Auto-post failed: {str(e)}")

async def handle_tournament_creation_steps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle step-by-step tournament creation"""
    if 'creating_tournament' not in context.user_data:
        return False
    
    creation_data = context.user_data['creating_tournament']
    step = creation_data['step']
    user_input = update.message.text
    
    if step == 'name':
        creation_data['name'] = user_input
        creation_data['step'] = 'date'
        await update.message.reply_text(
            f"✅ Tournament Name: {user_input}\n\n"
            f"Step 2/6: Enter tournament date (YYYY-MM-DD):"
        )
        return True
        
    elif step == 'date':
        try:
            from datetime import datetime
            datetime.strptime(user_input, '%Y-%m-%d')
            creation_data['date'] = user_input
            creation_data['step'] = 'time'
            await update.message.reply_text(
                f"✅ Date: {user_input}\n\n"
                f"Step 3/6: Enter tournament time (HH:MM format):"
            )
        except:
            await update.message.reply_text("❌ Invalid date format! Use YYYY-MM-DD (e.g., 2025-07-28)")
        return True
        
    elif step == 'time':
        try:
            from datetime import datetime
            datetime.strptime(user_input, '%H:%M')
            creation_data['time'] = user_input
            creation_data['step'] = 'entry_fee'
            await update.message.reply_text(
                f"✅ Time: {user_input}\n\n"
                f"Step 4/6: Enter entry fee (only number, e.g., 25):"
            )
        except:
            await update.message.reply_text("❌ Invalid time format! Use HH:MM (e.g., 20:30)")
        return True
        
    elif step == 'entry_fee':
        try:
            entry_fee = int(user_input)
            creation_data['entry_fee'] = entry_fee
            creation_data['step'] = 'map'
            await update.message.reply_text(
                f"✅ Entry Fee: ₹{entry_fee}\n\n"
                f"Step 5/6: Enter map name (e.g., Erangel, Sanhok, Miramar):"
            )
        except:
            await update.message.reply_text("❌ Invalid entry fee! Enter only numbers (e.g., 25)")
        return True
        
    elif step == 'map':
        creation_data['map'] = user_input
        creation_data['step'] = 'prize'
        prize_options = """Step 6/6: Select prize structure:
1. rank_based - Winner gets more, 2nd and 3rd get prizes
2. kill_based - Prize per kill + bonus
3. fixed - Winner takes all

Reply with: 1, 2, or 3"""
        await update.message.reply_text(
            f"✅ Map: {user_input}\n\n{prize_options}"
        )
        return True
        
    elif step == 'prize':
        prize_types = {'1': 'rank_based', '2': 'kill_based', '3': 'fixed'}
        if user_input in prize_types:
            creation_data['prize_type'] = prize_types[user_input]
            
            # Create tournament
            tournament_data = {
                'name': creation_data['name'],
                'type': creation_data['type'],
                'date': creation_data['date'],
                'time': creation_data['time'],
                'map': creation_data['map'],
                'entry_fee': creation_data['entry_fee'],
                'prize_type': creation_data['prize_type'],
                'prize_info': get_prize_info(creation_data['type'], creation_data['prize_type'])
            }
            
            # Create in database
            created_tournament = create_tournament(tournament_data)
            
            # Schedule room notification
            schedule_room_notification(created_tournament)
            
            # Generate final message
            tournament_post = get_tournament_post(created_tournament)
            
            msg = f"""✅ *TOURNAMENT CREATED SUCCESSFULLY!*

{tournament_post}

Tournament ID: `{created_tournament['tournament_id']}`

🎯 Tournament ready for participants!
⏰ Room details will be available 10 minutes before match starts."""
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
            # Auto-post to channel
            from config import CHANNEL_ID
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            try:
                channel_msg = f"""{tournament_post}

⏰ Room ID & Password will be shared 10 minutes before match starts!"""
                
                # Add join button
                keyboard = [[InlineKeyboardButton("🎮 JOIN TOURNAMENT", callback_data=f"join_tournament_{created_tournament['tournament_id']}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=channel_msg,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                await update.message.reply_text("✅ Tournament posted to channel automatically!")
            except Exception as e:
                await update.message.reply_text(f"✅ Tournament created! ❌ Auto-post failed: {str(e)}")
            
            # Clear creation data
            del context.user_data['creating_tournament']
        else:
            await update.message.reply_text("❌ Invalid option! Reply with 1, 2, or 3")
        return True
    
    return False

def schedule_room_notification(tournament_data):
    """Schedule room notification 10 minutes before tournament"""
    from datetime import datetime, timedelta
    
    try:
        # Parse tournament datetime
        tournament_datetime = datetime.strptime(
            f"{tournament_data['date']} {tournament_data['time']}", 
            "%Y-%m-%d %H:%M"
        )
        
        # Calculate notification time (10 minutes before)
        notification_time = tournament_datetime - timedelta(minutes=10)
        
        # Store notification in database for processing
        from database import schedule_notification
        schedule_notification({
            'tournament_id': tournament_data['tournament_id'],
            'notification_time': notification_time,
            'type': 'room_ready',
            'message': f"🚨 ROOM DETAILS READY!\n\nTournament: {tournament_data['name']}\nStarting in 10 minutes!\n\nRoom details will be shared soon! Get ready! 🔥"
        })
        
    except Exception as e:
        print(f"Failed to schedule notification: {e}")

def get_prize_info(tournament_type, prize_type):
    """Get prize information string"""
    prizes = PRIZE_POOLS[tournament_type][prize_type]
    
    if prize_type == 'kill_based':
        return f"₹{prizes['per_kill']} per kill + ₹{prizes['bonus']} bonus"
    elif prize_type == 'fixed':
        return f"Winner takes all: ₹{prizes['winner']}"
    elif prize_type == 'rank_based':
        return f"#1: ₹{prizes['1st']} | #2: ₹{prizes['2nd']} | #3: ₹{prizes['3rd']}"
    
    return "TBA"

async def ai_host_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /aihost command for AI tournament suggestions"""
    user_id = update.effective_user.id
    
    if not await is_admin(user_id):
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args:
        msg = """🤖 *AI TOURNAMENT SUGGESTIONS*

Usage: /aihost <type>

Available types:
• `/aihost solo` - AI solo tournament suggestion
• `/aihost duo` - AI duo tournament suggestion  
• `/aihost squad` - AI squad tournament suggestion

AI analysis ke saath smart suggestions! 🧠"""
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        return
    
    tournament_type = context.args[0].lower()
    
    if tournament_type not in ['solo', 'duo', 'squad']:
        await update.message.reply_text("❌ Invalid tournament type!")
        return
    
    # Get AI suggestion with advanced analysis
    suggestion = get_ai_tournament_suggestion(tournament_type)
    
    if not suggestion:
        await update.message.reply_text("❌ AI analysis failed! Creating tournament manually...")
        # Fallback to manual creation
        await create_tournament_interactive(update, context, tournament_type)
        return
    
    # Calculate advanced profit analysis
    from utils import calculate_advanced_profit_analysis
    estimated_participants = suggestion.get('optimal_participants', 15)
    entry_fee = suggestion['entry_fee']
    
    profit_analysis = calculate_advanced_profit_analysis(
        tournament_type, estimated_participants, entry_fee, suggestion
    )
    
    # Get market insights
    from utils import analyze_market_trends, get_optimal_tournament_timing
    market_trends = analyze_market_trends()
    optimal_timing = get_optimal_tournament_timing()
    
    msg = f"""🤖 *AI TOURNAMENT RECOMMENDATION*

🎯 *TOURNAMENT DETAILS:*
🏆 Name: {suggestion['name']}
🎮 Type: {tournament_type.upper()}
📍 Map: {suggestion['map']}
💰 Entry Fee: ₹{entry_fee}
🎁 Prize Type: {suggestion['prize_type']}
👥 Optimal Participants: {estimated_participants}

🧠 *AI CONFIDENCE: {suggestion['confidence']}%*
📈 Reasoning: {suggestion['reasoning']}

💼 *PROFIT ANALYSIS:*
• Total Collection: ₹{profit_analysis['total_collection']:,}
• Estimated Payout: ₹{profit_analysis['estimated_payout']:,}
• Operating Cost: ₹{profit_analysis['operating_cost']:,}
• Net Profit: ₹{profit_analysis['net_profit']:,}
• ROI: {profit_analysis['adjusted_roi']}%
• Risk Level: {profit_analysis['risk_level']}

📊 *MARKET INSIGHTS:*
• Player Activity: {market_trends['player_activity']}%
• Competition Level: {market_trends['competition_level']}
• Optimal Timing: {optimal_timing['slot_quality']}
• Expected Participation: {optimal_timing['expected_participation']}

🎯 *RECOMMENDATION: {profit_analysis['recommendation']}*

Accept AI suggestion? Reply with `/approve_ai {tournament_type}`"""
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def active_tournaments_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /active command"""
    user_id = update.effective_user.id
    
    if not await is_admin(user_id):
        await update.message.reply_text("❌ Admin only command!")
        return
    
    tournaments = get_active_tournaments()
    
    if not tournaments:
        await update.message.reply_text("🚫 No active tournaments currently!")
        return
    
    msg = "🎮 *ACTIVE TOURNAMENTS*\n\n"
    
    for tournament in tournaments:
        participants_count = len(tournament.get('participants', []))
        status_emoji = get_tournament_status_emoji(tournament['status'])
        
        msg += f"{status_emoji} *{tournament['name']}*\n"
        msg += f"📅 {tournament['date']} at {tournament['time']}\n"
        msg += f"👥 Participants: {participants_count}\n"
        msg += f"💰 Entry Fee: ₹{tournament['entry_fee']}\n"
        msg += f"🆔 ID: `{tournament['tournament_id']}`\n\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def drop_room_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /droproom command"""
    user_id = update.effective_user.id
    
    if not await is_admin(user_id):
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Usage: /droproom <tournament_id> <room_id> <password>\n"
            "Example: /droproom ABC123 123456789 vip50"
        )
        return
    
    if len(context.args) < 3:
        await update.message.reply_text("❌ Missing room details! Provide tournament_id, room_id, and password.")
        return
    
    tournament_id = context.args[0]
    room_id = context.args[1]
    password = context.args[2]
    
    # Update tournament with room details
    update_result = update_tournament(tournament_id, {
        'room_id': room_id,
        'room_password': password,
        'status': 'live'
    })
    
    if update_result.modified_count == 0:
        await update.message.reply_text("❌ Tournament not found!")
        return
    
    # Get tournament participants
    participants = get_tournament_participants(tournament_id)
    
    room_msg = f"""🎮 *ROOM DETAILS DROPPED!*

🏆 Tournament: {tournament_id}
🆔 Room ID: `{room_id}`
🔐 Password: `{password}`

⚡ JOIN FAST! Match starting soon!
🚫 Late entry not allowed!

Good luck warriors! 🔥"""
    
    # Send to admin first
    await update.message.reply_text(room_msg, parse_mode='Markdown')
    
    # Send to all participants
    success_count = 0
    for participant in participants:
        try:
            await context.bot.send_message(
                chat_id=participant['user_id'],
                text=room_msg,
                parse_mode='Markdown'
            )
            success_count += 1
        except:
            continue
    
    await update.message.reply_text(f"✅ Room details sent to {success_count}/{len(participants)} participants")

async def list_players_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /listplayers command"""
    user_id = update.effective_user.id
    
    if not await is_admin(user_id):
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /listplayers <tournament_id>")
        return
    
    tournament_id = context.args[0]
    participants = get_tournament_participants(tournament_id)
    
    if not participants:
        await update.message.reply_text("❌ No participants found for this tournament!")
        return
    
    msg = f"👥 *PARTICIPANTS LIST*\n\nTournament: {tournament_id}\n\n"
    
    for i, participant in enumerate(participants, 1):
        username = participant.get('username', 'No username')
        first_name = participant.get('first_name', 'Unknown')
        paid_status = "✅" if participant.get('confirmed', False) else "❌"
        
        msg += f"{i}. {first_name} (@{username}) {paid_status}\n"
    
    msg += f"\nTotal: {len(participants)} participants"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /clear command"""
    user_id = update.effective_user.id
    
    if not await is_admin(user_id):
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Usage:\n"
            "/clear tournament <tournament_id> - Delete tournament\n"
            "/clear player <tournament_id> <user_id> - Remove player"
        )
        return
    
    action = context.args[0]
    
    if action == "tournament":
        if len(context.args) < 2:
            await update.message.reply_text("❌ Tournament ID required!")
            return
        
        tournament_id = context.args[1]
        result = delete_tournament(tournament_id)
        
        if result.deleted_count > 0:
            await update.message.reply_text(f"✅ Tournament {tournament_id} deleted!")
        else:
            await update.message.reply_text("❌ Tournament not found!")
    
    elif action == "player":
        if len(context.args) < 3:
            await update.message.reply_text("❌ Tournament ID and User ID required!")
            return
        
        tournament_id = context.args[1]
        user_id_to_remove = int(context.args[2])
        
        # Remove player from tournament
        from database import db
        result = db.tournaments.update_one(
            {"tournament_id": tournament_id},
            {"$pull": {"participants": user_id_to_remove}}
        )
        
        if result.modified_count > 0:
            await update.message.reply_text(f"✅ Player {user_id_to_remove} removed from tournament!")
        else:
            await update.message.reply_text("❌ Player not found in tournament!")

async def data_vault_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /datavault command"""
    user_id = update.effective_user.id
    
    if not await is_admin(user_id):
        await update.message.reply_text("❌ Admin only command!")
        return
    
    # Get financial data
    today_data = get_financial_data("today")
    weekly_data = get_financial_data("weekly")
    monthly_data = get_financial_data("monthly")
    
    msg = f"""💰 *FINANCIAL VAULT*

📅 *TODAY'S COLLECTION:*
• Revenue: ₹{today_data['total_revenue']}
• Transactions: {today_data['total_transactions']}

📊 *WEEKLY EARNINGS:*
• Revenue: ₹{weekly_data['total_revenue']}
• Transactions: {weekly_data['total_transactions']}

📈 *MONTHLY REVENUE:*
• Revenue: ₹{monthly_data['total_revenue']}
• Transactions: {monthly_data['total_transactions']}

💎 Ghost Commander ka empire grow kar raha hai! 🔥"""
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def special_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /special command for winner declarations"""
    user_id = update.effective_user.id
    
    if not await is_admin(user_id):
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Usage: /special <type> <message>\n\n"
            "Types:\n"
            "• winner - Winner declaration\n"
            "• announcement - General announcement\n"
            "• promo - Promotional message"
        )
        return
    
    special_type = context.args[0]
    message = ' '.join(context.args[1:])
    
    if special_type == "winner":
        winner_msg = f"""🏆 *WINNER DECLARATION* 🏆

{message}

🎉 Congratulations to the champions!
💰 Prize distribution will be done shortly.

🚫 No Mercy Zone mein sirf legends jeetate hain! 🔥

Next tournament ke liye ready raho! 💪"""
        
    elif special_type == "announcement":
        winner_msg = f"""📢 *SPECIAL ANNOUNCEMENT*

{message}

🚫 No Mercy Zone Management"""
        
    elif special_type == "promo":
        winner_msg = f"""🔥 *PROMOTIONAL ALERT* 🔥

{message}

💥 Limited time offer! Jaldi karo!
🎮 Join karo aur dominate karo!"""
    
    else:
        await update.message.reply_text("❌ Invalid special type!")
        return
    
    # Send to admin first
    await update.message.reply_text(winner_msg, parse_mode='Markdown')
    
    # Auto-share to channel
    from config import CHANNEL_ID
    try:
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=winner_msg,
            parse_mode='Markdown'
        )
        await update.message.reply_text("✅ Message posted to channel automatically!")
    except Exception as e:
        await update.message.reply_text(f"✅ Message ready! ❌ Auto-post to channel failed: {str(e)}")
        await update.message.reply_text("📱 Please forward manually to channel/groups.")

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ban command"""
    user_id = update.effective_user.id
    
    if not await is_admin(user_id):
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /ban <user_id> or /ban @username")
        return
    
    target = context.args[0]
    
    # Extract user ID
    if target.startswith('@'):
        # Find user by username
        username = target[1:]
        from database import db
        user_doc = db.users.find_one({"username": username})
        if not user_doc:
            await update.message.reply_text("❌ User not found!")
            return
        target_user_id = user_doc['user_id']
    else:
        try:
            target_user_id = int(target)
        except:
            await update.message.reply_text("❌ Invalid user ID!")
            return
    
    # Ban user
    result = ban_user(target_user_id)
    
    if result.modified_count > 0:
        await update.message.reply_text(f"✅ User {target} banned successfully! 🔨")
    else:
        await update.message.reply_text("❌ User not found or already banned!")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unban command"""
    user_id = update.effective_user.id
    
    if not await is_admin(user_id):
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /unban <user_id> or /unban @username")
        return
    
    target = context.args[0]
    
    # Extract user ID
    if target.startswith('@'):
        username = target[1:]
        from database import db
        user_doc = db.users.find_one({"username": username})
        if not user_doc:
            await update.message.reply_text("❌ User not found!")
            return
        target_user_id = user_doc['user_id']
    else:
        try:
            target_user_id = int(target)
        except:
            await update.message.reply_text("❌ Invalid user ID!")
            return
    
    # Unban user
    result = unban_user(target_user_id)
    
    if result.modified_count > 0:
        await update.message.reply_text(f"✅ User {target} unbanned successfully! ✨")
    else:
        await update.message.reply_text("❌ User not found or not banned!")

async def confirm_payment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /confirm command"""
    user_id = update.effective_user.id
    
    if not await is_admin(user_id):
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /confirm @username")
        return
    
    target = context.args[0]
    
    if not target.startswith('@'):
        await update.message.reply_text("❌ Use @username format!")
        return
    
    username = target[1:]
    from database import db
    user_doc = db.users.find_one({"username": username})
    
    if not user_doc:
        await update.message.reply_text("❌ User not found!")
        return
    
    # Update user as confirmed
    update_user(user_doc['user_id'], {"paid": True, "confirmed": True})
    
    # Notify user
    try:
        await context.bot.send_message(
            chat_id=user_doc['user_id'],
            text="✅ Payment confirmed! You can now join tournaments. 🔥"
        )
    except:
        pass
    
    await update.message.reply_text(f"✅ Payment confirmed for @{username}!")

async def decline_payment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /decline command"""
    user_id = update.effective_user.id
    
    if not await is_admin(user_id):
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /decline @username")
        return
    
    target = context.args[0]
    
    if not target.startswith('@'):
        await update.message.reply_text("❌ Use @username format!")
        return
    
    username = target[1:]
    from database import db
    user_doc = db.users.find_one({"username": username})
    
    if not user_doc:
        await update.message.reply_text("❌ User not found!")
        return
    
    # Notify user
    try:
        await context.bot.send_message(
            chat_id=user_doc['user_id'],
            text="❌ Payment not received or invalid. Please check and send again."
        )
    except:
        pass
    
    await update.message.reply_text(f"❌ Payment declined for @{username}!")

async def approve_ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /approve_ai command"""
    user_id = update.effective_user.id
    
    if not await is_admin(user_id):
        await update.message.reply_text("❌ Admin only command!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /approve_ai <tournament_type>")
        return
    
    tournament_type = context.args[0].lower()
    
    if tournament_type not in ['solo', 'duo', 'squad']:
        await update.message.reply_text("❌ Invalid tournament type!")
        return
    
    # Get AI suggestion and create tournament
    suggestion = get_ai_tournament_suggestion(tournament_type)
    
    if not suggestion:
        await update.message.reply_text("❌ Failed to get AI suggestion!")
        return
    
    # Get optimal timing
    from utils import get_optimal_tournament_timing
    optimal_timing = get_optimal_tournament_timing()
    
    # Create tournament with AI suggestions
    tournament_data = {
        'name': suggestion['name'],
        'type': tournament_type,
        'date': optimal_timing['suggested_date'],
        'time': optimal_timing['suggested_time'],
        'map': suggestion['map'],
        'entry_fee': suggestion['entry_fee'],
        'prize_type': suggestion['prize_type'],
        'prize_info': f"{suggestion['prize_type']} prizes",
        'ai_generated': True,
        'ai_confidence': suggestion['confidence']
    }
    
    # Create tournament in database
    created_tournament = create_tournament(tournament_data)
    
    # Generate tournament post
    tournament_post = get_tournament_post(created_tournament)
    
    msg = f"""✅ AI TOURNAMENT APPROVED & CREATED!

{tournament_post}

🤖 AI Confidence: {suggestion['confidence']}%
🆔 Tournament ID: {created_tournament['tournament_id']}
⏰ Timing Quality: {optimal_timing['slot_quality']}

🎯 AI-optimized tournament is now live!
Ready for participants to join! 🔥"""
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def ai_analytics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /aianalytics command for comprehensive AI insights"""
    user_id = update.effective_user.id
    
    if not await is_admin(user_id):
        await update.message.reply_text("❌ Admin only command!")
        return
    
    from utils import analyze_historical_performance, analyze_market_trends, get_optimal_tournament_timing
    from datetime import datetime
    
    # Get comprehensive analytics
    solo_data = analyze_historical_performance("solo")
    duo_data = analyze_historical_performance("duo")  
    squad_data = analyze_historical_performance("squad")
    market_trends = analyze_market_trends()
    optimal_timing = get_optimal_tournament_timing()
    
    current_time = get_ist_time().strftime("%H:%M IST")
    
    msg = f"""🤖 AI ANALYTICS DASHBOARD

🕒 Current Time: {current_time}
📊 Market Activity: {market_trends['player_activity']}%
🏆 Competition Level: {market_trends['competition_level']}

⏰ OPTIMAL TIMING ANALYSIS:
• Next Best Slot: {optimal_timing['suggested_time']} ({optimal_timing['slot_quality']})
• Expected Participation: {optimal_timing['expected_participation']}
• Hours From Now: {optimal_timing['hours_from_now']}

📈 HISTORICAL PERFORMANCE:

🧍 SOLO TOURNAMENTS:
• Avg Participants: {solo_data['avg_participants']}
• Success Rate: {solo_data['success_rate']}%
• Popular Maps: {', '.join(solo_data['popular_maps'][:2])}
• Total Hosted: {solo_data.get('total_tournaments', 'N/A')}

👥 DUO TOURNAMENTS:
• Avg Participants: {duo_data['avg_participants']}
• Success Rate: {duo_data['success_rate']}%
• Popular Maps: {', '.join(duo_data['popular_maps'][:2])}
• Total Hosted: {duo_data.get('total_tournaments', 'N/A')}

👨‍👩‍👧‍👦 SQUAD TOURNAMENTS:
• Avg Participants: {squad_data['avg_participants']}
• Success Rate: {squad_data['success_rate']}%
• Popular Maps: {', '.join(squad_data['popular_maps'][:2])}
• Total Hosted: {squad_data.get('total_tournaments', 'N/A')}

🎯 AI RECOMMENDATIONS:
• New Registrations: {market_trends['new_registrations']} (7 days)
• Trending Maps: {', '.join(market_trends['trending_maps'][:3])}
• Optimal Entry Fees: Solo ₹{market_trends['optimal_entry_fees']['solo']}, Duo ₹{market_trends['optimal_entry_fees']['duo']}, Squad ₹{market_trends['optimal_entry_fees']['squad']}

🧠 AI suggests focusing on {optimal_timing['slot_quality'].lower()} slots for maximum engagement!"""
    
    await update.message.reply_text(msg, parse_mode='Markdown')
    await update.message.reply_text(f"❌ Payment declined for @{username}!")
