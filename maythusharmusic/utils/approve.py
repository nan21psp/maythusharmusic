# maythusharmusic/utils/approve.py

from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import UserNotParticipant
from maythusharmusic import app

async def check_main_bot_admin(client: Client, message: Message):
    """
    Clone Bot အသုံးပြုနေချိန်တွင် Main Bot သည် Group တွင် Admin ဖြစ်မဖြစ် စစ်ဆေးသည်။
    Admin ဖြစ်မှ True ပြန်ပေးမည်။ မဟုတ်ပါက သတိပေးစာပို့ပြီး False ပြန်ပေးမည်။
    """
    try:
        # Main Bot ၏ အချက်အလက်ကို ရယူခြင်း
        if not app.me:
            await app.get_me()
            
        main_bot_id = app.me.id
        main_bot_username = app.me.username

        # လက်ရှိ Run နေတာ Main Bot ဖြစ်နေရင် စစ်ဆေးစရာမလိုပါ (True ပြန်မယ်)
        if client.me.id == main_bot_id:
            return True

        try:
            # Clone Bot (client) ကနေ Main Bot ကို Group ထဲမှာ ရှာခြင်း
            member = await client.get_chat_member(message.chat.id, main_bot_id)
            
            # Main Bot သည် Admin (သို့) Owner မဟုတ်ရင် တားမည်
            if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                await message.reply_text(
                    f"⚠️ <b>Main Bot Admin Required!</b>\n\n"
                    f"ကျွန်တော် (Clone Bot) ကို အသုံးပြုရန်အတွက် မူရင်း Bot ဖြစ်သော @{main_bot_username} ကို ဤ Group တွင် <b>Admin (အက်ဒမင်)</b> ခန့်ထားပေးရပါမည်။",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("➕ Add Main Bot & Promote", url=f"https://t.me/{main_bot_username}?startgroup=true")]
                    ])
                )
                return False # စစ်ဆေးမှု မအောင်မြင်
                
        except UserNotParticipant:
            # Main Bot Group ထဲမှာ လုံးဝမရှိရင် တားမည်
            await message.reply_text(
                f"⚠️ <b>Main Bot Missing!</b>\n\n"
                f"Clone Bot ကို အသုံးပြုရန်အတွက် မူရင်း Bot ဖြစ်သော @{main_bot_username} ကို ဤ Group ထဲသို့ ထည့်သွင်းပြီး <b>Admin</b> ပေးထားပါ။",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add Main Bot", url=f"https://t.me/{main_bot_username}?startgroup=true")]
                ])
            )
            return False # စစ်ဆေးမှု မအောင်မြင်

        # အားလုံးအဆင်ပြေရင် True ပြန်ပေးမည်
        return True

    except Exception as e:
        print(f"Approve Check Error: {e}")
        return True # Error တက်ရင် အလုပ်ဆက်လုပ်ခွင့်ပြုမည် (Fail-safe)
