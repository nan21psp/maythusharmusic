from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from maythusharmusic import app

START_TEXT = """
**✨ ဟယ်လို {}!**

ကျွန်တော်က **{}**၊ အဆင်ပြေချောမွေ့တဲ့ music streaming experience ပေးဖို့ ဒီမှာရှိနေပါတယ်။

**🎵 ကျွန်တော့်မှာရှိတဲ့ အဓိကလုပ်ဆောင်ချက်တွေ:**
• High quality audio streaming
• Unlimited playback
• Queue management
• Channel & Group support
• 24/7 active

အောက်ကခလုတ်တွေကိုနှိပ်ပြီး ကျွန်တော့်ကိုသုံးလို့ရပါတယ်! 🎶
"""

@Client.on_message(filters.command("start") & filters.private)
async def start_private(client, Client, message):
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="🎵 Add me to your group",
                    url=f"https://t.me/{app_username}?startgroup=s&admin=delete_messages+manage_video_chats+pin_messages+invite_users+ban_users"
                )
            ],
            [
                InlineKeyboardButton("👑 Owner", url="https://t.me/iwillgoforwardsalone"),
                InlineKeyboardButton("💬 Support Group", url="https://t.me/sasukemusicsupportchat"),
            ],
            [
                InlineKeyboardButton("📢 Support Channel", url="https://t.me/everythingreset"),
            ],
        ]
    )
    
    await message.reply_text(
        START_TEXT.format(message.from_user.mention, (await client.get_me()).first_name),
        reply_markup=keyboard,
        disable_web_page_preview=True
    )
