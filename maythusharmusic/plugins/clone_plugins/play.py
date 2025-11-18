# maythusharmusic/plugins/clone_plugins/play.py

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from maythusharmusic import YouTube, userbot
from maythusharmusic.utils.stream.stream import stream
from maythusharmusic.utils.database import get_assistant, is_active_chat
import config

@Client.on_message(filters.command(["play", "vplay"]) & filters.group)
async def play_clone(client: Client, message: Message):
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text("<b>အသုံးပြုပုံ:</b>\n/play [သီချင်းအမည် (သို့) YouTube Link]")

    mystic = await message.reply_text("🔍 <b>ရှာဖွေနေသည်...</b>")

    # ၁။ Assistant ကို Group ထဲ အရင်ထည့်မည်
    try:
        userbot_client = await get_assistant(message.chat.id)
        try:
            # Group Link နဲ့ ဝင်ခိုင်းခြင်း
            invite_link = await client.export_chat_invite_link(message.chat.id)
            if "+" in invite_link:
                link_hash = invite_link.split("+")[1]
                await userbot_client.join_chat(f"https://t.me/joinchat/{link_hash}")
            else:
                await userbot_client.join_chat(invite_link)
        except Exception:
            # Link နဲ့မရရင် Username နဲ့စမ်းမယ်၊ ဒါမှမရရင် Admin ပေးဖို့ ပြောမယ်
            pass
    except Exception as e:
        print(f"Assistant Join Error: {e}")

    # ၂။ သီချင်းရှာဖွေခြင်း
    try:
        if message.reply_to_message:
            # File ကို Reply ပြန်တာဆိုရင် (လောလောဆယ် Search ကိုပဲ ဦးစားပေးပါမယ်)
            return await mystic.edit_text("သီချင်းအမည်ဖြင့် ရှာပေးပါ။")
        
        query = message.text.split(None, 1)[1]
        
        # YouTube မှာ ရှာမယ်
        try:
            result = await YouTube.details(query, True)
            if not result:
                return await mystic.edit_text("❌ မတွေ့ရှိပါ။")
            
            (title, duration_min, duration_sec, thumbnail, vidid) = result
            
            details = {
                "title": title,
                "link": f"https://www.youtube.com/watch?v={vidid}",
                "vidid": vidid,
                "duration_min": duration_min,
                "thumb": thumbnail
            }
            
        except Exception as e:
            return await mystic.edit_text(f"YouTube Error: {e}")

        # ၃။ Stream စမယ်
        await stream(
            _,
            mystic,
            message.from_user.id,
            details,
            message.chat.id,
            message.from_user.first_name,
            message.chat.id,
            video=True if "vplay" in message.command[0] else False,
            streamtype="youtube",
            spotify=False,
            forceplay=False,
        )
        
    except Exception as e:
        await mystic.edit_text(f"🚫 Error: {e}")
