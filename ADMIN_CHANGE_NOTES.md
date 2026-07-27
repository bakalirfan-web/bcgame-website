# Admin Change Notes

## Current Admin Update

This update focused on making the admin tools easier to use without blocking the bot.

### Telegram Admin Menu

- `Send Message` keeps the existing 3-step compose flow: image, text, buttons.
- `Broadcast` uses the same compose flow, then schedules delivery in a background task.
- Broadcast progress edits one Telegram status message after every 5 successful sends.
- The progress update includes total users, sent count, failed count, timestamp, and the latest 5 users reached.
- `Mark Done` now asks only for a BC.GAME UID.
- After UID entry, the bot marks the user done, deletes tracked bot messages, and sends a congratulations banner button.
- `Statistics` now shows total, eligible, verified, pending, marked done, active, claims, average level, highest level, and top level groups.
- `Users` shows a compact Telegram-side list; the full scroll list lives in the web panel.

### Done User Behavior

- Done users use this URL instead of the old `bcgame67.com` claim URL:
  `https://bcgame.st/assets/banner-BUqEgMu6.png`
- This applies when a done user returns with `/start`, opens `/profile`, updates their profile, or receives verification success.

### Web Admin Panel

- `admin_web.py` serves a local admin API and static UI.
- `admin_panel.html` shows a scrollable users table with:
  BC.GAME avatar, BC username, Telegram username, Telegram ID, BC UID, level, verification status, and done status.
- Every user row now has a `Profile` action that opens that user's BC.GAME profile web view by UID.
- Tier filters sit under the top stats: All, Beginner, Bronze, Silver, Gold, Platinum, Diamond.
- Clicking a tier filter updates the users table to show only users from that level group.
- Send, Mark Done, and Broadcast buttons show an in-button progress bar while the request is running.
- Successful sends and mark-done actions show a 3-second toast.
- The web panel can:
  send a direct text message by BC UID,
  start a text broadcast,
  mark a user done,
  view live statistics.
- `python bot.py` starts the web panel automatically.
- `python admin_web.py` starts the panel by itself.
- Default local URL: `http://127.0.0.1:8080/`
- Access key is `ADMIN_PANEL_KEY` in `config.py`.

### Files Touched

- `config.py`: added done banner, web admin, and broadcast batch settings.
- `database.py`: added live dashboard statistics and admin user serialization.
- `admin.py`: improved admin menu, background broadcast, mark-done flow, and richer stats.
- `bot.py`: done-user claim buttons now route to the banner URL; bot starts/stops the web admin server.
- `admin_web.py`: new local web admin server/API.
- `admin_panel.html`: new local web admin interface.
- `README.md`: updated setup and admin feature documentation.

## Follow-up Update

- The done-user `View Bonus` button now uses Telegram `web_app` mode instead of a normal browser URL.
- The web admin users API now returns `profile_url` for each user.
- Web admin rows include a `Profile` action beside `Send` and `Done`.
- The top dashboard now includes tier filters for level-based user lists.
- Button progress bars and 3-second success toasts were added for send/mark-done workflows.

## Level Name Tier Fix

- Tier filtering now reads the BC.GAME `levelName` field first.
- Examples:
  `Gold I` goes to Gold,
  `Platinum I` goes to Platinum,
  `Bronze I` goes to Bronze,
  `Diamond I` or `SVIP` goes to Diamond.
- Numeric level fallback is still kept only for records that do not include a text tier in `levelName`.

## Live BC.GAME Refresh

- Stale local rows can be corrected from the live BC.GAME API.
- Each web admin row has a `Refresh API` button that fetches the UID again and updates saved level, `levelName`, wager, wins, bets, and tier.
- The web admin toolbar has `Sync API`, which starts a background refresh for all saved users.
- Verified example: UID `12012041` changed from stale `VIP40/platinum` to live `Silver IV/silver`.
