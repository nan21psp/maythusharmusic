# maythusharmusic/plugins/clone_plugins/start.py

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from maythusharmusic import app
import config

@Client.on_message(filters.command(["start"]))
async def start_clone(client: Client, message: Message):
    if message.chat.type == "private":
        await message.reply_photo(
            photo=config.START_IMG_URL,
            caption=f"""
<b>👋 မင်္ဂလာပါ {message.from_user.mention} ခင်ဗျာ!</b>

ဒါကတော့ <b>{client.me.first_name}</b> (Clone Music Bot) ဖြစ်ပါတယ်။

ကျွန်တော့်ကို Group ထဲထည့်ပြီး Admin ပေးထားရင် သီချင်းနားထောင်လို့ ရပါပြီ။
""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Me To Group", url=f"https://t.me/{client.me.username}?startgroup=true")],
                [InlineKeyboardButton("📣 Support Channel", url=config.SUPPORT_CHANNEL)],
            ])
        )
    else:
        await message.reply_text("✅ Clone Music Bot အလုပ်လုပ်နေပါတယ်။")
