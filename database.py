"""
Database operations for No Mercy Zone Bot
"""

from pymongo import MongoClient
from datetime import datetime, timezone
import random
import string
from config import MONGODB_URI, DATABASE_NAME

# Global database connection
client = None
db = None

def init_database():
    """Initialize database connection"""
    global client, db
    try:
        client = MongoClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        
        # Test connection
        client.admin.command('ping')
        print("✅ Database connected successfully!")
        
        # Create indexes
        db.users.create_index("user_id", unique=True)
        db.tournaments.create_index("tournament_id", unique=True)
        db.payments.create_index("user_id")
        db.referrals.create_index("referrer_id")
        
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def generate_referral_code():
    """Generate unique referral code"""
    while True:
        code = "REF" + ''.join(random.choices(string.digits, k=6))
        if not db.users.find_one({"referral_code": code}):
            return code

def create_user(user_id, username, first_name):
    """Create new user in database"""
    referral_code = generate_referral_code()
    user_data = {
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "paid": False,
        "confirmed": False,
        "balance": 0,
        "referral_code": referral_code,
        "joined_at": datetime.now(timezone.utc),
        "is_member": False,
        "banned": False,
        "tournaments_joined": [],
        "total_spent": 0,
        "total_earned": 0
    }
    
    try:
        db.users.insert_one(user_data)
        return user_data
    except:
        return db.users.find_one({"user_id": user_id})

def get_user(user_id):
    """Get user from database"""
    return db.users.find_one({"user_id": user_id})

def update_user(user_id, update_data):
    """Update user data"""
    return db.users.update_one({"user_id": user_id}, {"$set": update_data})

def create_tournament(tournament_data):
    """Create new tournament"""
    tournament_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    tournament_data["tournament_id"] = tournament_id
    tournament_data["created_at"] = datetime.now(timezone.utc)
    tournament_data["participants"] = []
    tournament_data["status"] = "upcoming"
    
    db.tournaments.insert_one(tournament_data)
    return tournament_data

def get_active_tournaments():
    """Get all active tournaments"""
    return list(db.tournaments.find({"status": {"$in": ["upcoming", "live"]}}))

def join_tournament(user_id, tournament_id):
    """Join user to tournament"""
    result = db.tournaments.update_one(
        {"tournament_id": tournament_id},
        {"$addToSet": {"participants": user_id}}
    )
    
    if result.modified_count > 0:
        db.users.update_one(
            {"user_id": user_id},
            {"$addToSet": {"tournaments_joined": tournament_id}}
        )
    
    return result.modified_count > 0

def create_payment_request(user_id, tournament_id, amount, utr):
    """Create payment request"""
    payment_data = {
        "user_id": user_id,
        "tournament_id": tournament_id,
        "amount": amount,
        "utr": utr,
        "status": "pending",
        "created_at": datetime.now(timezone.utc)
    }
    
    db.payments.insert_one(payment_data)
    return payment_data

def get_pending_payments():
    """Get all pending payments"""
    return list(db.payments.find({"status": "pending"}))

def confirm_payment(user_id, tournament_id):
    """Confirm payment"""
    payment_result = db.payments.update_one(
        {"user_id": user_id, "tournament_id": tournament_id},
        {"$set": {"status": "confirmed", "confirmed_at": datetime.now(timezone.utc)}}
    )
    
    user_result = db.users.update_one(
        {"user_id": user_id},
        {"$set": {"paid": True, "confirmed": True}}
    )
    
    return payment_result.modified_count > 0 and user_result.modified_count > 0

def decline_payment(user_id, tournament_id):
    """Decline payment"""
    return db.payments.update_one(
        {"user_id": user_id, "tournament_id": tournament_id},
        {"$set": {"status": "declined", "declined_at": datetime.now(timezone.utc)}}
    )

def get_financial_data(period="today"):
    """Get financial data for specified period"""
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    if period == "today":
        start_date = today
    elif period == "weekly":
        start_date = today.replace(day=today.day - 7)
    elif period == "monthly":
        start_date = today.replace(day=1)
    else:
        start_date = today
    
    pipeline = [
        {"$match": {
            "status": "confirmed",
            "confirmed_at": {"$gte": start_date}
        }},
        {"$group": {
            "_id": None,
            "total_revenue": {"$sum": "$amount"},
            "total_transactions": {"$sum": 1}
        }}
    ]
    
    result = list(db.payments.aggregate(pipeline))
    if result:
        return result[0]
    else:
        return {"total_revenue": 0, "total_transactions": 0}

def ban_user(user_id):
    """Ban user"""
    return db.users.update_one(
        {"user_id": user_id},
        {"$set": {"banned": True, "banned_at": datetime.now(timezone.utc)}}
    )

def unban_user(user_id):
    """Unban user"""
    return db.users.update_one(
        {"user_id": user_id},
        {"$set": {"banned": False}, "$unset": {"banned_at": 1}}
    )

def get_tournament_participants(tournament_id):
    """Get tournament participants"""
    tournament = db.tournaments.find_one({"tournament_id": tournament_id})
    if tournament and "participants" in tournament:
        users = list(db.users.find({"user_id": {"$in": tournament["participants"]}}))
        return users
    return []

def update_tournament(tournament_id, update_data):
    """Update tournament data"""
    return db.tournaments.update_one(
        {"tournament_id": tournament_id},
        {"$set": update_data}
    )

def delete_tournament(tournament_id):
    """Delete tournament"""
    return db.tournaments.delete_one({"tournament_id": tournament_id})

def schedule_notification(notification_data):
    """Schedule a notification in the database"""
    try:
        db.notifications.insert_one(notification_data)
        return True
    except Exception as e:
        print(f"Failed to schedule notification: {e}")
        return False

def get_ai_tournament_suggestion(tournament_type):
    """Get AI tournament suggestion with advanced analysis"""
    # Mock data - replace with actual AI API call
    from datetime import datetime, timedelta
    import random
    
    next_time = get_next_tournament_time()
    
    tournament_names = {
        'solo': ['GHOST COMMANDER SOLO', 'DEATH MATCH ROYAL', 'LONE WOLF HUNT'],
        'duo': ['DEADLY DUO SHOWDOWN', 'PARTNER ELIMINATION', 'TWIN STRIKE'],
        'squad': ['SQUAD ANNIHILATION', 'TEAM DESTROYER', 'SQUAD SUPREMACY']
    }
    
    confidence_score = random.randint(75, 95)
    
    suggestion = {
        'name': random.choice(tournament_names[tournament_type]),
        'type': tournament_type,
        'date': next_time['date'],
        'time': next_time['time'],
        'map': random.choice(['Erangel', 'Sanhok', 'Miramar', 'Vikendi']),
        'entry_fee': random.choice([15, 20, 25, 30]),
        'prize_type': random.choice(['rank_based', 'kill_based', 'fixed']),
        'confidence': confidence_score,
        'reasoning': f"AI analysis shows {confidence_score}% success probability based on player patterns.",
        'optimal_participants': random.randint(12, 20)
    }
    
    return suggestion

# database.py (inside your MongoDB class)

async def save_payment(self, payment_data):
    await self.payments.insert_one(payment_data)

async def get_payment(self, user_id, tournament_id=None):
    query = {"user_id": user_id}
    if tournament_id:
        query["tournament_id"] = tournament_id
    return await self.payments.find_one(query)

async def get_tournament(self, tournament_id):
    return await self.tournaments.find_one({"tournament_id": tournament_id})
