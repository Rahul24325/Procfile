"""Database operations for No Mercy Zone Bot (Fixed Version + Async Stubs)"""

from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
import random
import string
from config import MONGODB_URI, DATABASE_NAME

# Connect to MongoDB
try:
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]

    # Create indexes
    db.users.create_index("user_id", unique=True)
    db.tournaments.create_index("tournament_id", unique=True)
    db.payments.create_index([("user_id", 1), ("tournament_id", 1)], unique=True)
    db.referrals.create_index("referrer_id")

    print("✅ Database connected successfully!")

except Exception as e:
    print(f"❌ Database connection failed: {e}")


# === Core Functions ===

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
        "confirmed": False,
        "balance": 0,
        "referral_code": referral_code,
        "joined_at": datetime.now(timezone.utc),
        "is_member": False,
        "banned": False,
        "tournaments_joined": [],
        "total_spent": 0,
        "total_earned": 0,
        "payments": []
    }
    try:
        db.users.insert_one(user_data)
        return user_data
    except:
        return db.users.find_one({"user_id": user_id})


def get_user(user_id):
    return db.users.find_one({"user_id": user_id})


def update_user(user_id, update_data):
    return db.users.update_one({"user_id": user_id}, {"$set": update_data})


def create_tournament(tournament_data):
    tournament_id = 'TN' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    tournament_data["tournament_id"] = tournament_id
    tournament_data["created_at"] = datetime.now(timezone.utc)
    tournament_data["participants"] = []
    tournament_data["status"] = "upcoming"
    tournament_data["confirmed_payments"] = 0

    db.tournaments.insert_one(tournament_data)
    return tournament_data


def get_tournament(tournament_id):
    return db.tournaments.find_one({"tournament_id": tournament_id})


def get_active_tournaments():
    return list(db.tournaments.find({"status": {"$in": ["upcoming", "live"]}}))


def join_tournament(user_id, tournament_id):
    payment = db.payments.find_one({
        "user_id": user_id,
        "tournament_id": tournament_id,
        "status": "confirmed"
    })

    if not payment:
        return False

    tournament_update = db.tournaments.update_one(
        {"tournament_id": tournament_id},
        {
            "$addToSet": {"participants": user_id},
            "$inc": {"confirmed_payments": 1}
        }
    )

    user_update = db.users.update_one(
        {"user_id": user_id},
        {
            "$addToSet": {"tournaments_joined": tournament_id},
            "$inc": {"total_spent": payment["amount"]}
        }
    )

    return tournament_update.modified_count > 0 and user_update.modified_count > 0


def create_payment_request(user_id, tournament_id, amount, utr):
    existing_payment = db.payments.find_one({
        "user_id": user_id,
        "tournament_id": tournament_id
    })

    if existing_payment:
        if existing_payment["status"] != "confirmed":
            db.payments.update_one(
                {"_id": existing_payment["_id"]},
                {"$set": {
                    "amount": amount,
                    "utr": utr,
                    "status": "pending",
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            return existing_payment
        else:
            return None

    payment_data = {
        "user_id": user_id,
        "tournament_id": tournament_id,
        "amount": amount,
        "utr": utr,
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    db.payments.insert_one(payment_data)
    db.users.update_one(
        {"user_id": user_id},
        {"$push": {"payments": {
            "tournament_id": tournament_id,
            "amount": amount,
            "utr": utr,
            "status": "pending",
            "timestamp": datetime.now(timezone.utc)
        }}}
    )

    return payment_data


def confirm_payment(user_id, tournament_id):
    payment_update = db.payments.update_one(
        {"user_id": user_id, "tournament_id": tournament_id},
        {"$set": {
            "status": "confirmed",
            "confirmed_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }}
    )

    if payment_update.modified_count == 0:
        return False

    user_payment_update = db.users.update_one(
        {
            "user_id": user_id,
            "payments.tournament_id": tournament_id
        },
        {"$set": {
            "payments.$.status": "confirmed",
            "confirmed": True,
            "payments.$.confirmed_at": datetime.now(timezone.utc)
        }}
    )

    payment = db.payments.find_one({
        "user_id": user_id,
        "tournament_id": tournament_id
    })

    if payment:
        db.tournaments.update_one(
            {"tournament_id": tournament_id},
            {"$inc": {"total_collected": payment["amount"]}}
        )

    return user_payment_update.modified_count > 0


def decline_payment(user_id, tournament_id):
    payment_update = db.payments.update_one(
        {"user_id": user_id, "tournament_id": tournament_id},
        {"$set": {
            "status": "declined",
            "declined_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }}
    )

    user_payment_update = db.users.update_one(
        {
            "user_id": user_id,
            "payments.tournament_id": tournament_id
        },
        {"$set": {
            "payments.$.status": "declined",
            "payments.$.declined_at": datetime.now(timezone.utc)
        }}
    )

    return payment_update.modified_count > 0 and user_payment_update.modified_count > 0


def has_paid_for_tournament(user_id, tournament_id):
    payment = db.payments.find_one({
        "user_id": user_id,
        "tournament_id": tournament_id,
        "status": "confirmed"
    })
    return payment is not None


def get_pending_payments():
    return list(db.payments.find({"status": "pending"}))


def get_financial_data(period="today"):
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    if period == "today":
        start_date = today
    elif period == "weekly":
        start_date = today - timedelta(days=7)
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
            "total_transactions": {"$sum": 1},
            "unique_users": {"$addToSet": "$user_id"}
        }},
        {"$project": {
            "total_revenue": 1,
            "total_transactions": 1,
            "unique_users": {"$size": "$unique_users"}
        }}
    ]

    result = list(db.payments.aggregate(pipeline))
    if result:
        return result[0]
    else:
        return {"total_revenue": 0, "total_transactions": 0, "unique_users": 0}


# === Async stubs (not active unless using motor) ===

async def save_payment(payment_data):
    return db.payments.insert_one(payment_data)

async def get_payment(user_id):
    return db.payments.find_one({"user_id": user_id})

async def get_tournament_async(tournament_id):
    return db.tournaments.find_one({"tournament_id": tournament_id})

def init_database():
    try:
        client = MongoClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        db.users.create_index("user_id", unique=True)
        print("✅ Database initialized!")
    except Exception as e:
        print("❌ Error initializing database:", e)
