import logging
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import BadRequest

from clone_bot import app, clone_bot
from config import MUSIC_ENABLED

logger = logging.getLogger(__name__)

@app.on_message(filters.command("play") & filters.group)
async def play_music(client, message: Message):
    """Play music command"""
    if not MUSIC_ENABLED:
        return await message.reply_text("❌ Music feature is currently disabled.")
    
    if len(message.command) < 2:
        return await message.reply_text("""
🎵 **Usage:** /play [song name or URL]

**Examples:**
• `/play faded`
• `/play https://youtu.be/60ItHLz5WEA`
• `/play spotify:track:123456`

**Supported:**
YouTube, Spotify, Apple Music, SoundCloud
""")
    
    query = ' '.join(message.command[1:])
    
    # Send processing message
    processing_msg = await message.reply_text("🔍 **Searching...**")
    
    try:
        # Call main bot API
        api_data = {
            "clone_bot_id": clone_bot.bot_info.id,
            "clone_bot_username": clone_bot.bot_info.username,
            "chat_id": message.chat.id,
            "chat_title": message.chat.title,
            "user_id": message.from_user.id,
            "user_name": message.from_user.first_name,
            "query": query,
            "message_id": message.id
        }
        
        response = await clone_bot.call_main_bot_api("music/play", api_data)
        
        if response.get("success"):
            title = response.get("title", "Unknown")
            duration = response.get("duration", "Unknown")
            thumb = response.get("thumbnail", "")
            
            success_text = f"""
🎵 **Now Playing**

**Title:** {title}
**Duration:** {duration}
**Requested by:** {message.from_user.mention}

**Controls:**
⏸️ /pause - ⏭️ /skip - ⏹️ /stop
"""
            buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⏸️ Pause", callback_data="pause_music"),
                    InlineKeyboardButton("⏭️ Skip", callback_data="skip_music")
                ],
                [
                    InlineKeyboardButton("📋 Queue", callback_data="show_queue"),
                    InlineKeyboardButton("🎛️ Controls", callback_data="music_controls")
                ]
            ])
            
            if thumb:
                await processing_msg.delete()
                await
