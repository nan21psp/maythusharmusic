import os
import asyncio
import logging
from typing import Dict, List, Optional
from pyrogram import Client
from pyrogram.types import User
from motor.motor_asyncio import AsyncIOMotorCollection

from config import CLONE_SESSIONS, API_ID, API_HASH, BOT_TOKEN

logger = logging.getLogger(__name__)

class CloneManager:
    def __init__(self, db: AsyncIOMotorCollection = None):
        self.db = db
        self.clients: Dict[str, Client] = {}
        self.active_clones: Dict[str, Dict] = {}
        
    async def create_clone_session(self, session_name: str, bot_token: str) -> Optional[Dict]:
        """Create a new bot session from bot token"""
        try:
            # Create bot client
            client = Client(
                name=session_name,
                api_id=API_ID,
                api_hash=API_HASH,
                bot_token=bot_token,
                in_memory=False
            )
            
            await client.start()
            bot_info = await client.get_me()
            
            session_data = {
                "session_name": session_name,
                "bot_token": bot_token,
                "bot_username": bot_info.username,
                "bot_id": bot_info.id,
                "is_bot": True,
                "created_at": asyncio.get_event_loop().time()
            }
            
            # Store in memory
            self.clients[session_name] = client
            self.active_clones[session_name] = session_data
            
            # Save to database if available
            if self.db:
                await self.db.update_one(
                    {"session_name": session_name},
                    {"$set": session_data},
                    upsert=True
                )
            
            logger.info(f"Clone session created: {session_name} for @{bot_info.username}")
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to create clone session: {e}")
            return None
    
    async def create_user_session(self, session_name: str) -> Optional[Dict]:
        """Create a new user session (for assistant)"""
        try:
            client = Client(
                name=session_name,
                api_id=API_ID,
                api_hash=API_HASH,
                in_memory=False
            )
            
            await client.start()
            user_info = await client.get_me()
            session_string = await client.export_session_string()
            
            session_data = {
                "session_name": session_name,
                "session_string": session_string,
                "user_id": user_info.id,
                "username": user_info.username,
                "first_name": user_info.first_name,
                "is_bot": False,
                "created_at": asyncio.get_event_loop().time()
            }
            
            self.clients[session_name] = client
            self.active_clones[session_name] = session_data
            
            if self.db:
                await self.db.update_one(
                    {"session_name": session_name},
                    {"$set": session_data},
                    upsert=True
                )
            
            logger.info(f"User session created: {session_name} for @{user_info.username}")
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to create user session: {e}")
            return None
    
    async def stop_clone(self, session_name: str) -> bool:
        """Stop a clone session"""
        try:
            if session_name in self.clients:
                await self.clients[session_name].stop()
                del self.clients[session_name]
            
            if session_name in self.active_clones:
                del self.active_clones[session_name]
            
            if self.db:
                await self.db.delete_one({"session_name": session_name})
            
            logger.info(f"Clone session stopped: {session_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop clone session: {e}")
            return False
    
    async def get_clone_info(self, session_name: str) -> Optional[Dict]:
        """Get information about a clone session"""
        return self.active_clones.get(session_name)
    
    async def list_clones(self) -> List[Dict]:
        """List all active clone sessions"""
        return list(self.active_clones.values())
    
    async def validate_bot_token(self, bot_token: str) -> tuple[bool, Optional[User]]:
        """Validate if bot token is working"""
        try:
            client = Client(
                name="temp_validation",
                api_id=API_ID,
                api_hash=API_HASH,
                bot_token=bot_token,
                in_memory=True
            )
            
            await client.start()
            bot_info = await client.get_me()
            await client.stop()
            
            return True, bot_info
            
        except Exception as e:
            logger.error(f"Bot token validation failed: {e}")
            return False, None

# Global instance
clone_manager = CloneManager()
