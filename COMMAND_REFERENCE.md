# BC.GAME Bonus Bot - Command Reference

## ðŸ‘¤ User Commands

### `/start`
**Description:** Start the bot or view your profile

**New User:**
- Shows welcome image (benefit-coco.png)
- Prompts for BC.GAME UID input
- Displays registration status

**Existing User:**
- Shows compact profile card
- Displays verification status
- Shows appropriate action button

---

### `/profile`
**Description:** View detailed profile information

**Displays:**
- Username
- BC.GAME UID
- VIP Level
- Total Wagered
- Wins/Bets statistics
- Verification status
- Profile button (if verified)

---

### `/help`
**Description:** Display help information

**Shows:**
- Available commands
- How the bot works
- Level requirements
- Admin commands (if admin)

---

## ðŸ”§ Admin Commands

### `/admin`
**Access:** Only users in `ADMIN_IDS` list
**Description:** Open the admin control panel

**Main Menu Options:**

#### ðŸ“Š Statistics
Shows:
- Total Users
- Verified Users
- Pending Verifications
- Total Claims
- Last Updated

---

#### ðŸ‘¥ User List
Displays:
- First 20 registered users
- Username, UID, Level
- Verification status (âœ… verified, â³ pending)

---

#### â³ Pending Verifications
**Purpose:** Manage users awaiting verification

**For Each User:**
- Username and Telegram ID
- BC.GAME UID and Level
- Two action buttons:
  - **âœ… Verify [Username]** - Approve user
  - **âŒ Error** - Send error message

**Verification Error Options:**
1. Incorrect Email
2. Incorrect Phone
3. 2FA Issue
4. 2FA Reused/Expired

**When You Approve:**
- User receives "Verification Approved!" message
- User gets "Open Profile & Claim Bonus" button
- Can access bonuses immediately

**When You Send Error:**
- User receives specific error message
- Can retry verification
- Status updated in database

---

#### ðŸ“¢ Broadcast Message
**Usage:**
1. Click "ðŸ“¢ Broadcast Message"
2. Send your message text
3. Bot broadcasts to all users
4. Shows success/fail statistics

**Example:**
```
Admin: [Clicks Broadcast]
Admin: "ðŸŽ‰ New bonus promotion! Check your profile now!"
Bot: "Broadcasting to 150 users..."
Bot: "âœ… Broadcast Complete - Sent: 148, Failed: 2"
```

---

#### ðŸ“· Send Photo
**Usage:**
1. Click "ðŸ“· Send Photo"
2. Send photo with optional caption
3. Broadcasts to all users

**Example:**
```
Admin: [Clicks Send Photo]
Admin: [Sends image with caption "New promotion!"]
Bot: Broadcasts photo to all users
```

---

#### ðŸ“ Send to User
**Usage:**
1. Click "ðŸ“ Send to User"
2. Enter Telegram User ID
3. Send message content
4. Message delivered to that user only

**Example:**
```
Admin: [Clicks Send to User]
Admin: 6942741954
Bot: "âœ… Target user: 6942741954. Now send the message content"
Admin: "Your bonus has been approved!"
Bot: "âœ… Message sent to user 6942741954"
```

---

#### ðŸŽ Set Bonus Text
**Usage:** Set custom bonus text for specific user

**Format:** `USER_ID|Bonus text message`

**Examples:**

**Set Bonus:**
```
Admin: [Clicks Set Bonus Text]
Admin: 6942741954|ðŸŽ‰ Claim your exclusive $100 bonus now!
Bot: "âœ… Bonus text set for user 6942741954:
      ðŸŽ‰ Claim your exclusive $100 bonus now!"
```

**Remove Bonus:**
```
Admin: 6942741954|REMOVE
Bot: "âœ… Bonus text removed for user 6942741954"
```

**User Experience:**
- **With Bonus Text:**
  - Custom text displayed in profile
  - "ðŸ’° Claim My Bonus Now" button appears
  
- **Without Bonus Text:**
  - Purple progress bar animates
  - "Your bonus is being prepared..."
  - No claim button (waiting for admin)

---

#### ðŸ”„ Refresh Stats
**Purpose:** Manually update statistics

**Action:**
- Recalculates all user counts
- Updates verified/pending/total numbers
- Refreshes timestamp

