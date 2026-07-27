# BC.GAME Bonus Bot - Quick Start Guide

## ðŸš€ Getting Started

### 1. First Time Setup
The bot is now completely redesigned with a new workflow. Follow these steps:

#### A. Start the Bot
```bash
python bot.py
```

#### B. Test as User
1. Open Telegram and start the bot
2. You'll see the welcome image with benefit-coco.png
3. Enter your BC.GAME UID
4. You'll see a smaller profile card showing:
   - Your username and level
   - Status: Not Verified
   - "ðŸ” Start Verification" button

#### C. Test Verification Process
1. Click "ðŸ” Start Verification" (opens bcgame67.com)
2. Complete the verification on bcgame67.com
3. Return to bot
4. Your status is now "Pending"

### 2. Admin Functions

#### Access Admin Panel
Send `/admin` to the bot (must be in ADMIN_IDS list)

#### Verify a User
1. Click "â³ Pending Verifications"
2. See list of users awaiting approval
3. Click "âœ… Verify [Username]"
4. User receives "Verification Approved!" message

#### Send Verification Error
1. Go to "â³ Pending Verifications"
2. Click "âŒ Error" next to username
3. Select error type:
   - Incorrect Email
   - Incorrect Phone
   - 2FA Issue
   - 2FA Reused
4. User receives specific error message

#### Set Custom Bonus Text
1. Click "ðŸŽ Set Bonus Text"
2. Send message in format: `USER_ID|Bonus text`
   
**Examples:**
```
6942741954|ðŸŽ‰ Claim your exclusive $100 bonus!
6942741954|ðŸ’° Special VIP bonus ready - $50
6942741954|REMOVE
```

When bonus text is set:
- User sees custom text in profile
- "Claim My Bonus Now" button appears

When NOT set:
- User sees animated progress bar
- Text: "Your bonus is being prepared..."

#### Broadcast to All Users
1. Click "ðŸ“¢ Broadcast Message"
2. Send your message text
3. Bot sends to all registered users
4. Shows success/fail count

#### Send to Specific User
1. Click "ðŸ“ Send to User"
2. Enter Telegram User ID
3. Send message content
4. User receives message

### 3. Testing the Complete Flow

#### Test 1: New User Registration
```
User: /start
Bot: Shows welcome image + "Enter your BC.Game UID"
User: [Enters UID]
Bot: Shows small profile card with verification button
```

#### Test 2: Verification Approval
```
User: Clicks "ðŸ” Start Verification"
[Admin approves in /admin panel]
User: Receives "Verification Approved!" message
User: Opens profile â†’ sees bonus section
```

#### Test 3: Bonus Text Control
```
Admin: /admin â†’ Set Bonus Text
Admin: 6942741954|Claim $50 bonus!
[User opens profile]
User: Sees "Claim $50 bonus!" text
User: Sees "ðŸ’° Claim My Bonus Now" button
```

#### Test 4: No Bonus Text (Progress Bar)
```
Admin: /admin â†’ Set Bonus Text
Admin: 6942741954|REMOVE
[User refreshes profile]
User: Sees purple progress bar animating
User: Sees "Your bonus is being prepared..."
User: No claim button (waiting for admin)
```

### 4. Important Configuration

#### BotFather Domain Setup
âš ï¸ **CRITICAL:** Must configure domain in BotFather for mini-apps to work

```
1. Open @BotFather in Telegram
2. Send /setdomain
3. Select your bot
4. Enter: https://bcgametop.github.io
```

Without this, WebApps will open in browser instead of Telegram mini-app.

#### Admin IDs
Edit [config.py](config.py) to add admin user IDs:

```python
ADMIN_IDS = [6942741954, 123456789]  # Add your admin IDs
```

### 5. User Commands

| Command | Description |
|---------|-------------|
| `/start` | Register or view profile |
| `/profile` | View detailed profile info |
| `/help` | Show help message |

### 6. Admin Commands

| Command | Description |
|---------|-------------|
| `/admin` | Open admin panel |
| `/cancel` | Cancel current operation |

### 7. Workflow Summary

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   New User      â”‚
â”‚   /start        â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Welcome Image   â”‚
â”‚ Enter UID       â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Small Profile   â”‚
â”‚ Not Verified    â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ ðŸ” Verification â”‚
â”‚ bcgame67.com â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Admin Reviews   â”‚
â”‚ âœ… or âŒ        â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
    âœ…   â”‚   âŒ
    â”Œâ”€â”€â”€â”€â”´â”€â”€â”€â”€â”
    â–¼         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚Verifiedâ”‚ â”‚ Error  â”‚
â”‚Status  â”‚ â”‚Message â”‚
â””â”€â”€â”€â”¬â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”¬â”€â”€â”€â”€â”˜
    â”‚          â”‚
    â–¼          â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Admin Sets      â”‚
â”‚ Bonus Text?     â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
    Yes  â”‚  No
    â”Œâ”€â”€â”€â”€â”´â”€â”€â”€â”€â”
    â–¼         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Bonus  â”‚ â”‚Progressâ”‚
â”‚ Text   â”‚ â”‚  Bar   â”‚
â”‚+Button â”‚ â”‚(85%)   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### 8. Troubleshooting

#### Problem: WebApp opens in browser
**Solution:** Set BotFather domain to https://bcgametop.github.io

#### Problem: User not seeing bonus text
**Solution:** Admin must set bonus text using format `USER_ID|Text`

#### Problem: Progress bar stuck at 85%
**Explanation:** This is intentional. Shows user is waiting for admin to set bonus text.

#### Problem: Verification errors not showing
**Solution:** Check that error messages are being sent from admin panel correctly

#### Problem: Admin panel not accessible
**Solution:** Verify your Telegram ID is in ADMIN_IDS in config.py

### 9. Features Overview

âœ… **Start Command**
- Welcome image (benefit-coco.png)
- Clean, professional introduction
- Small profile display

âœ… **Verification System**
- bcgame67.com integration
- Admin approval required
- Custom error messages
- Status tracking

âœ… **Admin Controls**
- Pending verifications list
- Quick approve/reject buttons
- Set custom bonus text per user
- Broadcast messages
- Send to specific users

âœ… **Progress System**
- Animated progress bar when no bonus
- Shows 85% (pending admin)
- Smooth animations

âœ… **Bonus Text**
- Admin-controlled messaging
- Per-user customization
- Easy to update/remove

âœ… **Statistics**
- Total users
- Verified count
- Pending count
- Claims tracking

### 10. Next Steps

1. **Start bot:** `python bot.py`
2. **Test user flow:** Send /start as regular user
3. **Test admin panel:** Send /admin as admin
4. **Set bonus text:** Use format shown above
5. **Verify users:** Approve pending verifications
6. **Monitor stats:** Check statistics in admin panel

---

**Need Help?**
- Check [WORKFLOW_DOCUMENTATION.md](WORKFLOW_DOCUMENTATION.md) for complete details
- Review code comments in [bot.py](bot.py), [admin.py](admin.py), [database.py](database.py)
- Test each feature individually before full deployment

**Ready to Launch! ðŸš€**
