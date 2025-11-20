from pyrogram import filters
from pyrogram.types import Message
from maythusharmusic import app
from maythusharmusic.misc import SUDOERS
from maythusharmusic.utils.database import autoend_off, autoend_on

# config.py ထဲမှာ AUTOEND_ENABLED = True/False ဆိုပြီးသတ်မှတ်ထားနိုင်တယ်
try:
    from maythusharmusic.config import AUTOEND_ENABLED
except ImportError:
    AUTOEND_ENABLED = True  # Default value

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

# Autoend status check function
async def get_autoend_status():
    # Database ကနေ current status ကိုဖတ်တဲ့ function လိုအပ်ရင်ဒီမှာထည့်နိုင်တယ်
    return AUTOEND_ENABLED

# Bot start တက်တာနဲ့ autoend setting ကို apply လုပ်မယ်
@app.on_startup()
async def setup_autoend():
    if AUTOEND_ENABLED:
        await autoend_on()
        print("> •ᴀᴜᴛᴏᴇɴᴅ ᴇɴᴀʙʟᴇᴅ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ")
    else:
        await autoend_off()
        print("> •ᴀᴜᴛᴏᴇɴᴅ ᴅɪꜱᴀʙʟᴇᴅ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ")