---

### `/cancel`
**Description:** Cancel current admin operation

**Use When:**
- In broadcast mode â†’ Cancels broadcast
- Setting bonus text â†’ Cancels operation
- Sending to user â†’ Cancels operation

---

## ðŸ“‹ Admin Action Examples

### Scenario 1: Approve New User
```
User: [Clicks "ðŸ” Start Verification"]
User: [Completes bcgame67.com login]

Admin: /admin
Admin: [Clicks "â³ Pending Verifications"]
Admin: [Sees new user in list]
Admin: [Clicks "âœ… Verify Username"]

Result:
âœ… User receives approval message
âœ… User gets profile button
âœ… Can claim bonuses
```

---

### Scenario 2: Reject with Error
```
User: [Tries verification but wrong info]

Admin: /admin
Admin: [Clicks "â³ Pending Verifications"]
Admin: [Clicks "âŒ Error" next to user]
Admin: [Selects "Incorrect Email"]

Result:
âŒ User receives "Incorrect email provided"
âŒ User can try again
```

---

### Scenario 3: Set Custom Bonus
```
VIP User: [Completed verification]

Admin: /admin
Admin: [Clicks "ðŸŽ Set Bonus Text"]
Admin: 6942741954|ðŸŽ VIP Exclusive: $200 Bonus!

User: [Opens profile]
Result:
âœ… Sees "ðŸŽ VIP Exclusive: $200 Bonus!"
âœ… Claim button visible
```

---

### Scenario 4: Broadcast Announcement
```
Admin: /admin
Admin: [Clicks "ðŸ“¢ Broadcast Message"]
Admin: "ðŸŽŠ Weekend Special! All bonuses increased by 50%!"

Result:
âœ… All 150 users receive message
âœ… Admin sees: "Sent: 148, Failed: 2"
```

---

### Scenario 5: Personal Message
```
Admin: /admin
Admin: [Clicks "ðŸ“ Send to User"]
Admin: 6942741954
Admin: "Your special bonus has been activated!"

Result:
âœ… Only user 6942741954 receives message
âœ… Private, one-on-one communication
```

---

## ðŸŽ¯ Command Tips

### For Users:
- Always start with `/start` first time
- Use `/profile` to check bonus status quickly
- Contact support if verification fails

### For Admins:
- Check "Pending Verifications" regularly
- Set bonus text for verified VIPs first
- Use broadcast for general announcements
- Use "Send to User" for personal messages
- Refresh stats weekly to keep data current

---

## ðŸš¨ Important Notes

### Verification Process:
1. User clicks "ðŸ” Start Verification"
2. Opens bcgame67.com (Telegram mini-app)
3. User completes login/2FA
4. Admin reviews in pending list
5. Admin approves or sends error
6. User receives notification

### Bonus Text System:
- **Set:** User sees text + claim button
- **Not Set:** User sees progress bar
- **Removed:** Reverts to progress bar
- Updates immediately when changed

### Broadcast Rules:
- Sends to ALL registered users
- Cannot filter by status
- Shows fail count if users blocked bot
- Max ~30 messages per second (Telegram limit)

---

## ðŸ”‘ Quick Reference

| Command | Who | Purpose |
|---------|-----|---------|
| `/start` | User | Register or view profile |
| `/profile` | User | Detailed profile view |
| `/help` | User | Show help |
| `/admin` | Admin | Admin panel |
| `/cancel` | Admin | Cancel operation |

| Admin Action | Format | Example |
|--------------|--------|---------|
| Verify User | Click button | âœ… Verify Username |
| Send Error | Click â†’ Select | âŒ Error â†’ Incorrect Email |
| Set Bonus | USER_ID\|Text | 123\|Claim $50! |
| Remove Bonus | USER_ID\|REMOVE | 123\|REMOVE |
| Broadcast | Send text | ðŸŽ‰ New promotion! |
| Send to User | ID then text | 123 then message |

---

**Need more help?**
- See [QUICK_START.md](QUICK_START.md) for setup
- See [WORKFLOW_DOCUMENTATION.md](WORKFLOW_DOCUMENTATION.md) for details
- Check [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md) for what's new

**Ready to manage your bot! ðŸš€**
