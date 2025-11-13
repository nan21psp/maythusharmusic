import os
import asyncio
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import BadRequest, Unauthorized

from maythusharmusic import app
from maythusharmusic.core.clone import clone_manager
from config import BANNED_USERS, OWNER_ID, CLONE_ENABLED

# Clone command handler
@app.on_message(filters.command("clone") & filters.private & ~BANNED_USERS)
async def clone_command(client: Client, message: Message):
    if not CLONE_ENABLED:
        return await message.reply_text("❌ Clone system is currently disabled.")
    
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return await message.reply_text("🚫 This command is only for bot owner!")
    
    if len(message.command) < 2:
        # Show clone help
        help_text = """
🤖 **Bot Clone System**

**Usage:**
`/clone <bot_token>` - Clone a bot using token
`/clone session` - Create user session for assistant
`/clone list` - List all active clones
`/clone stop <session_name>` - Stop a clone session

**Example:**
`/clone 123456:ABCdefGhIjKlmNoPQRsTUVwxyZ`

**Get Bot Token:**
1. Go to @BotFather
2. Create new bot with /newbot
3. Copy the bot token
4. Use with /clone command
"""
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🤖 BotFather", url="https://t.me/BotFather")],
            [InlineKeyboardButton("❌ Close", callback_data="close_help")]
        ])
        return await message.reply_text(help_text, reply_markup=buttons)
    
    command = message.command[1]
    
    if command == "list":
        await list_clones(client, message)
    elif command == "session":
        await create_user_session(client, message)
    elif command == "stop" and len(message.command) > 2:
        session_name = message.command[2]
        await stop_clone(client, message, session_name)
    else:
        # Assume it's a bot token
        bot_token = command
        await clone_bot(client, message, bot_token)

async def clone_bot(client: Client, message: Message, bot_token: str):
    """Clone a bot using bot token"""
    try:
        # Validate bot token
        validation_msg = await message.reply_text("🔍 Validating bot token...")
        is_valid, bot_info = await clone_manager.validate_bot_token(bot_token)
        
        if not is_valid:
            await validation_msg.edit_text("❌ Invalid bot token! Please check and try again.")
            return
        
        await validation_msg.edit_text(f"✅ Valid bot token for @{bot_info.username}\n\nCreating clone session...")
        
        # Create clone session
        session_name = f"bot_{bot_info.username}_{int(asyncio.get_event_loop().time())}"
        session_data = await clone_manager.create_clone_session(session_name, bot_token)
        
        if not session_data:
            await validation_msg.edit_text("❌ Failed to create clone session!")
            return
        
        # Success message
        success_text = f"""
✅ **Bot Clone Created Successfully!**

**🤖 Bot Info:**
├─ Name: {bot_info.first_name}
├─ Username: @{bot_info.username}
├─ ID: `{bot_info.id}`
└─ Session: `{session_name}`

**📋 Available Commands:**
├─ /play - Play music in groups
├─ /skip - Skip current song
├─ /pause - Pause playback
└─ /queue - Show song queue

**🔗 Add to Groups:**
Add @{bot_info.username} to your groups and use /play command!
"""
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{bot_info.username}?startgroup=true")],
            [InlineKeyboardButton("🎵 Test Play", url=f"https://t.me/{bot_info.username}")],
            [InlineKeyboardButton("🗑 Delete Clone", callback_data=f"delete_clone:{session_name}")]
        ])
        
        await validation_msg.edit_text(success_text, reply_markup=buttons)
        
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

async def create_user_session(client: Client, message: Message):
    """Create user session for assistant"""
    try:
        msg = await message.reply_text("🔄 Creating user session...")
        
        session_name = f"user_session_{int(asyncio.get_event_loop().time())}"
        session_data = await clone_manager.create_user_session(session_name)
        
        if not session_data:
            await msg.edit_text("❌ Failed to create user session!")
            return
        
        session_text = f"""
✅ **User Session Created**

**Session Name:** `{session_data['session_name']}`
**User ID:** `{session_data['user_id']}`
**Username:** @{session_data['username']}
**First Name:** {session_data['first_name']}

**Session String:**
```{session_data['session_string']}```
"""
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Copy Session", callback_data=f"copy_session:{session_data['session_string']}")],
            [InlineKeyboardButton("🗑 Delete", callback_data=f"delete_session:{session_name}")]
        ])
        
        await msg.edit_text(session_text, reply_markup=buttons)
        
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

async def list_clones(client: Client, message: Message):
    """List all active clones"""
    try:
        clones = await clone_manager.list_clones()
        
        if not clones:
            return await message.reply_text("📭 No active clone sessions found.")
        
        clone_list = "🤖 **Active Clone Sessions:**\n\n"
        
        for i, clone in enumerate(clones, 1):
            if clone['is_bot']:
                clone_list += f"{i}. **Bot:** @{clone['bot_username']}\n"
                clone_list += f"   ├─ ID: `{clone['bot_id']}`\n"
                clone_list += f"   ├─ Session: `{clone['session_name']}`\n"
                clone_list += f"   └─ Type: Bot Account\n\n"
            else:
                clone_list += f"{i}. **User:** {clone['first_name']}\n"
                clone_list += f"   ├─ Username: @{clone['username']}\n"
                clone_list += f"   ├─ Session: `{clone['session_name']}`\n"
                clone_list += f"   └─ Type: User Account\n\n"
        
        await message.reply_text(clone_list)
        
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

async def stop_clone(client: Client, message: Message, session_name: str):
    """Stop a clone session"""
    try:
        clone_info = await clone_manager.get_clone_info(session_name)
        if not clone_info:
            return await message.reply_text("❌ Clone session not found!")
        
        success = await clone_manager.stop_clone(session_name)
        if success:
            await message.reply_text(f"✅ Clone session `{session_name}` stopped successfully!")
        else:
            await message.reply_text("❌ Failed to stop clone session!")
            
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

# Callback handlers
@app.on_callback_query(filters.regex("delete_clone:"))
async def delete_clone_cb(client, callback_query):
    session_name = callback_query.data.split(":")[1]
    user_id = callback_query.from_user.id
    
    if user_id != OWNER_ID:
        return await callback_query.answer("Only owner can delete clones!", show_alert=True)
    
    success = await clone_manager.stop_clone(session_name)
    if success:
        await callback_query.answer("Clone deleted!", show_alert=True)
        await callback_query.message.edit_text("✅ Clone session deleted successfully!")
    else:
        await callback_query.answer("Failed to delete clone!", show_alert=True)

@app.on_callback_query(filters.regex("copy_session:"))
async def copy_session_cb(client, callback_query):
    session_string = callback_query.data.split(":")[1]
    await callback_query.answer("Session string copied to clipboard!", show_alert=True)
    await callback_query.message.reply_text(f"Session String:\n`{session_string}`")

@app.on_callback_query(filters.regex("delete_session:"))
async def delete_session_cb(client, callback_query):
    session_name = callback_query.data.split(":")[1]
    user_id = callback_query.from_user.id
    
    if user_id != OWNER_ID:
        return await callback_query.answer("Only owner can delete sessions!", show_alert=True)
    
    success = await clone_manager.stop_clone(session_name)
    if success:
        await callback_query.answer("Session deleted!", show_alert=True)
        await callback_query.message.delete()
    else:
        await callback_query.answer("Failed to delete session!", show_alert=True)

@app.on_callback_query(filters.regex("close_help"))
async def close_help_cb(client, callback_query):
    await callback_query.message.delete()
