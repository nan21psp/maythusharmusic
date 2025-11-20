from pyrogram import filters
from pyrogram.types import Message

from maythusharmusic import app
from maythusharmusic.misc import SUDOERS
from maythusharmusic.utils.database import autoend_off, autoend_on

# Autoend ကို default အနေနဲ့ enable လုပ်ထားမယ်
# ဒီ value ကိုပြင်ရုံနဲ့ autoend status ပြောင်းသွားမယ်
AUTOEND_ENABLED = True

@app.on_message(filters.command("autoend") & SUDOERS)
async def auto_end_stream(_, message: Message):
    usage = "<b>ᴇxᴀᴍᴘʟᴇ :</b>\n\n/autoend [ᴇɴᴀʙʟᴇ | ᴅɪsᴀʙʟᴇ]"
    if len(message.command) != 2:
        return await message.reply_text(usage)
    
    state = message.text.split(None, 1)[1].strip().lower()
    if state == "enable":
        await autoend_on()
        await message.reply_text(
            "ᴀᴜᴛᴏ ᴇɴᴅ sᴛʀᴇᴀᴍ ᴇɴᴀʙʟᴇᴅ.\n\nᴀssɪsᴛᴀɴᴛ ᴡɪʟʟ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ʟᴇᴀᴠᴇ ᴛʜᴇ ᴠɪᴅᴇᴏᴄʜᴀᴛ ᴀғᴛᴇʀ ғᴇᴡ ᴍɪɴs ᴡʜᴇɴ ɴᴏ ᴏɴᴇ ɪs ʟɪsᴛᴇɴɪɴɢ."
        )
    elif state == "disable":
        await autoend_off()
        await message.reply_text("» ᴀᴜᴛᴏ ᴇɴᴅ sᴛʀᴇᴀᴍ ᴅɪsᴀʙʟᴇᴅ.")
    else:
        await message.reply_text(usage)

# Autoend status ကိုစစ်ဆေးပြီးသတ်မှတ်မယ်
async def set_autoend_status():
    try:
        if AUTOEND_ENABLED:
            await autoend_on()
            print("🎵 Autoend feature is ENABLED by default")
        else:
            await autoend_off() 
            print("🎵 Autoend feature is DISABLED by default")
    except Exception as e:
        print(f"Error setting autoend status: {e}")

# Function ကိုခေါ်သုံးမယ်
set_autoend_status()
