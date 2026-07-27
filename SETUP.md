# Quick Setup Guide

## Prerequisites
- Python 3.8 or higher
- Telegram account
- BC.GAME account (for API access)

## Step-by-Step Setup

### 1. Install Python Packages
```bash
pip install -r requirements.txt
```

### 2. Create Your Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command
3. Choose a name (e.g., "BC.GAME Bonus Bot")
4. Choose a username (must end with 'bot', e.g., "bcgame_bonus_bot")
5. Copy the bot token (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 3. Get Your Telegram User ID

1. Open [@userinfobot](https://t.me/userinfobot)
2. Send any message
3. Copy your user ID (e.g., `123456789`)

### 4. Configure config.py

Open `config.py` and update:

```python
# Replace with your bot token from BotFather
BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"

# Replace with your Telegram user ID
ADMIN_IDS = [123456789]

# Update after hosting userprofile.html
WEBAPP_URL = "https://yourdomain.com/userprofile.html"
```

### 5. Host userprofile.html

#### Using GitHub Pages (Recommended)

1. Create a new repository on GitHub
2. Upload `userprofile.html`
3. Go to Settings → Pages
4. Select "Deploy from main branch"
5. Wait a few minutes
6. Your URL will be: `https://username.github.io/repository-name/userprofile.html`
7. Update `WEBAPP_URL` in `config.py`

#### Using Vercel

1. Install Vercel CLI:
   ```bash
   npm i -g vercel
   ```

2. Create a `vercel.json`:
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "userprofile.html",
         "use": "@vercel/static"
       }
     ]
   }
   ```

3. Deploy:
   ```bash
   vercel
   ```

4. Update `WEBAPP_URL` in `config.py` with the provided URL

### 6. Run the Bot

#### Windows
Double-click `start.bat` or run:
```cmd
python bot.py
```

#### Linux/Mac
```bash
python3 bot.py
```

### 7. Test the Bot

1. Open Telegram
2. Search for your bot username
3. Send `/start`
4. Enter a BC.GAME UID
5. Check if profile loads correctly

## Common Issues

### Bot doesn't respond
- ✅ Check bot token is correct
- ✅ Ensure bot.py is running
- ✅ Check console for errors

### Profile not loading
- ✅ Verify BC.GAME API cookies are valid
- ✅ Check UID is correct
- ✅ Look for API errors in console

### WebApp not opening
- ✅ Verify userprofile.html is hosted
- ✅ Check WEBAPP_URL is correct and accessible
- ✅ Ensure it's using HTTPS (not HTTP)

### "Not authorized" error
- ✅ Verify your user ID is in ADMIN_IDS
- ✅ Restart the bot after config changes

## Updating BC.GAME API Cookies

If the API stops working:

1. Open BC.GAME in Chrome/Firefox
2. Press F12 to open DevTools
3. Go to Application → Cookies → https://bc.fun
4. Find `SESSION` cookie → Copy value
5. Find `smidV2` cookie → Copy value
6. Update in `config.py`:
   ```python
   API_CONFIG = {
       'cookies': {
           'SESSION': 'paste_session_cookie_here',
           'smidV2': 'paste_smid_v2_cookie_here'
       },
       ...
   }
   ```
7. Restart the bot

## Next Steps

- Test all bot commands
- Try the admin panel (`/admin`)
- Test profile viewing with different UIDs
- Customize messages in bot.py as needed
- Set up automatic restarts (systemd, pm2, etc.)

## Security Tips

- ⚠️ Never share your bot token
- ⚠️ Never commit config.py to GitHub
- ⚠️ Keep API cookies private
- ⚠️ Only add trusted users to ADMIN_IDS
- ⚠️ Regularly update dependencies

## Need Help?

Check the full README.md for detailed documentation.
