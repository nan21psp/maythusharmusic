import re
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from maythusharmusic import app
from config import OWNER_ID

@app.on_message(filters.command(["post", "sendlink"]) & filters.user(OWNER_ID))
async def post_with_buttons(client: Client, message: Message):
    if len(message.command) < 3:
        return await message.reply_text(
            "<b>အသုံးပြုပုံ:</b>\n"
            "<code>/post [Channel ID] [စာသား] ~ [Button Name][URL]</code>\n\n"
            "<b>ဥပမာ:</b>\n"
            "<code>/post -1001234567890 မင်္ဂလာပါ ခင်ဗျာ ~ [Join Channel][https://t.me/D_E_V_S]</code>"
        )

    try:
        # Channel ID ကို ခွဲယူခြင်း
        chat_id = message.command[1]
        
        # ကျန်တဲ့ စာသားအားလုံးကို ယူခြင်း
        raw_text = message.text.split(None, 2)[2]

        text_content = ""
        markup = None

        # Button ပါ/မပါ စစ်ဆေးခြင်း ("~" သင်္ကေတ ခံထားရမည်)
        if "~" in raw_text:
            parts = raw_text.split("~", 1)
            text_content = parts[0].strip()
            button_part = parts[1].strip()

            # Button Format ကို ရှာဖွေခြင်း: [Name][Link]
            # ဥပမာ: [Google][https://google.com] [Channel][https://t.me/...]
            pattern = r"\[(.*?)\]\[(.*?)\]"
            matches = re.findall(pattern, button_part)

            keyboard = []
            row = []
            for name, link in matches:
                row.append(InlineKeyboardButton(text=name, url=link.strip()))
                # တစ်တန်းမှာ ၂ ခုပြမယ်
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)

            if keyboard:
                markup = InlineKeyboardMarkup(keyboard)
        else:
            text_content = raw_text

        # Channel သို့ ပို့ခြင်း
        await client.send_message(
            chat_id=int(chat_id),
            text=text_content,
            reply_markup=markup,
            disable_web_page_preview=True
        )
        await message.reply_text("✅ <b>Post တင်ခြင်း အောင်မြင်ပါသည်။</b>")

    except Exception as e:
        await message.reply_text(f"❌ <b>Error:</b> {e}")
