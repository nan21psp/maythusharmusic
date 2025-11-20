from pyrogram import filters
from pyrogram.types import Message
import asyncio
from maythusharmusic import app
from maythusharmusic.misc import SUDOERS
from maythusharmusic.utils.database import autoend_off, autoend_on

class AutoEndManager:
    def __init__(self):
        self.autoend_enabled = True  # Default True - Autoend will work
        self.check_interval = 60  # Check every 60 seconds
        self.min_listeners = 1  # Minimum listeners required
        self.empty_duration = 60  # 3 minutes empty before autoend
        
    async def set_autoend(self, enabled: bool):
        """Set autoend status"""
        self.autoend_enabled = enabled
        if enabled:
            await autoend_on()
        else:
            await autoend_off()
    
    def is_autoend_enabled(self):
        """Check if autoend is enabled - returns True/False"""
        return self.autoend_enabled
    
    async def start_autoend_check(self):
        """Start autoend checking loop"""
        while True:
            if self.autoend_enabled:
                await self._check_empty_chats()
            await asyncio.sleep(self.check_interval)
    
    async def _check_empty_chats(self):
        """Check for empty voice chats and autoend"""
        try:
            # Get all active voice chats
            active_chats = await self._get_active_voice_chats()
            
            for chat_id in active_chats:
                listeners = await self._get_listener_count(chat_id)
                
                if listeners < self.min_listeners:
                    # If no listeners for specified duration, end stream
                    await self._auto_end_stream(chat_id)
                    
        except Exception as e:
            print(f"Autoend check error: {e}")
    
    async def _get_active_voice_chats(self):
        """Get list of active voice chats - implement based on your bot"""
        # This should return list of chat_ids where bot is in voice chat
        active_chats = []
        # Implement your logic here
        return active_chats
    
    async def _get_listener_count(self, chat_id):
        """Get number of listeners in voice chat - implement based on your bot"""
        # This should return number of listeners in the voice chat
        listener_count = 0
        # Implement your logic here
        return listener_count
    
    async def _auto_end_stream(self, chat_id):
        """End stream in specified chat"""
        try:
            # Implement your stream ending logic here
            print(f"Autoending stream in chat {chat_id}")
            # Example: await app.leave_group_call(chat_id)
        except Exception as e:
            print(f"Autoend error in chat {chat_id}: {e}")

# Create global instance
autoend_manager = AutoEndManager()

# Command handler for manual control (optional)
@app.on_message(filters.command("autoend") & SUDOERS)
async def auto_end_control(_, message: Message):
    usage = (
        "**AutoEnd Control**\n\n"
        "**Current Status:** `{status}`\n\n"
        "**Usage:**\n"
        "/autoend true - Enable autoend\n"
        "/autoend false - Disable autoend\n"
        "/autoend status - Check status"
    )
    
    if len(message.command) < 2:
        current_status = autoend_manager.is_autoend_enabled()
        status_text = "True ✅" if current_status else "False ❌"
        return await message.reply_text(usage.format(status=status_text))
    
    command = message.command[1].lower()
    
    if command in ["true", "enable", "on", "1"]:
        await autoend_manager.set_autoend(True)
        await message.reply_text(
            "✅ **AutoEnd Enabled**\n\n"
            "Bot will automatically end streams when no listeners.\n"
            "**Status:** `True`"
        )
        
    elif command in ["false", "disable", "off", "0"]:
        await autoend_manager.set_autoend(False)
        await message.reply_text(
            "❌ **AutoEnd Disabled**\n\n"
            "Bot will NOT autoend streams.\n"
            "**Status:** `False`"
        )
        
    elif command in ["status", "check"]:
        current_status = autoend_manager.is_autoend_enabled()
        status_text = "Enabled ✅" if current_status else "Disabled ❌"
        await message.reply_text(
            f"🔍 **AutoEnd Status**\n\n"
            f"**Current:** `{current_status}`\n"
            f"**Meaning:** {status_text}"
        )
        
    else:
        current_status = autoend_manager.is_autoend_enabled()
        status_text = "True ✅" if current_status else "False ❌"
        await message.reply_text(usage.format(status=status_text))

# Start autoend check when bot starts
@app.on_message(filters.command("startautoend") & SUDOERS)
async def start_autoend(_, message: Message):
    """Start the autoend checking loop"""
    asyncio.create_task(autoend_manager.start_autoend_check())
    await message.reply_text("🔄 AutoEnd checking started!")

# You can also automatically start when bot runs
# Add this in your __main__ or startup code:
"""
# In your main.py or __init__.py
from maythusharmusic.utils.autoend import autoend_manager

async def startup():
    # Start autoend checking
    asyncio.create_task(autoend_manager.start_autoend_check())
"""
