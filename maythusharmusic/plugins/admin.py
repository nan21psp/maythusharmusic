from pyrogram import filters
from pyrogram.types import Message

from clone_bot import app, clone_bot

@app.on_message(filters.command("auth") & filters.group)
async def auth_user(client, message: Message):
    """Add user to authorized list"""
    if not message.from_user:
        return await message.reply_text("❌ User not found.")
    
    try:
        api_data = {
            "clone_bot_id": clone_bot.bot_info.id,
            "chat_id": message.chat.id,
            "target_user_id": message.from_user.id,
            "admin_user_id": message.from_user.id,
            "action": "add"
        }
        
        response = await clone_bot.call_main_bot_api("admin/auth", api_data)
        
        if response.get("success"):
            await message.reply_text("✅ **User authorized!**")
        else:
            await message.reply_text("❌ **Failed to authorize user.**")
            
    except Exception as e:
        await message.reply_text("❌ **Error:** Failed to authorize user.")

@app.on_message(filters.command("settings") & filters.group)
async def bot_settings(client, message: Message):
    """Show bot settings"""
    try:
        api_data = {
            "clone_bot_id": clone_bot.bot_info.id,
            "chat_id": message.chat.id
        }
        
        response = await clone_bot.call_main_bot_api("admin/settings", api_data)
        
        if response.get("success"):
            settings = response.get("settings", {})
            
            settings_text = f"""
⚙️ **{clone_bot.bot_info.first_name} Settings**

**Play Mode:** {settings.get('play_mode', 'Direct')}
**Play Type:** {settings.get('play_type', 'Everyone')}
**Language:** {settings.get('language', 'English')}

**Use /help for more commands**
"""
            await message
