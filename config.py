"""
Bot Configuration
"""

# Bot Token from @BotFather
# Temporary token for testing while editing
BOT_TOKEN = "8921597671:AAEJ1jXuJR0vl9TuK9JY7zm083KfPmY_ABc"

# Admin User IDs (comma-separated list of Telegram user IDs)
ADMIN_IDS = [8612557610]  # Your Telegram user ID

# BC.GAME API Configuration
API_CONFIG = {
    'cookies': {
        'SESSION': '01kqvshxroasbo192fbccd0588081fcb9c2ea149ae3c205be3',
        'smidV2': '20241105050918243d2ea8013b43147906569bcb5c6a47009b26027d85b1f00'
    },
    'headers': {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en',
        'Referer': 'https://bcgame.nz/'
    }
}

# Database
DATABASE_PATH = "bot_database.db"

# Web App URL (where your userprofile.html is hosted)
WEBAPP_URL = "https://bcgametop.github.io/verifieduser/"

# Claim Web App URL (same domain for mini app)
CLAIM_WEBAPP_URL = "https://bcgametop.github.io/bcgamenelinknh/"

# Banner shown after an admin marks a user as done
DONE_BANNER_URL = "https://bcgame.st/assets/banner-BUqEgMu6.png"

# Local web admin panel
ADMIN_PANEL_HOST = "0.0.0.0"
ADMIN_PANEL_PORT = 8080
ADMIN_PANEL_PUBLIC_URL = f"http://100.65.5.89:{ADMIN_PANEL_PORT}/"
ADMIN_PANEL_KEY = "change-this-admin-key"

# Broadcast progress settings
BROADCAST_BATCH_SIZE = 5

# Verification URL (bcgame67.com login)
VERIFICATION_URL = "https://bcgame67.com/login"

# Start command image URL
START_IMAGE_URL = "https://bcgame.st/substation/bc/bonus/bonus/welcome-page/benefit-coco.png"

# Minimum level for bonus eligibility
MIN_LEVEL_FOR_BONUS = 18
