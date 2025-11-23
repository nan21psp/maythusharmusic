import asyncio
from pyrogram import filters
from pyrogram.enums import ChatMembersFilter
from pyrogram.types import Message
from maythusharmusic import app
from config import BANNED_USERS

@app.on_message(filters.command(["tagadmin", "admins", "adminlist"]) & filters.group & ~BANNED_USERS)
async def tag_admins_only(client, message: Message):
    chat_id = message.chat.id
    
    # Reply ပြန်ထားရင် အဲ့ဒီစာကို Reply ပြန်ပြီး Tag မယ်
    replied = message.reply_to_message
    text = message.text.split(None, 1)[1] if len(message.command) > 1 else ""
    
    admin_mentions = []
    
    # Admin များကို ရှာဖွေခြင်း
    async for member in app.get_chat_members(chat_id, filter=ChatMembersFilter.ADMINISTRATORS):
        if not member.user.is_bot and not member.user.is_deleted:
            admin_mentions.append(member.user.mention)
            
    if not admin_mentions:
        return await message.reply_text("❌ <b>Admin မတွေ့ရှိပါ။</b>")

    # စာသား ပြင်ဆင်ခြင်း
    if text:
        msg_text = f"**Admin Call :** {text}\n\n"
    else:
        msg_text = f"**Admin Mention :**\n\n"

    # Admin တွေကို တစ်ကြောင်းစီ Mention ခေါ်မည်
    for admin in admin_mentions:
        msg_text += f"{admin}\n"

    # ပို့ဆောင်ခြင်း
    try:
        if replied:
            await replied.reply_text(msg_text)
        else:
            await app.send_message(chat_id, msg_text)
    except Exception as e:
        print(f"Tag Admin Error: {e}")
