"""
BC.GAME API Module
"""
import aiohttp
import asyncio
from io import BytesIO
from typing import Optional, Dict
import logging
from config import API_CONFIG
from database import Database

logger = logging.getLogger(__name__)

async def fetch_bcgame_user(uid: str) -> Optional[Dict]:
    """Fetch BC.GAME user data with retry logic"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to fetch UID {uid} (attempt {attempt + 1}/{max_retries})")
            
            # Create a new session with SSL verification disabled and increased timeout
            timeout = aiohttp.ClientTimeout(total=30, connect=15, sock_read=15)
            connector = aiohttp.TCPConnector(ssl=False, force_close=True)
            
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    f"https://bcgame.nz/api/game/support/user/info/{uid}/",
                    headers=API_CONFIG['headers'],
                    cookies=API_CONFIG['cookies'],
                    timeout=timeout
                ) as r:
                    logger.info(f"API Response Status: {r.status} for UID: {uid}")
                    
                    if r.status == 200:
                        # Get response text first for debugging
                        response_text = await r.text()
                        logger.info(f"API Raw Response: {response_text[:500]}")  # Log first 500 chars
                        
                        try:
                            import json
                            response_data = json.loads(response_text)
                            logger.info(f"API JSON Keys: {list(response_data.keys()) if isinstance(response_data, dict) else type(response_data)}")
                            
                            # Check if response has 'data' key
                            if 'data' in response_data:
                                data = response_data['data']
                                if data:
                                    logger.info(f"Successfully fetched data for UID: {uid}")
                                    return data
                                else:
                                    logger.warning(f"Empty data for UID: {uid}")
                            else:
                                # Maybe the response IS the data
                                if isinstance(response_data, dict) and any(key in response_data for key in ['userId', 'name', 'level']):
                                    logger.info(f"Response data directly contains user info for UID: {uid}")
                                    return response_data
                                logger.warning(f"Unexpected response structure for UID: {uid}, Keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'not a dict'}")
                        except Exception as json_err:
                            logger.error(f"JSON parse error for UID {uid}: {json_err}")
                    elif r.status == 404:
                        logger.error(f"User not found (404) for UID: {uid}")
                        return None  # Don't retry for 404
                    else:
                        logger.error(f"API returned status {r.status} for UID: {uid}")
                        response_text = await r.text()
                        logger.error(f"Error response: {response_text[:300]}")
                        
        except asyncio.TimeoutError:
            logger.warning(f"Timeout on attempt {attempt + 1} for UID {uid}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)  # Wait before retry
                continue
        except Exception as e:
            logger.error(f"API Error for UID {uid} on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
                continue
    
    logger.error(f"All {max_retries} attempts failed for UID {uid}")
    return None

async def fetch_profile_image(user_id: str) -> Optional[BytesIO]:
    """Fetch profile image from BC.GAME"""
    try:
        session = await Database.http()
        
        # Try primary URL
        async with session.get(
            f"https://img2.distributedresourcestorage.com/avatar/{user_id}/s",
            timeout=aiohttp.ClientTimeout(total=5)
        ) as r:
            if r.status == 200:
                photo = BytesIO(await r.read())
                photo.name = 'profile.jpg'
                logger.info(f"Fetched profile image for user: {user_id}")
                return photo
        
        # Try fallback URL
        async with session.get(
            f"https://bcgame.nz/api/avatar/{user_id}",
            timeout=aiohttp.ClientTimeout(total=5)
        ) as r:
            if r.status == 200:
                photo = BytesIO(await r.read())
                photo.name = 'profile.jpg'
                logger.info(f"Fetched profile image (fallback) for user: {user_id}")
                return photo
                
    except Exception as e:
        logger.error(f"Error fetching profile image: {e}")
    
    return None

def format_money(amount: float) -> str:
    """Format money amount"""
    if amount >= 1000000:
        return f"${amount/1000000:.2f}M"
    elif amount >= 1000:
        return f"${amount/1000:.2f}K"
    return f"${amount:.2f}"

def format_number(num: int) -> str:
    """Format number with commas"""
    return f"{num:,}"
