import re
import logging
import traceback
import os
import shutil
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import AccessTokenInvalid

from config import API_ID, API_HASH, OWNER_ID
from maythusharmusic import app

# Clone Bot များကို ယာယီမှတ်ထားရန်
CLONES = set()

@app.on_message(filters.command("clone") & filters.private)
async def clone_txt(client, message: Message):
    try:
        try:
            from maythusharmusic.utils.database import save_clone, get_clone_by_user
        except ImportError:
            return await message.reply_text("❌ Database Error")

        # ONE USER ONE BOT LIMIT CHECK
        user_id = message.from_user.id
        existing_clone = await get_clone_by_user(user_id)
        
        if existing_clone:
            bot_username = existing_clone.get("bot_username", "Unknown")
            bot_token = existing_clone.get("bot_token", "")
            return await message.reply_text(
                f"⚠️ <b>ကန့်သတ်ချက်!</b>\n\n"
                f"မိတ်ဆွေတွင် Clone Bot တစ်ခု ရှိပြီးသား ဖြစ်နေပါသည်။\n"
                f"🤖 <b>Bot:</b> @{bot_username}\n\n"
                f"နောက်တစ်ခု အသစ်ထပ်လုပ်လိုပါက ရှိပြီးသား Bot ကို အရင်ဖျက်ပေးပါ:\n"
                f"<code>/delclone {bot_token}</code>"
            )

        if len(message.command) < 2:
            return await message.reply_text(
                "<b>အသုံးပြုပုံ :</b>\n\n/clone [Bot Token]\n\nBot Token ကို @BotFather ထံမှ ရယူပါ။"
            )
        
        bot_token = message.text.split(None, 1)[1]
        
        if not re.match(r'^\d+:[a-zA-Z0-9_-]+$', bot_token):
            return await message.reply_text("❌ မှားယွင်းသော Bot Token ဖြစ်ပါသည်။")

        msg = await message.reply_text("♻️ <b>Clone Bot ဖန်တီးနေပါသည်...</b>\n\nခေတ္တစောင့်ဆိုင်းပေးပါ။")

        try:
            ai = Client(
                name=bot_token,
                api_id=API_ID,
                api_hash=API_HASH,
                bot_token=bot_token,
                plugins=dict(root="maythusharmusic.plugins.clone_plugins"),
            )
            
            await ai.start()
            bot_info = await ai.get_me()
            username = bot_info.username
            
            await save_clone(bot_token, user_id, username)
            CLONES.add(bot_token)
            
            details = f"""
<b>✅ Clone Bot အောင်မြင်စွာ ဖန်တီးပြီးပါပြီ!</b>

<b>🤖 Bot Name:</b> {bot_info.first_name}
<b>🔗 Username:</b> @{username}

<i>⚠️မှတ်ချက်: သီချင်းနားထောင်ရန် သင့် Clone Bot ကို Group ထဲထည့်ပြီး Admin ပေးထားပါ။</i>
"""
            await msg.edit_text(details)
            
        except AccessTokenInvalid:
            await msg.edit_text("❌ Bot Token မှားယွင်းနေပါသည်။")
        except Exception as e:
            await msg.edit_text(f"❌ အမှားဖြစ်ပွားခဲ့သည်: {e}")

    except Exception as e:
        await message.reply_text(f"🐞 <b>Error:</b> {e}")


@app.on_message(filters.command("delclone") & filters.private)
async def delete_clone_bot(client, message: Message):
    try:
        from maythusharmusic.utils.database import delete_clone, get_clone_by_user
        
        token = None
        if len(message.command) >= 2:
            token = message.text.split(None, 1)[1]
        else:
            user_clone = await get_clone_by_user(message.from_user.id)
            if user_clone:
                token = user_clone.get("bot_token")
            else:
                return await message.reply_text("⚠️ မိတ်ဆွေတွင် ဖျက်စရာ Clone Bot မရှိပါ။")

        await delete_clone(token)
        await message.reply_text("✅ Clone Bot ကို အောင်မြင်စွာ ဖျက်သိမ်းလိုက်ပါပြီ။")
        
    except Exception as e:
        await message.reply_text(f"Error: {e}")


