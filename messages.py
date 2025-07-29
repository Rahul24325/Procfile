"""
Message templates for No Mercy Zone Bot
"""

from config import CHANNEL_URL, DISCUSSION_GROUP_URL, SUPPORT_EMAIL, INSTAGRAM_HANDLE, ADMIN_USERNAME

def get_welcome_message(first_name):
    """Get welcome message for new users"""
    return f"""🧨 Welcome {first_name}, the Ghost Commander has arrived!

🚫 This is a No Mercy Zone 🔥  
Yahan dosti nahi, bas domination hoti hai 😈  
Squad mein entry ka matlab lobby tera slave ban chuka hai

💸 Paisa nahi? Referral bhej aur free entry kama!  
📢 Channel mandatory hai warna winner list se naam gayab!

📧 Support: {SUPPORT_EMAIL}  
📸 Insta: {INSTAGRAM_HANDLE} 
🎫 {ADMIN_USERNAME}  
🔗 Channel: {CHANNEL_URL}
Discussion group links {DISCUSSION_GROUP_URL}

⚔️ Ghost Commander Squad mein ho ab  
Ab sirf kills bolenge, baaki sab chup!

🎯 Pehle channel join karo, phir tournament mein entry milegi!"""

def get_channel_join_message():
    """Get channel join message"""
    return """❌ Abhi bhi channel join nahi kiya? 
Jaldi se join karo warna entry milegi hi nahi!"""

def get_main_menu_message(first_name, referral_code):
    """Get main menu message"""
    return f"""🔥 Lobby Access Granted! 🔥  
👑 Welcome, {first_name}.  
🧨 Ab sirf kill karega ya lobby ka malik banega?  
🚫 No Mercy Zone mein sirf legends tikte hain! {first_name}?

Tera Personal Referral Code: `{referral_code}`
Dost ko bhej, aur FREE ENTRY pa!"""

def get_admin_dashboard_message():
    """Get admin dashboard message"""
    from datetime import datetime
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return f"""👑 *Welcome Back, 🧨 Ghost Commander!*  
"Server breathe kar raha hai... kyunki Boss wapas aaya hai!" 😎💻

🧨 *System Armed & Ready*  
🕒 *Time:* `{current_time}`  
🎮 *Live Matches:* Loading...  
🚀 *Next Drop-In:* Soon

🧬 Admin Arsenal: 
(1). /host - Create tournaments (Solo/Duo/Squad)
(2). /aihost - AI tournament suggestions with profit analysis
(3). /approve_ai - Approve and create AI-suggested tournaments
(4). /aianalytics - Comprehensive AI insights dashboard
(5). /active - View active tournaments
(6). /droproom - Send room details    
(7). /listplayers - View participant list    
(8). /clear - Edit/remove tournament
(9). /datavault - Financial reports
(10). /special - Custom notifications & Winner Declaration
(11). /ban - Ban users
(12). /unban - Unban users
(13). /dashboard - Show admin dashboard
(14). /confirm - Approve payments
(15). /decline - Decline payments

⚠️ *Note:*  
Yeh teri lobby hai bhai...  
Yahan rules likhta bhi tu hai, todta bhi tu! 🔥🧠"""

def get_tournament_post(tournament_data):
    """Generate tournament post"""
    tournament_type = tournament_data["type"].upper()
    tournament_name = tournament_data["name"]
    date = tournament_data["date"]
    time = tournament_data["time"]
    map_name = tournament_data["map"]
    entry_fee = tournament_data["entry_fee"]
    prize_info = tournament_data.get("prize_info", "TBA")
    
    type_emoji = {
        "SOLO": "🧍",
        "DUO": "👥", 
        "SQUAD": "👨‍👩‍👧‍👦"
    }
    
    return f"""🎮 TOURNAMENT TYPE: {type_emoji.get(tournament_type, "🎮")} {tournament_type}  
🏆 {tournament_name}  
📅 Date: {date}  
🕘 Time: {time}  
📍 Map: {map_name}  
💰 Entry Fee: ₹{entry_fee}  
🎁 Prize Pool: {prize_info}

🔽 JOIN & DETAILS 🔽"""

def get_whatsapp_status_template(referral_code):
    """Get WhatsApp status template"""
    return f"""🎮 BGMI TOURNAMENTS LIVE!
🔥 Daily Cash 💰 | 💀 Kill Rewards | 👑 VIP Matches
💥 FREE ENTRY with my code 👉 {referral_code}
📲 Click & Join:
https://t.me/Turnament_ManagerBot={referral_code}
⚡ Limited Slots! Fast join karo!

#BGMI #EarnWithKills"""

def get_rules_message():
    """Get rules and terms message"""
    return f"""📜 TOURNAMENT RULES & TERMS

🎯 GAME RULES:
1. ❌ No emulators allowed
2. ❌ No teaming/hacking/cheating
3. 📊 Points = Kills + Rank position
4. ⏰ Be punctual - late entry not allowed
5. 📱 Original BGMI app only

⚠️ DISCLAIMER & TERMS:
1. 🚫 No refunds after room details are shared
2. ❌ Not responsible for lag/disconnect issues
3. 🔨 Cheaters will be banned permanently
4. ⚖️ By joining, you accept all risks
5. 👑 Admin decisions are final

💰 PAYMENT TERMS:
1. Pay to UPI: 8435010927@ybl
2. Send screenshot to {ADMIN_USERNAME}
3. Use /paid command with UTR number
4. Wait for admin confirmation

🚫 VIOLATIONS = INSTANT BAN
No Mercy Zone mein mercy nahi milti! 🔥"""

def get_help_message():
    """Get help message"""
    return f"""🆘 HELP & SUPPORT

🎮 USER COMMANDS:
• 🎯 Click menu buttons for navigation
• 💰 /paid - Submit payment proof
• 📜 /matchhistory - View your tournaments
• 🆘 /help - Show this help

📞 SUPPORT CONTACT:
• 📧 Email: {SUPPORT_EMAIL}
• 👑 Admin: {ADMIN_USERNAME}
• 📸 Instagram: {INSTAGRAM_HANDLE}

🔗 IMPORTANT LINKS:
• 📢 Channel: {CHANNEL_URL}
• 💬 Discussion: {DISCUSSION_GROUP_URL}

⚡ QUICK TIPS:
1. Join channel first for tournament access
2. Use your referral code for free entries
3. Pay exactly the tournament fee amount
4. Keep payment screenshot ready
5. Be active in discussion group

🚫 No Mercy Zone - Yahan sirf winners survive karte hain! 🔥"""
