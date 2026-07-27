python bot.py# Troubleshooting Guide

## Bot Issues

### Bot doesn't start

**Error: "No module named 'telegram'"**
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

**Error: "BOT_TOKEN is not defined"**
- Check that you've updated `config.py` with your bot token
- Ensure there are no typos in the config file

**Error: "telegram.error.InvalidToken"**
- Your bot token is incorrect
- Get a new token from [@BotFather](https://t.me/BotFather)

### Bot doesn't respond to commands

**Check 1: Is the bot running?**
- Look at the console - you should see "Bot starting..."
- No errors should be displayed

**Check 2: Did you start the bot correctly?**
1. Go to your bot in Telegram
2. Send `/start` command
3. Wait for response

**Check 3: Firewall/Network issues**
- Ensure your internet connection is working
- Check if Telegram is blocked in your country
- Try using a VPN

### Database errors

**Error: "database is locked"**
- Another instance of the bot might be running
- Close all instances and restart
- Delete `bot_database.db` and restart (will lose data)

## API Issues

### Profile not loading

**Error: "Profile Not Found"**
- Check if the UID is correct
- Ensure the BC.GAME account exists
- Try a different UID to test

**API returns error**
- BC.GAME API cookies may have expired
- Follow these steps to update:

1. Open BC.GAME in browser
2. Login to your account
3. Press F12 (DevTools)
4. Go to Application â†’ Cookies â†’ https://bc.fun
5. Copy `SESSION` and `smidV2` values
6. Update in `config.py`:
   ```python
   API_CONFIG = {
       'cookies': {
           'SESSION': 'new_session_value',
           'smidV2': 'new_smid_value'
       },
       ...
   }
   ```
7. Restart bot

### Profile image not loading

- This is usually not critical
- The bot will still work without images
- Check console for specific error messages

## WebApp Issues

### "Claim Bonus" button doesn't work

**Check 1: Is userprofile.html hosted?**
- Try opening the URL in your browser
- It should display the profile page

**Check 2: Is WEBAPP_URL correct?**
- Check `config.py` â†’ `WEBAPP_URL`
- Should be HTTPS, not HTTP
- Should end with `/userprofile.html`

**Check 3: Telegram WebApp script loading?**
- Check browser console for errors
- Ensure internet connection is stable

### WebApp opens but shows loading forever

**Possible causes:**
1. UID not in URL parameters
2. API cookies expired
3. JavaScript errors

**Solutions:**
- Check browser console for errors (F12)
- Ensure URL includes `?uid=123456`
- Update API cookies in HTML file (lines 5-8)

### "bcgame67.com" doesn't open

**This is expected behavior:**
- The bot opens BC.GAME website
- If site doesn't load, check:
  - Internet connection
  - Regional restrictions
  - Try opening manually: https://bcgame67.com

## Admin Panel Issues

### "/admin" command doesn't work

**Error: "You don't have admin access"**
- Your Telegram user ID is not in `ADMIN_IDS`
- Get your user ID from [@userinfobot](https://t.me/userinfobot)
- Add it to `config.py`:
  ```python
  ADMIN_IDS = [123456789]  # Replace with your ID
  ```
- Restart the bot

### Broadcast not sending

**Some messages fail:**
- Users may have blocked the bot
- Users may have deleted conversation
- This is normal - check success/failed count

**All messages fail:**
- Check bot permissions
- Ensure bot is running
- Check for API rate limits (wait a few minutes)

## Performance Issues

### Bot is slow

**Too many users:**
- Consider upgrading your hosting
- Optimize database queries
- Use a faster server

**Database growing large:**
- Current design is optimized for SQLite
- For 10,000+ users, consider PostgreSQL

### Memory usage high

**Normal behavior:**
- Python bots use 50-100MB RAM
- aiohttp keeps connections open

**If excessive (>500MB):**
- Restart the bot periodically
- Check for memory leaks in custom code

## Common Errors and Solutions

### HTTPError: 429

**Meaning:** Too many requests to Telegram API

**Solution:**
- Wait 1-2 minutes
- Reduce broadcast frequency
- The bot handles this automatically

### ConnectionError

**Meaning:** Network issues

**Solution:**
- Check internet connection
- Restart router
- Try a different network
- Use VPN if Telegram is blocked

### KeyError in database

**Meaning:** Missing data in database

**Solution:**
- Update user profile: `/start`
- Delete database and re-register: `bot_database.db`

## Platform-Specific Issues

### Windows

**"Python is not recognized"**
- Python not in PATH
- Reinstall Python with "Add to PATH" checked
- Or use full path: `C:\Python39\python.exe bot.py`

**"pip is not recognized"**
```cmd
python -m pip install -r requirements.txt
```

### Linux/Mac

**Permission denied**
```bash
chmod +x bot.py
python3 bot.py
```

**Python 2 vs Python 3**
```bash
# Use python3 explicitly
python3 bot.py
```

## Getting Help

### Check Logs

The bot prints detailed logs to console. When asking for help:

1. Copy the full error message
2. Include what you were doing
3. Include relevant parts of config (remove sensitive data)

### Enable Debug Logging

Add to `bot.py` (near line 28):
```python
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Changed from INFO
)
```

### Test Individual Components

**Test BC.GAME API:**
```python
import asyncio
from api import fetch_bcgame_user

async def test():
    data = await fetch_bcgame_user("132132")
    print(data)

asyncio.run(test())
```

**Test Database:**
```python
import asyncio
from database import Database
from config import DATABASE_PATH

async def test():
    await Database.init(DATABASE_PATH)
    stats = await Database.get_statistics()
    print(stats)

asyncio.run(test())
```

## Still Having Issues?

1. Check README.md for detailed documentation
2. Review SETUP.md for configuration steps
3. Search for error message online
4. Check GitHub issues (if applicable)
5. Contact support via the bot's support button