# --- (၁) OWNER ONLY: Clone Bot အရေအတွက် ကြည့်ခြင်း ---
@app.on_message(filters.command("totalclones") & filters.user(OWNER_ID))
async def total_clones_stats(client, message: Message):
    try:
        from maythusharmusic.utils.database import get_clones
        clones = await get_clones()
        
        total = len(clones)
        text = f"📊 <b>Clone Bot စာရင်းအင်းများ</b>\n\n"
        text += f"🤖 <b>စုစုပေါင်း Clones:</b> {total}\n\n"
        
        if total > 0:
            text += "<b>Bot Usernames:</b>\n"
            for count, clone in enumerate(clones, 1):
                username = clone.get("bot_username", "Unknown")
                text += f"{count}. @{username}\n"
        
        await message.reply_text(text)
    except Exception as e:
        await message.reply_text(f"Error: {e}")


# --- (၂) OWNER ONLY: Clone Bot အားလုံးကို ဖျက်ခြင်း ---
@app.on_message(filters.command("delallclones") & filters.user(OWNER_ID))
async def delete_all_clones_func(client, message: Message):
    try:
        from maythusharmusic.utils.database import remove_all_clones, get_clones
        
        # Confirm လုပ်ခိုင်းခြင်း
        if len(message.command) < 2 or message.text.split()[1] != "confirm":
            return await message.reply_text(
                "⚠️ <b>သတိပေးချက်!</b>\n\n"
                "Clone Bot အားလုံးကို ဖျက်ပစ်မှာ သေချာပါသလား?\n"
                "သေချာရင် အောက်ပါအတိုင်း ရိုက်ပါ:\n"
                "<code>/delallclones confirm</code>"
            )
            
        msg = await message.reply_text("♻️ <b>Clone Bot အားလုံးကို ဖျက်သိမ်းနေပါသည်...</b>")
        
        # Database ရှင်းလင်းခြင်း
        await remove_all_clones()
        
        # Session Files များကို ရှင်းလင်းခြင်း (Optional)
        # (Client session files တွေကျန်ခဲ့ရင် နေရာယူလို့ ရှင်းတာပါ)
        # session file တွေက root folder မှာ ရှိနေတတ်ပါတယ်
        
        await msg.edit_text("✅ <b>Clone Bot အားလုံးကို Database မှ အောင်မြင်စွာ ဖျက်သိမ်းလိုက်ပါပြီ။</b>\n\nEffect သက်ရောက်စေရန် Bot ကို Restart ချပေးပါ။ (/reboot)")
        
    except Exception as e:
        await message.reply_text(f"Error: {e}")


async def restart_clones():
    try:
        from maythusharmusic.utils.database import get_clones
        clones = await get_clones()
        
        if not clones:
            return
        
        print(f"Total Clones Found: {len(clones)}")
        
        for clone in clones:
            token = clone["bot_token"]
            try:
                ai = Client(
                    name=token,
                    api_id=API_ID,
                    api_hash=API_HASH,
                    bot_token=token,
                    plugins=dict(root="maythusharmusic.plugins.clone_plugins"),
                )
                await ai.start()
                print(f"Started Clone: @{clone['bot_username']}")
                CLONES.add(token)
            except Exception as e:
                print(f"Failed to start clone {token}: {e}")
    except ImportError:
        print("Database module loading error inside restart_clones")
    except Exception as e:
        print(f"Error in restart_clones: {e}")


@app.on_message(filters.command("clonebot") & filters.user(OWNER_ID))
async def clone_mode_switch(client, message: Message):
    try:
        from maythusharmusic.utils.database import set_clones_active, is_clones_active
        
        if len(message.command) != 2:
            status = await is_clones_active()
            txt = "✅ <b>Enabled</b>" if status else "❌ <b>Disabled</b>"
            return await message.reply_text(f"<b>Current Clone System Status:</b> {txt}\n\n<b>Usage:</b> <code>/clonebot [on|off]</code>")
            
        state = message.text.split(None, 1)[1].strip().lower()
        
        if state == "on" or state == "enable":
            await set_clones_active(True)
            await message.reply_text("✅ <b>Clone Bot System ကို ဖွင့်လိုက်ပါပြီ။</b>\nClone Bot အားလုံး ပုံမှန်အတိုင်း အလုပ်ပြန်လုပ်ပါမည်။")
            
        elif state == "off" or state == "disable":
            await set_clones_active(False)
            await message.reply_text("❌ <b>Clone Bot System ကို ပိတ်လိုက်ပါပြီ။</b>\nClone Bot အားလုံးသည် 'Under Maintenance' ဟု ပြပါမည်။")
            
        else:
            await message.reply_text("<b>Usage:</b> <code>/clonebot [on|off]</code>")
            
    except Exception as e:
        await message.reply_text(f"Error: {e}")





