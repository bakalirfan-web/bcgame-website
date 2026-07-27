# BC.GAME Bonus Bot - Complete Workflow Documentation

## ðŸŽ¯ Overview
Complete redesign of the BC.GAME bonus bot with verification system, admin controls, and smooth user experience.

## ðŸ“‹ New Features

### 1. **Start Command with Welcome Image**
- Displays benefit-coco.png image on `/start`
- Caption: "Please enter your BC.Game UID to proceed with the bonus claim"
- For existing users: Shows smaller profile with verification status

### 2. **User Registration Flow**
```
/start â†’ Welcome Image â†’ Enter UID â†’ Smaller Profile Display â†’ Verification Required
```

**For new users:**
- Image displayed with welcome message
- User enters BC.GAME UID
- Profile registered
- Shows smaller profile card with:
  - Username
  - UID
  - Level
  - Status: Not Verified
  - "ðŸ” Start Verification" button

**For returning users:**
- Shows compact profile
- Verification status displayed
- If verified: "ðŸŽ Open Profile & Claim Bonus" button
- If not verified: "ðŸ” Start Verification" button + verification status message

### 3. **Verification System**
**User Side:**
- Click "ðŸ” Start Verification" â†’ Opens bcgame67.com in Telegram mini-app
- User completes login/verification
- Status tracked in database

**Admin Side:**
- `/admin` â†’ "â³ Pending Verifications"
- See list of users awaiting verification
- For each user, two options:
  1. **âœ… Verify User** - Approve verification
  2. **âŒ Error** - Send error message

**Verification Error Options:**
- Incorrect Email
- Incorrect Phone
- 2FA Issue
- 2FA Reused/Expired

When admin selects an error:
- User receives specific error message
- Verification status updated in database
- User can retry verification

When admin approves:
- User receives "âœ… Verification Approved!" message
- "ðŸŽ Open Profile & Claim Bonus" button becomes available
- User can now access full profile and bonuses

### 4. **Admin Panel Features**
Access: `/admin` command (only for users in ADMIN_IDS list)

**Main Menu:**
- ðŸ“Š Statistics
- ðŸ‘¥ User List
- â³ Pending Verifications
- ðŸ“¢ Broadcast Message
- ðŸ“· Send Photo
- ðŸ“ Send to User
- ðŸŽ Set Bonus Text
- ðŸ”„ Refresh Stats

#### Statistics
Shows:
- Total Users
- Verified Users
- Pending Verification
- Total Claims
- Last Updated timestamp

#### User List
- First 20 users displayed
- Shows username, UID, level
- Checkmark (âœ…) for verified, hourglass (â³) for pending

#### Pending Verifications
- List of unverified users
- Quick action buttons:
  - âœ… Verify [username]
  - âŒ Error (shows error options)

#### Broadcast Message
1. Admin clicks "ðŸ“¢ Broadcast Message"
2. Sends next message text
3. Bot broadcasts to all users
4. Shows success/fail count

#### Send Photo
1. Admin clicks "ðŸ“· Send Photo"
2. Sends photo with caption
3. Broadcasts to all users

#### Send to User
1. Admin clicks "ðŸ“ Send to User"
2. Enters Telegram User ID
3. Sends message content
4. Message delivered to specific user

#### Set Bonus Text
Admin sets custom bonus text for specific user:

**Format:** `USER_ID|Bonus text message`

**Example:** `123456789|ðŸŽ‰ Claim your $50 bonus now!`

**To remove:** `123456789|REMOVE`

This text appears in the user's profile page as bonus description.

### 5. **UserProfile Page Enhancements**

#### Progress Bar (No Bonus Text Set)
When admin hasn't set bonus text:
- Purple animated progress bar displayed
- Text: "Your bonus is being prepared..."
- Shows "Verifying eligibility..." message
- Progress animates to 85% (indicating admin approval pending)

#### Bonus Text Display (Admin Set)
When admin sets bonus text:
- Custom bonus message displayed
- "ðŸ’° Claim My Bonus Now" button shows
- User can click to claim

**URL Parameter:** `bonus_text` added to WebApp URL
- Example: `?uid=123&bonus_text=Claim%20your%20bonus!`

### 6. **Database Schema Updates**

**New Columns in `users` table:**
```sql
verified INTEGER DEFAULT 0
verification_status TEXT DEFAULT ''
bonus_text TEXT DEFAULT NULL
```

**Updated `statistics` table:**
```sql
verified_users INTEGER DEFAULT 0
pending_users INTEGER DEFAULT 0
```

**New Database Methods:**
- `update_verification_status(telegram_id, verified, status)`
- `get_pending_verifications()` - Returns list of unverified users
- `set_bonus_text(telegram_id, bonus_text)` - Sets custom bonus text
- `update_statistics()` - Manually refresh stats

