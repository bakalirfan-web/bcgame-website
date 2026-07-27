# BC.GAME Bonus Telegram Bot

A comprehensive Telegram bot for BC.GAME users to check their profile, eligibility for bonuses, and claim rewards.

## Features

- âœ… BC.GAME UID registration
- ðŸ“Š Profile statistics (level, VIP, wagered, wins, bets)
- ðŸŽ Bonus eligibility checking (Level 18+)
- ðŸ–¼ï¸ Profile picture display
- ðŸ“± Telegram WebApp integration
- ðŸ‘¨â€ðŸ’¼ Admin panel with:
  - User statistics
  - Background broadcasting with progress updates
  - User management
  - Mark Done flow with chat cleanup and banner message
  - Eligible users list
  - Local web admin panel

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Bot

Edit `config.py` and set:

- `BOT_TOKEN`: Your Telegram bot token from [@BotFather](https://t.me/BotFather)
- `ADMIN_IDS`: List of Telegram user IDs for admin access
- `WEBAPP_URL`: URL where your userprofile.html is hosted
- `API_CONFIG`: BC.GAME API credentials (already configured)

#### Getting Your Telegram User ID

1. Send a message to [@userinfobot](https://t.me/userinfobot)
2. Copy your user ID
3. Add it to `ADMIN_IDS` list in `config.py`

#### Getting Bot Token

1. Open [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` command
3. Follow instructions to create a bot
4. Copy the token and paste it in `config.py`

### 3. Host the HTML File

You need to host `userprofile.html` on a web server (GitHub Pages, Vercel, Netlify, etc.)

#### Option 1: GitHub Pages (Free & Easy)

1. Create a new GitHub repository
2. Upload `userprofile.html`
3. Enable GitHub Pages in repository settings
4. Use the provided URL in `config.py` under `WEBAPP_URL`

#### Option 2: Vercel (Free)

1. Install Vercel CLI: `npm i -g vercel`
2. Run `vercel` in the project directory
3. Deploy the HTML file
4. Use the provided URL in `config.py`

### 4. Run the Bot

```bash
python bot.py
```

## Usage

### For Users

1. Start the bot: `/start`
2. Enter your BC.GAME UID
3. View your profile and check eligibility
4. If level 18+, claim your bonus!

### For Admins

1. Use `/admin` to open admin panel
2. View statistics
3. Manage users
4. Broadcast messages to all users

## Commands

### User Commands
- `/start` - Register or view profile
- `/profile` - View your profile details
- `/help` - Show help message

### Admin Commands
- `/admin` - Open admin panel
- View statistics
- User management
- Broadcast messages

## Admin Panel Features

### Statistics
- Total users
- Eligible users (Level 18+)
- Total claims
- Last updated timestamp

### User Management
- View all users
- View eligible users only
- User details (UID, level, VIP status)

### Broadcasting
- Send messages to all users
- Broadcast runs in the background so the bot keeps responding
- Telegram progress message updates after every 5 successful sends
- Latest batch list shows the users reached in that batch
- Success/failure tracking
- HTML formatting support

### Mark Done
- Admin clicks `Mark Done`, enters the BC.GAME UID, and the bot marks that user done immediately
- Tracked bot messages in the user chat are deleted where Telegram allows it
- User receives a congratulations message with the banner button:
  `https://bcgame.st/assets/banner-BUqEgMu6.png`
- Done users see that banner URL instead of the old `bcgame67.com` claim URL when they return to the bot

### Web Admin Panel
- Running `python bot.py` also starts a local panel at `http://127.0.0.1:8080/`
- You can also run it alone with:

```bash
python admin_web.py
```

- Access key is configured in `config.py` as `ADMIN_PANEL_KEY`
- The panel shows a scrollable users list with BC.GAME avatar, BC username, Telegram username/ID, UID, level, verification, and Mark Done status
- Every user row includes a Profile button for that user's BC.GAME profile web view
- Tier filters show All, Beginner, Bronze, Silver, Gold, Platinum, and Diamond users
- `Refresh API` on a user row updates that user's saved BC.GAME level and tier from the live API
- `Sync API` starts a background refresh for all users so stale local levels are corrected
- Send/Mark Done actions show in-button progress and a 3-second success toast
- The panel can send a direct message by UID, start a text broadcast, mark users done, and view live statistics

## File Structure

```
bcgame bot+link/
â”œâ”€â”€ bot.py              # Main bot file
â”œâ”€â”€ config.py           # Configuration file
â”œâ”€â”€ database.py         # Database operations
â”œâ”€â”€ api.py              # BC.GAME API functions
â”œâ”€â”€ admin.py            # Admin commands and panel
â”œâ”€â”€ admin_web.py        # Local web admin API/server
â”œâ”€â”€ admin_panel.html    # Local web admin UI
â”œâ”€â”€ requirements.txt    # Python dependencies
â”œâ”€â”€ userprofile.html    # Profile web app (host separately)
â”œâ”€â”€ ADMIN_CHANGE_NOTES.md # Notes for future admin changes
â””â”€â”€ README.md          # This file
```

## Database

The bot automatically creates an SQLite database (`bot_database.db`) with:

- **users table**: User profiles and BC.GAME data
- **statistics table**: Bot statistics

## Security Notes

- Never share your `BOT_TOKEN`
- Never share your BC.GAME API credentials
- Keep `config.py` private
- Admin commands are restricted to users in `ADMIN_IDS`

## Troubleshooting

### Bot doesn't respond
- Check if bot token is correct
- Ensure bot is running
- Check internet connection

### Profile not loading
- Verify BC.GAME API credentials in `config.py`
- Check UID is correct
- Check API endpoint accessibility

### WebApp not opening
- Ensure `userprofile.html` is hosted properly
- Check `WEBAPP_URL` in `config.py`
- Verify Telegram WebApp script is loaded

### Admin panel not accessible
- Ensure your Telegram user ID is in `ADMIN_IDS`
- Check you're using the correct user account

## API Configuration

The bot uses BC.GAME API with session cookies. If API stops working:

1. Open BC.GAME in browser
2. Login to your account
3. Open DevTools (F12)
4. Go to Application/Storage > Cookies
5. Copy `SESSION` and `smidV2` values
6. Update `API_CONFIG` in `config.py`

## Support

For issues or questions, contact the bot admin via the Support button in the profile.

## License

This project is for educational purposes. Use responsibly and comply with BC.GAME's terms of service.
