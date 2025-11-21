# maythusharmusic/plugins/tools/antisticker.py

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from maythusharmusic import app
from maythusharmusic.utils.database import is_antisticker_on, antisticker_on, antisticker_off
from maythusharmusic.utils.admin_check import admin_check
from config import BANNED_USERS

# --- (၁) အဖွင့်/အပိတ် Command ---
@app.on_message(filters.command("antisticker") & filters.group & ~BANNED_USERS)
async def antisticker_control(client: Client, message: Message):
    # Admin ဟုတ်မဟုတ် စစ်ဆေးခြင်း
    if not await admin_check(message):
        return await message.reply_text("⚠️ ဤ Command ကို <b>Admin</b> များသာ သုံးနိုင်ပါသည်။")
    
    if len(message.command) != 2:
        return await message.reply_text("<b>အသုံးပြုပုံ:</b>\n/antisticker [on|off]")
    
    state = message.command[1].lower()
    
    if state == "on" or state == "enable":
        await antisticker_on(message.chat.id)
        await message.reply_text("🚫 <b>Anti-Sticker စနစ်ကို ဖွင့်လိုက်ပါပြီ။</b>\n\nယခုမှစ၍ Admin မှလွဲပြီး အခြားသူများ Sticker ပို့၍မရပါ။")
        
    elif state == "off" or state == "disable":
        await antisticker_off(message.chat.id)
        await message.reply_text("✅ <b>Anti-Sticker စနစ်ကို ပိတ်လိုက်ပါပြီ။</b>\n\nလူတိုင်း Sticker ပို့နိုင်ပါပြီ။")
        
    else:
        await message.reply_text("<b>အသုံးပြုပုံ:</b>\n/antisticker [on|off]")


# --- (၂) Sticker များကို စောင့်ကြည့်ပြီး ဖျက်မည့် Function ---
@app.on_message(filters.sticker & filters.group)
async def delete_stickers(client: Client, message: Message):
    # Anti-Sticker ဖွင့်ထားခြင်း ရှိမရှိ စစ်ဆေးခြင်း
    if not await is_antisticker_on(message.chat.id):
        return # မဖွင့်ထားရင် ဘာမှမလုပ်ဘဲ ကျော်မယ်

    # ပို့သူက Admin ဟုတ်မဟုတ် စစ်ဆေးခြင်း (Admin ဆိုရင် ခွင့်ပြုမယ်)
    try:
        member = await client.get_chat_member(message.chat.id, message.from_user.id)
        if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
            return
    except:
        pass

    # Admin မဟုတ်ရင် Sticker ကို ဖျက်မယ်
    try:
        await message.delete()
    except Exception:
        # Bot က Admin မဟုတ်လို့ ဖျက်မရရင် ကျော်သွားမယ်
        pass
        
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from maythusharmusic import app
from maythusharmusic.utils.database import is_antisticker_on, antisticker_on, antisticker_off
from maythusharmusic.utils.admin_check import admin_check
from config import BANNED_USERS, OWNER_ID

# --- (၁) အဖွင့်/အပိတ် Command ---
@app.on_message(filters.command("antisticker") & filters.group & ~BANNED_USERS)
async def antisticker_control(client: Client, message: Message):
    # Admin ဟုတ်မဟုတ် စစ်ဆေးခြင်း
    if not await admin_check(message):
        return await message.reply_text("⚠️ ဤ Command ကို <b>Admin</b> များသာ သုံးနိုင်ပါသည်။")
    
    if len(message.command) != 2:
        return await message.reply_text("<b>အသုံးပြုပုံ:</b>\n/antisticker [on|off]")
    
    state = message.command[1].lower()
    
    if state == "devon" or state == "devenable":
        await antisticker_on(message.chat.id)
        await message.reply_text("🚫 <b>Anti-Sticker စနစ်ကို ဖွင့်လိုက်ပါပြီ။</b>\n\nယခုမှစ၍ <b>Group Owner (ပိုင်ရှင်)</b> မှလွဲပြီး Admin များအပါအဝင် မည်သူမျှ Sticker ပို့၍မရပါ။")
        
    elif state == "devoff" or state == "devdisable":
        await antisticker_off(message.chat.id)
        await message.reply_text("✅ <b>Anti-Sticker စနစ်ကို ပိတ်လိုက်ပါပြီ။</b>\n\nလူတိုင်း Sticker ပို့နိုင်ပါပြီ။")
        
    else:
        await message.reply_text("<b>အသုံးပြုပုံ:</b>\n/antisticker [on|off]")


# --- (၂) Sticker များကို စောင့်ကြည့်ပြီး ဖျက်မည့် Function (Strict Mode) ---
@app.on_message(filters.sticker & filters.group)
async def delete_stickers(client: Client, message: Message):
    # Anti-Sticker ဖွင့်ထားခြင်း ရှိမရှိ စစ်ဆေးခြင်း
    if not await is_antisticker_on(message.chat.id):
        return 

    # (က) Bot Owner ဖြစ်လျှင် ခွင့်ပြုမည်
    if message.from_user.id == OWNER_ID:
        return

    # (ခ) Group Owner (ပိုင်ရှင်) ဖြစ်မှသာ ခွင့်ပြုမည်
    try:
        member = await client.get_chat_member(message.chat.id, message.from_user.id)
        if member.status == ChatMemberStatus.OWNER:
            return # Owner ဆိုရင် မဖျက်ဘူး
            
        # မှတ်ချက်: ChatMemberStatus.ADMINISTRATOR ကို ဖြုတ်လိုက်ပါပြီ
        # ဒါကြောင့် Admin တွေပို့ရင်လည်း အောက်ရောက်ပြီး အဖျက်ခံရပါမယ်
        
    except:
        pass

    # ကျန်သူများ (Admin + Member) ၏ Sticker ကို ဖျက်မည်
    try:
        await message.delete()
    except Exception:
        pass
