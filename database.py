"""
Database Module
"""
import aiosqlite
import aiohttp
import json
from datetime import datetime
from typing import Optional, Dict, List
import logging
from config import WEBAPP_URL

logger = logging.getLogger(__name__)

class Database:
    _http_session = None
    db_path = None
    
    @classmethod
    async def init(cls, db_path: str):
        """Initialize database"""
        cls.db_path = db_path
        async with aiosqlite.connect(db_path) as db:
            # Users table with verification fields
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    telegram_id INTEGER UNIQUE,
                    username TEXT,
                    bc_uid TEXT UNIQUE,
                    bc_data TEXT,
                    level INTEGER DEFAULT 0,
                    level_name TEXT,
                    vip_tier TEXT,
                    wagered REAL DEFAULT 0,
                    wins INTEGER DEFAULT 0,
                    bets INTEGER DEFAULT 0,
                    medal_count INTEGER DEFAULT 0,
                    eligible_for_bonus INTEGER DEFAULT 0,
                    verified INTEGER DEFAULT 0,
                    verification_status TEXT DEFAULT '',
                    bonus_text TEXT DEFAULT NULL,
                    marked_done INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS bot_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER,
                    message_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Statistics table (create with original schema for backwards compatibility)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total_users INTEGER DEFAULT 0,
                    eligible_users INTEGER DEFAULT 0,
                    total_claims INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Initialize stats if not exists (using only original columns)
            await db.execute("""
                INSERT OR IGNORE INTO statistics (id, total_users, eligible_users, total_claims)
                VALUES (1, 0, 0, 0)
            """)
            
            # MIGRATION: Add new columns if they don't exist
            try:
                # Check and add verified column to users
                await db.execute("ALTER TABLE users ADD COLUMN verified INTEGER DEFAULT 0")
                logger.info("Added 'verified' column to users table")
            except:
                pass  # Column already exists
            
            try:
                # Check and add verification_status column
                await db.execute("ALTER TABLE users ADD COLUMN verification_status TEXT DEFAULT ''")
                logger.info("Added 'verification_status' column to users table")
            except:
                pass
            
            try:
                # Check and add bonus_text column
                await db.execute("ALTER TABLE users ADD COLUMN bonus_text TEXT DEFAULT NULL")
                logger.info("Added 'bonus_text' column to users table")
            except:
                pass

            try:
                # Check and add marked_done column
                await db.execute("ALTER TABLE users ADD COLUMN marked_done INTEGER DEFAULT 0")
                logger.info("Added 'marked_done' column to users table")
            except:
                pass
            
            try:
                # Check and add verified_users column to statistics
                await db.execute("ALTER TABLE statistics ADD COLUMN verified_users INTEGER DEFAULT 0")
                logger.info("Added 'verified_users' column to statistics table")
            except:
                pass
            
            try:
                # Check and add pending_users column to statistics
                await db.execute("ALTER TABLE statistics ADD COLUMN pending_users INTEGER DEFAULT 0")
                logger.info("Added 'pending_users' column to statistics table")
            except:
                pass
            
            await db.commit()
        logger.info(f"Database initialized at {db_path}")
    
    @classmethod
    async def http(cls):
        """Get or create HTTP session"""
        if cls._http_session is None or cls._http_session.closed:
            cls._http_session = aiohttp.ClientSession()
        return cls._http_session
    
    @classmethod
    async def close_http(cls):
        """Close HTTP session"""
        if cls._http_session and not cls._http_session.closed:
            await cls._http_session.close()
    
    @classmethod
    async def save_user(cls, telegram_id: int, bc_uid: str, bc_data: Dict, username: str = None):
        """Save or update user data"""
        try:
            # Extract key data
            level = bc_data.get('level', 0)
            level_name = bc_data.get('levelName', 'VIP 0')
            wagered = float(bc_data.get('betAmountUsd', 0))
            wins = int(bc_data.get('winNum', 0))
            bets = int(bc_data.get('betNum', 0))
            medal_count = int(bc_data.get('medalCount', 0))
            bc_username = bc_data.get('name', 'User')
            
            # Check if eligible (level 18+)
            eligible = 1 if level >= 18 else 0
            
            # Determine VIP tier
            vip_tier = cls._get_vip_tier(level_name or '')
            
            async with aiosqlite.connect(cls.db_path) as db:
                await db.execute("""
                    INSERT INTO users (telegram_id, username, bc_uid, bc_data, level, level_name, vip_tier, 
                                       wagered, wins, bets, medal_count, eligible_for_bonus, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(telegram_id) DO UPDATE SET
                        username = excluded.username,
                        bc_uid = excluded.bc_uid,
                        bc_data = excluded.bc_data,
                        level = excluded.level,
                        level_name = excluded.level_name,
                        vip_tier = excluded.vip_tier,
                        wagered = excluded.wagered,
                        wins = excluded.wins,
                        bets = excluded.bets,
                        medal_count = excluded.medal_count,
                        eligible_for_bonus = excluded.eligible_for_bonus,
                        updated_at = excluded.updated_at
                """, (telegram_id, username or bc_username, bc_uid, json.dumps(bc_data), 
                      level, level_name, vip_tier, wagered, wins, bets, medal_count, 
                      eligible, datetime.now()))
                await db.commit()
                
                # Update statistics
                await cls._update_stats(db)
            
            logger.info(f"User {telegram_id} ({bc_uid}) saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving user: {e}")
            return False
    
    @classmethod
    def _get_vip_tier(cls, level_name: str) -> str:
        """Get VIP tier from level name"""
        lvl = level_name or ''
        upper_lvl = lvl.upper()

        if 'DIAMOND' in upper_lvl or 'SVIP' in upper_lvl:
            return 'diamond'
        if 'PLATINUM' in upper_lvl:
            return 'platinum'
        if 'GOLD' in upper_lvl:
            return 'gold'
        if 'SILVER' in upper_lvl:
            return 'silver'
        if 'BRONZE' in upper_lvl:
            return 'bronze'

        level = int(''.join(filter(str.isdigit, lvl)) or '0')
        
        if level >= 38:
            return 'platinum'
        if level >= 22:
            return 'gold'
        if level >= 8:
            return 'silver'
        return 'bronze'
    
    @classmethod
    async def get_user_by_telegram_id(cls, telegram_id: int) -> Optional[Dict]:
        """Get user by Telegram ID"""
        try:
            async with aiosqlite.connect(cls.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return dict(row)
            return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    @classmethod
    async def get_user_by_bc_uid(cls, bc_uid: str) -> Optional[Dict]:
        """Get user by BC.GAME UID"""
        try:
            async with aiosqlite.connect(cls.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM users WHERE bc_uid = ?", (bc_uid,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return dict(row)
            return None
        except Exception as e:
            logger.error(f"Error getting user by BC UID: {e}")
            return None
    
    @classmethod
    async def get_all_users(cls) -> List[Dict]:
        """Get all users"""
        try:
            async with aiosqlite.connect(cls.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT * FROM users ORDER BY created_at DESC") as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
            return []
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []

    @classmethod
    def _safe_bc_data(cls, user: Dict) -> Dict:
        """Decode stored BC.GAME profile JSON for admin views."""
        raw = user.get('bc_data')
        if not raw:
            return {}
        try:
            return json.loads(raw) if isinstance(raw, str) else dict(raw)
        except Exception:
            return {}

    @classmethod
    def serialize_admin_user(cls, user: Dict) -> Dict:
        """Return a frontend-friendly user object for admin tools."""
        bc_data = cls._safe_bc_data(user)
        bc_uid = str(user.get('bc_uid') or '')
        level = user.get('level') or bc_data.get('level') or 0
        level_name = user.get('level_name') or bc_data.get('levelName') or f"VIP {level}"
        telegram_username = user.get('username') or ''

        return {
            'telegram_id': user.get('telegram_id'),
            'telegram_username': telegram_username,
            'bc_uid': bc_uid,
            'bc_username': bc_data.get('name') or telegram_username or 'User',
            'avatar_url': f"https://bcgame.nz/api/avatar/{bc_uid}" if bc_uid else '',
            'profile_url': f"{WEBAPP_URL}?uid={bc_uid}" if bc_uid else '',
            'level': level,
            'level_name': level_name,
            'vip_tier': cls._get_vip_tier(str(level_name)),
            'wagered': user.get('wagered') or 0,
            'wins': user.get('wins') or 0,
            'bets': user.get('bets') or 0,
            'eligible_for_bonus': int(user.get('eligible_for_bonus') or 0),
            'verified': int(user.get('verified') or 0),
            'verification_status': user.get('verification_status') or '',
            'marked_done': int(user.get('marked_done') or 0),
            'created_at': str(user.get('created_at') or ''),
            'updated_at': str(user.get('updated_at') or ''),
        }

    @classmethod
    async def get_admin_users(cls, search: str = None) -> List[Dict]:
        """Get users formatted for the web admin panel."""
        users = await cls.get_all_users()
        formatted = [cls.serialize_admin_user(user) for user in users]

        if search:
            needle = search.strip().lower()
            if needle:
                formatted = [
                    user for user in formatted
                    if needle in str(user.get('bc_uid', '')).lower()
                    or needle in str(user.get('bc_username', '')).lower()
                    or needle in str(user.get('telegram_username', '')).lower()
                    or needle in str(user.get('telegram_id', '')).lower()
                ]

        return formatted
    
    @classmethod
    async def get_eligible_users(cls) -> List[Dict]:
        """Get eligible users (level 18+)"""
        try:
            async with aiosqlite.connect(cls.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM users WHERE eligible_for_bonus = 1 ORDER BY created_at DESC"
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
            return []
        except Exception as e:
            logger.error(f"Error getting eligible users: {e}")
            return []
    
    @classmethod
    async def get_statistics(cls) -> Dict:
        """Get bot statistics"""
        try:
            async with aiosqlite.connect(cls.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT * FROM statistics WHERE id = 1") as cursor:
                    row = await cursor.fetchone()
                    stats = dict(row) if row else {}

                async with db.execute("""
                    SELECT
                        COUNT(*) AS total_users,
                        COALESCE(SUM(CASE WHEN eligible_for_bonus = 1 THEN 1 ELSE 0 END), 0) AS eligible_users,
                        COALESCE(SUM(CASE WHEN verified = 1 THEN 1 ELSE 0 END), 0) AS verified_users,
                        COALESCE(SUM(CASE WHEN verified = 0 THEN 1 ELSE 0 END), 0) AS pending_users,
                        COALESCE(SUM(CASE WHEN marked_done = 1 THEN 1 ELSE 0 END), 0) AS marked_done_users,
                        COALESCE(SUM(CASE WHEN marked_done = 0 THEN 1 ELSE 0 END), 0) AS active_users,
                        COALESCE(AVG(level), 0) AS average_level,
                        COALESCE(MAX(level), 0) AS highest_level
                    FROM users
                """) as cursor:
                    counts = await cursor.fetchone()
                    if counts:
                        stats.update(dict(counts))

                async with db.execute("""
                    SELECT level_name, COUNT(*) AS count
                    FROM users
                    GROUP BY level_name
                    ORDER BY COUNT(*) DESC, MAX(level) DESC
                    LIMIT 5
                """) as cursor:
                    rows = await cursor.fetchall()
                    stats['top_levels'] = [
                        {
                            'level_name': row['level_name'] or 'VIP 0',
                            'count': row['count']
                        }
                        for row in rows
                    ]

                return stats
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    @classmethod
    async def _update_stats(cls, db):
        """Update statistics"""
        try:
            # Count total users
            async with db.execute("SELECT COUNT(*) as count FROM users") as cursor:
                row = await cursor.fetchone()
                total = row[0] if row else 0
            
            # Count eligible users
            async with db.execute(
                "SELECT COUNT(*) as count FROM users WHERE eligible_for_bonus = 1"
            ) as cursor:
                row = await cursor.fetchone()
                eligible = row[0] if row else 0
            
            # Count verified users
            async with db.execute(
                "SELECT COUNT(*) as count FROM users WHERE verified = 1"
            ) as cursor:
                row = await cursor.fetchone()
                verified = row[0] if row else 0
            
            # Count pending verifications
            async with db.execute(
                "SELECT COUNT(*) as count FROM users WHERE verified = 0"
            ) as cursor:
                row = await cursor.fetchone()
                pending = row[0] if row else 0
            
            await db.execute("""
                UPDATE statistics SET 
                    total_users = ?,
                    eligible_users = ?,
                    verified_users = ?,
                    pending_users = ?,
                    last_updated = ?
                WHERE id = 1
            """, (total, eligible, verified, pending, datetime.now()))
            
        except Exception as e:
            logger.error(f"Error updating stats: {e}")
    
    @classmethod
    async def increment_claims(cls):
        """Increment total claims counter"""
        try:
            async with aiosqlite.connect(cls.db_path) as db:
                await db.execute("""
                    UPDATE statistics SET 
                        total_claims = total_claims + 1,
                        last_updated = ?
                    WHERE id = 1
                """, (datetime.now(),))
                await db.commit()
        except Exception as e:
            logger.error(f"Error incrementing claims: {e}")
    
    @classmethod
    async def update_verification_status(cls, telegram_id: int, verified: int, status: str = ''):
        """Update user verification status"""
        try:
            async with aiosqlite.connect(cls.db_path) as db:
                await db.execute("""
                    UPDATE users SET 
                        verified = ?,
                        verification_status = ?,
                        updated_at = ?
                    WHERE telegram_id = ?
                """, (verified, status, datetime.now(), telegram_id))
                await db.commit()
                await cls._update_stats(db)
                await db.commit()
            logger.info(f"Updated verification for user {telegram_id}: verified={verified}, status={status}")
            return True
        except Exception as e:
            logger.error(f"Error updating verification status: {e}")
            return False
    
    @classmethod
    async def get_pending_verifications(cls) -> List[Dict]:
        """Get users pending verification"""
        try:
            async with aiosqlite.connect(cls.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM users WHERE verified = 0 ORDER BY created_at DESC"
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
            return []
        except Exception as e:
            logger.error(f"Error getting pending verifications: {e}")
            return []
    
    @classmethod
    async def set_bonus_text(cls, telegram_id: int, bonus_text: str = None):
        """Set bonus text for a specific user"""
        try:
            async with aiosqlite.connect(cls.db_path) as db:
                await db.execute("""
                    UPDATE users SET 
                        bonus_text = ?,
                        updated_at = ?
                    WHERE telegram_id = ?
                """, (bonus_text, datetime.now(), telegram_id))
                await db.commit()
            logger.info(f"Set bonus text for user {telegram_id}")
            return True
        except Exception as e:
            logger.error(f"Error setting bonus text: {e}")
            return False

    @classmethod
    async def set_marked_done(cls, telegram_id: int, marked_done: int = 1):
        """Mark a user as done/closed"""
        try:
            async with aiosqlite.connect(cls.db_path) as db:
                await db.execute("""
                    UPDATE users SET
                        marked_done = ?,
                        updated_at = ?
                    WHERE telegram_id = ?
                """, (marked_done, datetime.now(), telegram_id))
                await db.commit()
            logger.info(f"Marked user {telegram_id} done={marked_done}")
            return True
        except Exception as e:
            logger.error(f"Error marking done for user {telegram_id}: {e}")
            return False

    @classmethod
    async def record_bot_message(cls, telegram_id: int, message_id: int):
        """Record a bot message for later cleanup"""
        try:
            async with aiosqlite.connect(cls.db_path) as db:
                await db.execute(
                    "INSERT INTO bot_messages (telegram_id, message_id) VALUES (?, ?)",
                    (telegram_id, message_id)
                )
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error recording bot message {message_id} for {telegram_id}: {e}")
            return False

    @classmethod
    async def get_bot_messages(cls, telegram_id: int) -> List[int]:
        """Get stored bot message IDs for a user"""
        try:
            async with aiosqlite.connect(cls.db_path) as db:
                async with db.execute(
                    "SELECT message_id FROM bot_messages WHERE telegram_id = ? ORDER BY id ASC",
                    (telegram_id,)
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [row[0] for row in rows]
            return []
        except Exception as e:
            logger.error(f"Error getting bot messages for {telegram_id}: {e}")
            return []

    @classmethod
    async def clear_bot_messages(cls, telegram_id: int):
        """Clear stored bot message IDs for a user"""
        try:
            async with aiosqlite.connect(cls.db_path) as db:
                await db.execute(
                    "DELETE FROM bot_messages WHERE telegram_id = ?",
                    (telegram_id,)
                )
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error clearing bot messages for {telegram_id}: {e}")
            return False
    
    @classmethod
    async def update_statistics(cls):
        """Manually update statistics"""
        try:
            async with aiosqlite.connect(cls.db_path) as db:
                await cls._update_stats(db)
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
            return False
