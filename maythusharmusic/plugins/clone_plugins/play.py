# maythusharmusic/plugins/clone_plugins/play.py

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import ChatAdminRequired, UserNotParticipant

import config
from maythusharmusic import YouTube, app
from maythusharmusic.utils.stream.stream import stream
from maythusharmusic.utils.database import get_assistant, get_lang
from strings import get_string

# --- (၁) User တောင်းဆိုထားသော Imports များ ---
from maythusharmusic.utils.inline import (
    botplaylist_markup,
    livestream_markup,
    playlist_markup,
    slider_markup,
    track_markup,
)
# ------------------------------------------

@Client.on_message(filters.command(["play", "vplay"]) & filters.group)
async def play_clone(client: Client, message: Message):
    # Language String ရယူခြင်း
    try:
        language = await get_lang(message.chat.id)
        _ = get_string(language)
    except:
        _ = get_string("en")

    # URL သို့မဟုတ် Query ရှာဖွေခြင်း
    url = await YouTube.url(message)
    
    # --- (၂) အကယ်၍ စာသားမပါရင် Playlist Button ပြမည် ---
    if not url and len(message.command) < 2:
        buttons = botplaylist_markup(_)
        return await message.reply_photo(
            photo=config.PLAYLIST_IMG_URL,
            caption=_["playlist_1"],
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    # ------------------------------------------------

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

    # ၂။ YouTube Data ရယူခြင်း & Inline Markup အသုံးပြုခြင်း
    try:
        query = url if url else message.text.split(None, 1)[1]
        
        try:
            result = await YouTube.details(query)
            if not result:
                return await mystic.edit_text("❌ မတွေ့ရှိပါ။")
            
            (title, duration_min, duration_sec, thumbnail, vidid) = result
            
            # --- (၃) Live Stream စစ်ဆေးခြင်း ---
            if duration_min == "Live" or not duration_min:
                # Live ဖြစ်နေရင် ချက်ချင်းမဖွင့်ဘဲ ခလုတ်ပြမယ် (Main Bot လိုမျိုး)
                buttons = livestream_markup(
                    _,
                    vidid,
                    message.from_user.id,
                    "v" if "vplay" in message.command[0] else "a",
                    "g", # Mode (Group)
                    "d", # Force Play (Default)
                )
                return await mystic.edit_text(
                    _["play_13"], # "Live stream detected..."
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
            # --------------------------------
            
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

# Note: Callback Queries (ခလုတ်နှိပ်ရင် အလုပ်လုပ်ဖို့) အတွက်
# သီးသန့် Callback Handler တွေ Clone Bot မှာ ထပ်ထည့်ဖို့ လိုအပ်နိုင်ပါတယ်။
# Main Bot ရဲ့ Callback တွေက Clone Bot နဲ့ ချိတ်ဆက်ထားခြင်း မရှိရင် ခလုတ်တွေက အလုပ်လုပ်မှာ မဟုတ်ပါဘူး။
