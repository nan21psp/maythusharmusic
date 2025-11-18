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
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text("<b>အသုံးပြုပုံ:</b>\n/play [သီချင်းအမည် (သို့) YouTube Link]")

    try:
        language = await get_lang(message.chat.id)
        _ = get_string(language)
    except:
        _ = get_string("en")

    mystic = await message.reply_text("🔍 <b>ရှာဖွေနေသည်...</b>")

    # ၁။ Assistant ကို Group ထဲ ရှိမရှိ စစ်ဆေးခြင်း၊ မရှိရင် ထည့်ခြင်း
    try:
        userbot = await get_assistant(message.chat.id)
        userbot_me = await userbot.get_me()
        
        try:
            # Assistant Group ထဲမှာ ရှိမရှိ စစ်တယ်
            await client.get_chat_member(message.chat.id, userbot_me.id)
        except UserNotParticipant:
            # မရှိရင် Invite Link နဲ့ ဆွဲထည့်မယ်
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
                    f"သီချင်းဖွင့်ရန်အတွက် <b>{client.me.first_name}</b> (Clone Bot) ကို <b>Admin</b> ပေးထားရန် လိုအပ်ပါသည်။\n\n"
                    f"သို့မဟုတ် Assistant အကောင့် <b>@{userbot_me.username}</b> ကို Group ထဲ လူကိုယ်တိုင် ထည့်ပေးပါ။"
                )
            except Exception as e:
                return await mystic.edit_text(f"Assistant Join Error: {e}")
    except Exception as e:
        print(f"Assistant Check Error: {e}")

    # ၂။ သီချင်းရှာဖွေခြင်း
    try:
        if message.reply_to_message:
            # (File Reply Logic ကို လိုအပ်ရင် နောက်မှထည့်နိုင်သည်)
            return await mystic.edit_text("သီချင်းအမည်ဖြင့် ရှာပေးပါ။")
        
        query = message.text.split(None, 1)[1]
        
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
