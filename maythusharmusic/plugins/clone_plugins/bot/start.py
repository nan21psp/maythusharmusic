from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from maythusharmusic import app

# Quote ပုံစံပေါ်ဖို့အတွက် စာကြောင်းရှေ့မှာ > ကိုထည့်ပေးထားပါတယ်
START_TEXT = """
**🫧 ʜᴇʟʟᴏ {}!**

> ɪ ᴀᴍ **{}**, ʜᴇʀᴇ ᴛᴏ ᴘʀᴏᴠɪᴅᴇ ʏᴏᴜ ᴡɪᴛʜ ᴀ ꜱᴍᴏᴏᴛʜ ᴍᴜꜱɪᴄ ꜱᴛʀᴇᴀᴍɪɴɢ ᴇxᴘᴇʀɪᴇɴᴄᴇ.

> • ᴍʏ ᴍᴀɪɴ ꜰᴜɴᴄᴛɪᴏɴꜱ
> • ʜǫ ᴀᴜᴅɪᴏ : 320ᴋʙᴘs sᴛʀᴇᴀᴍɪɴɢ
> • sᴛʀᴇᴀᴍ sᴜᴘᴘᴏʀᴛ : ᴀᴜᴅɪᴏ-ᴠɪᴅᴇᴏ
> • 24-7 ᴜᴘᴛɪᴍᴇ : ᴇɴᴛᴇʀᴘʀɪsᴇ ʀᴇʟɪᴀʙɪʟɪᴛʏ
> • ᴘʟᴀʏ ᴄᴏᴍᴍᴇɴᴛꜱ : play, vplay, mp4 support 
> • ʙᴇsᴇᴅ ᴏɴ : ʏᴏᴜᴛᴜʙᴇ ᴀᴘɪ

ʏᴏᴜ ᴄᴀɴ ᴜꜱᴇ ᴍᴇ ʙʏ ᴄʟɪᴄᴋɪɴɢ ᴛʜᴇ ʙᴜᴛᴛᴏɴꜱ ʙᴇʟᴏᴡ. 🫧
"""

@Client.on_message(filters.command("start") & filters.private)
async def start_private(client: Client, message: Message):
    # Bot username ကိုရယူခြင်း
    app_username = (await client.get_me()).username
    
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ",
                    url=f"https://t.me/{app_username}?startgroup=s&admin=delete_messages+manage_video_chats+pin_messages+invite_users+ban_users"
                )
            ],
            [
                InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴘᴇʀ", url="https://t.me/iwillgoforwardsalone"),
                InlineKeyboardButton("ꜱᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ", url="https://t.me/sasukemusicsupportchat"),
            ],
            [
                InlineKeyboardButton("ꜱᴜᴘᴘᴏʀᴛ ᴄʜᴀɴɴᴇʟ", url="https://t.me/everythingreset"),
            ],
        ]
    )
    
    await message.reply_text(
        START_TEXT.format(message.from_user.mention, (await client.get_me()).first_name),
        reply_markup=keyboard,
        disable_web_page_preview=True
    )
