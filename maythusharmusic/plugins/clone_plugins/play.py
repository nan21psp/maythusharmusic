# maythusharmusic/plugins/clone_plugins/play.py

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import ChatAdminRequired, UserNotParticipant
from maythusharmusic import YouTube
from maythusharmusic.utils.stream.stream import stream
from maythusharmusic.utils.database import get_assistant, get_lang
from strings import get_string

@Client.on_message(filters.command(["play", "vplay"]) & filters.group)
async def play_clone(client: Client, message: Message):
    # Language String ရယူခြင်း
    try:
        language = await get_lang(message.chat.id)
        _ = get_string(language)
    except:
        _ = get_string("en")

    # URL သို့မဟုတ် Query ရှာဖွေခြင်း (YouTube.py ကို အသုံးပြုခြင်း)
    url = await YouTube.url(message)
    
    if not url and len(message.command) < 2:
        return await message.reply_text("<b>အသုံးပြုပုံ:</b>\n/play [သီချင်းအမည် (သို့) YouTube Link]\n(သို့မဟုတ်) Link ပါသောစာကို Reply ပြန်၍ /play နှိပ်ပါ။")

    mystic = await message.reply_text("🔍 <b>ရှာဖွေနေသည်...</b>")

    # ၁။ Assistant ကို Group ထဲ ရှိမရှိ စစ်ဆေးခြင်း
    try:
        userbot = await get_assistant(message.chat.id)
        userbot_me = await userbot.get_me()
        
        try:
            await client.get_chat_member(message.chat.id, userbot_me.id)
        except UserNotParticipant:
            try:
                invite_link = await client.export_chat_invite_link(message.chat.id)
                if "+" in invite_link:
                    link_hash = invite_link.split("+")[1]
                    await userbot.join_chat(f"https://t.me/joinchat/{link_hash}")
                else:
                    await userbot.join_chat(invite_link)
            except ChatAdminRequired:
                return await mystic.edit_text(
                    f"🚨 <b>Assistant ဝင်မရပါ!</b>\n\n"
                    f"သီချင်းဖွင့်ရန် <b>{client.me.first_name}</b> ကို <b>Admin</b> ပေးထားရန် လိုအပ်ပါသည်။"
                )
            except Exception as e:
                return await mystic.edit_text(f"Assistant Join Error: {e}")
    except Exception as e:
        print(f"Assistant Check Error: {e}")

    # ၂။ YouTube Data ရယူခြင်း (YouTube.py နှင့် ချိတ်ဆက်ခြင်း)
    try:
        # URL ရှိရင် URL နဲ့ရှာမယ်၊ မရှိရင် Command နောက်က စာသားနဲ့ ရှာမယ်
        query = url if url else message.text.split(None, 1)[1]
        
        try:
            # YouTube.py မှ details function ကို ခေါ်သုံးခြင်း
            result = await YouTube.details(query)
            
            if not result:
                return await mystic.edit_text("❌ မတွေ့ရှိပါ။")
            
            # YouTube.py မှ ပြန်လာသော Data များကို ဖြည်ခြင်း
            (title, duration_min, duration_sec, thumbnail, vidid) = result
            
            details = {
                "title": title,
                "link": f"https://www.youtube.com/watch?v={vidid}",
                "vidid": vidid,
                "duration_min": duration_min,
                "thumb": thumbnail
            }
            
        except Exception as e:
            return await mystic.edit_text(f"YouTube Search Error: {e}")

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
