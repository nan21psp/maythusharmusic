import re
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from maythusharmusic import app
from config import OWNER_ID

@app.on_message(filters.command(["post", "sendpost"]) & filters.user(OWNER_ID))
async def create_post(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /post [Channel ID] [Message] ~ [Button][Link]")

    try:
        chat_id = message.command[1]
        raw_text = ""
        if len(message.command) > 2:
            raw_text = message.text.split(None, 2)[2]

        caption_text = raw_text
        reply_markup = None

        if "~" in raw_text:
            parts = raw_text.split("~", 1)
            caption_text = parts[0].strip()
            button_data = parts[1].strip()

            pattern = r"\[(.*?)\]\[(.*?)\]"
            matches = re.findall(pattern, button_data)

            if matches:
                keyboard = []
                row = []
                for name, link in matches:
                    row.append(InlineKeyboardButton(text=name, url=link.strip()))
                    if len(row) == 2:
                        keyboard.append(row)
                        row = []
                if row:
                    keyboard.append(row)
                reply_markup = InlineKeyboardMarkup(keyboard)

        if message.reply_to_message and message.reply_to_message.photo:
            await client.send_photo(
                chat_id=int(chat_id),
                photo=message.reply_to_message.photo.file_id,
                caption=caption_text,
                reply_markup=reply_markup
            )
        elif message.reply_to_message and message.reply_to_message.text:
            final_text = caption_text if caption_text else message.reply_to_message.text
            await client.send_message(
                chat_id=int(chat_id),
                text=final_text,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
        else:
            await client.send_message(
                chat_id=int(chat_id),
                text=caption_text,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )

        await message.reply_text("✅ Posted!")

    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")
