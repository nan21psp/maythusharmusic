# maythusharmusic/plugins/sudo/autoadd.py

import asyncio
from pyrogram import filters
from pyrogram.enums import ChatType
from maythusharmusic import app
from maythusharmusic.misc import SUDOERS
from maythusharmusic.utils.database import get_assistant

# Command: /addmain (Sudo Users Only)
# Main Bot မှာပဲ အလုပ်လုပ်ပါမယ်

@app.on_message(filters.command("addmain") & SUDOERS)
async def add_main_bot_to_all_chats(client, message):
    # Main Bot ဟုတ်မဟုတ် စစ်ဆေးခြင်း
    if client.me.id != app.me.id:
        return await message.reply_text("⚠️ ဤ Command ကို Main Bot တွင်သာ အသုံးပြုနိုင်ပါသည်။")

    msg = await message.reply_text("♻️ <b>Assistant ရှိသော Group များသို့ Main Bot ကို လိုက်လံထည့်သွင်းနေပါသည်...</b>\n\n<i>(ဤလုပ်ဆောင်ချက်သည် အချိန်အနည်းငယ် ကြာနိုင်ပါသည်)</i>")
    
    try:
        # 1. Assistant နှင့် Main Bot အချက်အလက် ရယူခြင်း
        userbot = await get_assistant(message.chat.id)
        bot_username = app.me.username
        bot_id = app.me.id
        
        added_count = 0
        failed_count = 0
        already_in_count = 0
        
        # 2. Assistant ၏ Chat များကို စစ်ဆေးခြင်း
        async for dialog in userbot.get_dialogs():
            # Group နှင့် Supergroup များကိုသာ ရွေးချယ်မည်
            if dialog.chat.type in [ChatType.SUPERGROUP, ChatType.GROUP]:
                chat_id = dialog.chat.id
                
                try:
                    # Main Bot ရှိပြီးသားလား စစ်ဆေးမည်
                    member = await userbot.get_chat_member(chat_id, bot_id)
                    already_in_count += 1
                    continue 
                except:
                    # မရှိသေးရင် Add မည်
                    try:
                        await userbot.add_chat_members(chat_id, bot_username)
                        added_count += 1
                        # FloodWait ရှောင်ရန် အနည်းငယ်နားမည်
                        await asyncio.sleep(1.5) 
                    except Exception as e:
                        # Admin မဟုတ်လို့ (သို့) Ban ထားလို့ ထည့်မရတာ ဖြစ်နိုင်သည်
                        failed_count += 1
                        await asyncio.sleep(0.5)

        # 3. ရလဒ်ပြသခြင်း
        await msg.edit_text(
            f"✅ <b>လုပ်ဆောင်မှု ပြီးဆုံးပါပြီ!</b>\n\n"
            f"📥 <b>အောင်မြင်စွာ ထည့်သွင်းမှု:</b> {added_count}\n"
            f"⚠️ <b>ထည့်မရပါ (Admin လိုအပ်/Ban):</b> {failed_count}\n"
            f"ℹ️ <b>ရှိပြီးသား Group များ:</b> {already_in_count}"
        )
        
    except Exception as e:
        await msg.edit_text(f"❌ <b>Error:</b> {e}")
