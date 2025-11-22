from pyrogram.enums import ParseMode
from maythusharmusic import app
from maythusharmusic.utils.database import is_on_off
from config import LOGGER_ID

async def play_logs(message, streamtype):
    # Logger ဖွင့်ထားမှ လုပ်မည်
    if await is_on_off(2):
        # Log စာသား ဖန်တီးခြင်း
        logger_text = f"""
<b>{app.mention} ᴘʟᴀʏ ʟᴏɢ</b>

<b>ᴄʜᴀᴛ ɪᴅ :</b> <code>{message.chat.id}</code>
<b>ᴄʜᴀᴛ ɴᴀᴍᴇ :</b> {message.chat.title}
<b>ᴄʜᴀᴛ ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.chat.username}

<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>
<b>ɴᴀᴍᴇ :</b> {message.from_user.mention}
<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}

<b>ǫᴜᴇʀʏ :</b> {message.text.split(None, 1)[1]}
<b>sᴛʀᴇᴀᴍᴛʏᴘᴇ :</b> {streamtype}"""
        
        # Log Group ထဲမှာ သီချင်းဖွင့်ရင် Log ထပ်မပို့ပါ (Loop မဖြစ်အောင်)
        if message.chat.id != LOGGER_ID:
            try:
                # နည်းလမ်း (၁) - Main Bot ဖြင့် ပို့မည်
                await app.send_message(
                    chat_id=LOGGER_ID,
                    text=logger_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
            except Exception as e:
                # နည်းလမ်း (၂) - Main Bot မရရင် Clone Bot (message client) ဖြင့် ပို့မည်
                try:
                    await message._client.send_message(
                        chat_id=LOGGER_ID,
                        text=logger_text,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True,
                    )
                except Exception as e2:
                    print(f"Failed to send log: {e2}")
        return
