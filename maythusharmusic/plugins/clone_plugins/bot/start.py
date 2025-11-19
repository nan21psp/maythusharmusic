from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from maythusharmusic.utils.database import get_lang
from strings import get_string
import config

# --- (၁) Button Function ကို ဒီဖိုင်ထဲမှာပဲ သီးသန့်ထည့်သွင်းခြင်း ---
def clone_start_pm(_, bot_username):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_3"], # "အုပ်စုသို့ထည့်ရန်"
                url=f"https://t.me/{bot_username}?startgroup=s&admin=delete_messages+manage_video_chats+pin_messages+invite_users+ban_users",
            )
        ],
        [
            InlineKeyboardButton(text=_["S_B_5"], user_id=config.OWNER_ID), # "ပိုင်ရှင်"
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_CHAT), # "အကူအညီ"
        ],
        [
            InlineKeyboardButton(text=_["S_B_6"], url=config.SUPPORT_CHANNEL), # "ချန်နယ်"
        ],
    ]
    return buttons
# ---------------------------------------------------------------

@Client.on_message(filters.command(["start"]))
async def start_clone(client: Client, message: Message):
    # Language String ရယူခြင်း
    try:
        language = await get_lang(message.chat.id)
        _ = get_string(language)
    except:
        _ = get_string("en")

    if message.chat.type == "private":
        # Bot Username ယူခြင်း
        bot_username = client.me.username
        
        # အပေါ်က Function ကို ခေါ်သုံးပြီး ခလုတ်များရယူခြင်း
        buttons = clone_start_pm(_, bot_username)
        
        await message.reply_photo(
            photo=config.START_IMG_URL,
            caption=f"""
<b>👋 မင်္ဂလာပါ {message.from_user.mention} ခင်ဗျာ!</b>

ဒါကတော့ <b>{client.me.first_name}</b> (Clone Music Bot) ဖြစ်ပါတယ်။

ကျွန်တော့်ကို Group ထဲထည့်ပြီး Admin ပေးထားရင် သီချင်းနားထောင်လို့ ရပါပြီ။
""",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await message.reply_text("✅ Clone Music Bot အလုပ်လုပ်နေပါတယ်။")
