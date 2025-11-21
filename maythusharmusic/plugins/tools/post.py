import re
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from maythusharmusic import app
from config import OWNER_ID

@app.on_message(filters.command(["post", "sendpost"]) & filters.user(OWNER_ID))
async def create_post(client: Client, message: Message):
    # Command မှာ Channel ID ပါမပါ စစ်ဆေးခြင်း
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>အသုံးပြုပုံ:</b>\n"
            "1. ပုံ (သို့) စာသားတစ်ခုကို Reply ပြန်ပါ။\n"
            "2. Command ရိုက်ပါ: <code>/post [Channel ID] [Caption] ~ [Button][Link]</code>\n\n"
            "<b>ဥပမာ:</b>\n"
            "<code>/post -100xxxxxx မင်္ဂလာပါ ~ [Join Channel][https://t.me/xxxx]</code>"
        )

    try:
        chat_id = message.command[1] # Channel ID
        
        # Caption နဲ့ Button ခွဲထုတ်ခြင်း
        raw_text = ""
        if len(message.command) > 2:
            raw_text = message.text.split(None, 2)[2]

        caption_text = raw_text
        reply_markup = None

        # "~" ပါရင် Button ပါတယ်လို့ ယူဆမယ်
        if "~" in raw_text:
            parts = raw_text.split("~", 1)
            caption_text = parts[0].strip() # "~" အရှေ့က စာသား
            button_data = parts[1].strip() # "~" အနောက်က Button Data

            # Button များကို [Name][Link] ပုံစံဖြင့် ရှာဖွေခြင်း
            pattern = r"\[(.*?)\]\[(.*?)\]"
            matches = re.findall(pattern, button_data)

            if matches:
                keyboard = []
                row = []
                for name, link in matches:
                    row.append(InlineKeyboardButton(text=name, url=link.strip()))
                    # တစ်တန်းမှာ ၂ ခုပြမယ် (လိုချင်ရင် ပြောင်းလို့ရပါတယ်)
                    if len(row) == 2:
                        keyboard.append(row)
                        row = []
                if row:
                    keyboard.append(row)
                reply_markup = InlineKeyboardMarkup(keyboard)

        # (က) Reply ပြန်ထားတာ ပုံ (Photo) ဖြစ်လျှင်
        if message.reply_to_message and message.reply_to_message.photo:
            await client.send_photo(
                chat_id=int(chat_id),
                photo=message.reply_to_message.photo.file_id,
                caption=caption_text,
                reply_markup=reply_markup
            )
        
        # (ခ) Reply ပြန်ထားတာ စာ (Text) သက်သက်ဖြစ်လျှင်
        elif message.reply_to_message and message.reply_to_message.text:
            # Reply ထားတဲ့စာကို ယူမယ်၊ Command မှာရေးထားတဲ့ Caption ရှိရင် အစားထိုးမယ်
            final_text = caption_text if caption_text else message.reply_to_message.text
            await client.send_message(
                chat_id=int(chat_id),
                text=final_text,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )

        # (ဂ) Reply မဟုတ်ဘဲ Command နဲ့တန်းပို့လျှင် (စာသားသီးသန့်)
        else:
            if not caption_text:
                return await message.reply_text("ပို့မည့် စာသား (သို့) ပုံကို Reply ပြန်ပေးပါ။")
                
            await client.send_message(
                chat_id=int(chat_id),
                text=caption_text,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )

        await message.reply_text("✅ <b>Channel သို့ Post တင်ပြီးပါပြီ။</b>")

    except Exception as e:
        await message.reply_text(f"❌ <b>Error:</b> {e}")
