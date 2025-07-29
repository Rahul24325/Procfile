"""
Configuration settings for No Mercy Zone Bot
"""

import os

# Bot Configuration
BOT_TOKEN = "8341741465:AAG81VWIc84evKwBR1IIbwMoaHQJwgLXLsY"
ADMIN_ID = 5558853984
ADMIN_USERNAME = "@Ghost_Commander"
CHANNEL_ID = -1002880573048
CHANNEL_URL = "https://t.me/NoMercyZoneBG"
DISCUSSION_GROUP_URL = "https://t.me/NoMercyZoneBGG"

# Payment Configuration
UPI_ID = "8435010927@ybl"
SUPPORT_EMAIL = "dumwalasquad.in@zohomail.in"
INSTAGRAM_HANDLE = "https://www.instagram.com/ghostinside.me"

# Database Configuration
MONGODB_URI = "mongodb+srv://rahul7241146384:rahul7241146384@cluster0.qeaogc4.mongodb.net/"
DATABASE_NAME = "no_mercy_zone"

# AI Configuration
AI_API_KEY = os.getenv("AI_API_KEY", "d96a2478-7fde-4d76-a28d-b8172e561077")

# Tournament Maps
TOURNAMENT_MAPS = ["Erangel", "Miramar", "Sanhok", "Livik", "Karakin"]

# Prize Pool Templates
PRIZE_POOLS = {
    "solo": {
        "kill_based": {"per_kill": 25, "bonus": 200},
        "fixed": {"winner": 500},
        "rank_based": {"1st": 300, "2nd": 150, "3rd": 50}
    },
    "duo": {
        "kill_based": {"per_kill": 15, "bonus": 300},
        "fixed": {"winner": 1500},
        "rank_based": {"1st": 800, "2nd": 500, "3rd": 200}
    },
    "squad": {
        "kill_based": {"per_kill": 10, "bonus": 500},
        "fixed": {"winner": 2500},
        "rank_based": {"1st": 2000, "2nd": 1200, "3rd": 800}
    }
}

# Entry Fees
ENTRY_FEES = {
    "solo": 50,
    "duo": 80,
    "squad": 200
}
