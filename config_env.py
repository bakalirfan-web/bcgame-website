"""
Optional: Environment Variables Configuration
To use this, rename to config.py and set environment variables
"""
import os

# Bot Token from @BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Admin User IDs (comma-separated)
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "123456789")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_STR.split(",") if x.strip()]

# BC.GAME API Configuration
API_CONFIG = {
    'cookies': {
        'SESSION': os.getenv("BCGAME_SESSION_COOKIE", '01kqvshxroasbo192fbccd0588081fcb9c2ea149ae3c205be3'),
        'smidV2': os.getenv("BCGAME_SMID_V2_COOKIE", '20241105050918243d2ea8013b43147906569bcb5c6a47009b26027d85b1f00')
    },
    'headers': {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en',
        'Referer': 'https://bc.fun/'
    }
}

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", "bot_database.db")

# Web App URL (where your userprofile.html is hosted)
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://yourdomain.com/userprofile.html")

# Minimum level for bonus eligibility
MIN_LEVEL_FOR_BONUS = int(os.getenv("MIN_LEVEL_FOR_BONUS", "18"))