### 7. **Configuration Updates**

**config.py additions:**
```python
VERIFICATION_URL = "https://bcgame67.com/login"
START_IMAGE_URL = "https://bcgame.st/substation/bc/bonus/bonus/welcome-page/benefit-coco.png"
```

## ðŸ”„ Complete User Journey

### New User Flow
1. **Start:** User sends `/start` to bot
2. **Welcome:** Welcome image + "Please enter your BC.Game UID"
3. **Registration:** User sends UID
4. **Profile Display:** Small profile card shown with "Not Verified" status
5. **Verification:** User clicks "ðŸ” Start Verification"
6. **bcgame67.com:** Opens in mini-app for login
7. **Admin Review:** Admin sees user in pending list
8. **Admin Action:** 
   - âœ… Approves â†’ User gets verified
   - âŒ Error â†’ User gets specific error message
9. **Set Bonus:** Admin sets bonus text (optional)
10. **User Access:** User opens profile
11. **Bonus Display:** 
    - If bonus text set: Shows text + claim button
    - If no bonus text: Shows progress bar
12. **Claim:** User clicks claim button â†’ Bot sends claim WebApp

### Returning User Flow
1. User sends `/start`
2. Shows compact profile with current status
3. If verified: Direct access to profile page
4. If not verified: Verification button + status message

## ðŸ› ï¸ Admin Workflow

### Approve Verification
```
/admin â†’ Pending Verifications â†’ âœ… Verify [User] â†’ User notified
```

### Reject with Error
```
/admin â†’ Pending Verifications â†’ âŒ Error â†’ Select Error Type â†’ User notified
```

### Set Bonus Text
```
/admin â†’ Set Bonus Text â†’ Send: USER_ID|Bonus message â†’ Confirmed
```

### Broadcast Announcement
```
/admin â†’ Broadcast Message â†’ Send message text â†’ Broadcast to all users
```

### Send to Specific User
```
/admin â†’ Send to User â†’ Enter User ID â†’ Send message â†’ Delivered
```

## ðŸŽ¨ UI/UX Improvements

### Smooth Loading
- Profile page loads without lag
- Progress bar animates smoothly
- Transitions between states are seamless

### Progress Indication
- Loading states clearly shown
- Progress bar for pending bonus approval
- Status messages always visible

### Verification Status Display
- Clear indication of verified/unverified status
- Specific error messages when verification fails
- Admin-controlled verification messages

### Bonus Text Control
- Admin has full control over bonus messaging
- Progress bar shown when no bonus set
- Custom bonus text displayed when admin sets it
- Smooth transition between states

## ðŸ“± Telegram Mini-App Integration

### bcgame67.com Verification
- Opens in Telegram mini-app (same domain as bot's WebApp domain)
- User completes login/2FA
- Returns to bot after completion

### Profile Page
- Opens in mini-app
- Shows full BC.GAME profile with medals, stats, VIP badges
- Responsive design
- BC.GAME styling maintained

### Claim Page
- Opens in mini-app (bcgametop.github.io/bcgamenelinknh/)
- Same-domain ensures mini-app functionality
- Smooth claim process

## ðŸ” Admin Security

- Only users in `ADMIN_IDS` list can access admin panel
- All admin actions logged
- Verification status changes tracked
- User data protected

## ðŸ“Š Statistics Tracking

### Automatically Updated
- Total users count
- Verified users count
- Pending verifications count
- Total claims count

### Manual Refresh
Admin can manually refresh stats with "ðŸ”„ Refresh Stats" button

## ðŸš€ Deployment Notes

1. **BotFather Domain:** Must be set to `https://bcgametop.github.io`
2. **Database:** Will auto-migrate with new columns on first run
3. **Dependencies:** No new dependencies required
4. **Python Version:** Python 3.8+ required

## âš¡ Quick Start Commands

**User Commands:**
- `/start` - Register or view profile
- `/profile` - View detailed profile
- `/help` - Show help message

**Admin Commands:**
- `/admin` - Open admin panel
- `/cancel` - Cancel current admin operation

## ðŸŽ¯ Key Improvements

âœ… Professional welcome experience with image
âœ… Smaller, cleaner profile displays
âœ… Complete verification system with admin controls
âœ… Custom error messages for verification failures
âœ… Admin-controlled bonus text
âœ… Progress bar for pending bonuses
âœ… Broadcast system for announcements
âœ… Send messages to specific users
âœ… Enhanced statistics tracking
âœ… Smooth, lag-free user experience
âœ… Complete mini-app integration

## ðŸ“ Notes

- Progress bar animates to 85% to indicate admin approval pending
- Bonus text parameter passed via URL to profile page
- All WebApp URLs automatically include bonus text when set
- Verification status persists across sessions
- Admin can change bonus text anytime (updates immediately)
