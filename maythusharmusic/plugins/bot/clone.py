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
    # Variable Initialization (Error ကာကွယ်ရန်)
    bot_token = None
    
    try:
        try:
            from maythusharmusic.utils.database import save_clone, get_clone_by_user, is_clones_active
        except ImportError:
            return await message.reply_text("❌ Database Error: Module Import Failed")

        # --- (၁) SYSTEM ON/OFF CHECK ---
        if not await is_clones_active():
            return await message.reply_text(
                "> •**𝙎𝙮𝙨𝙩𝙚𝙢 𝙈𝙖𝙞𝙣𝙩𝙚𝙣𝙖𝙣𝙘𝙚**\n"
                ">\n"
                "> •𝘾𝙡𝙤𝙣𝙚 𝙗𝙤𝙩 စနစ်ကို 𝙊𝙬𝙣𝙚𝙧 မှ ယာယီပိတ်ထားပါသည်။\n"
                "> •ခေတ္တစောင့်ဆိုင်းပြီးမှ ပြန်လည်ကြိုးစားပါ။"
            )
        # -----------------------------

        # --- (၂) ONE USER ONE BOT LIMIT CHECK ---
        user_id = message.from_user.id
        existing_clone = await get_clone_by_user(user_id)
        
        if existing_clone:
            bot_username = existing_clone.get("bot_username", "Unknown")
            bot_token_existing = existing_clone.get("bot_token", "")
            return await message.reply_text(
                f">𝗡𝗼𝘁𝗶𝗰 𝗙𝗼𝗿 𝗨𝘀𝗲𝗿𝘀\n"
                f"𝙔𝙤𝙪 𝙖𝙡𝙧𝙚𝙖𝙙𝙮 𝙝𝙖𝙫𝙚 𝙖 𝘾𝙡𝙤𝙣𝙚 𝘽𝙤𝙩.\n"
                f"𝗕𝗼𝘁 : @{bot_username}\n\n"
                f"𝙄𝙛 𝙮𝙤𝙪 𝙬𝙖𝙣𝙩 𝙩𝙤 𝙘𝙧𝙚𝙖𝙩𝙚 𝙖 𝙣𝙚𝙬 𝙤𝙣𝙚, 𝙙𝙚𝙡𝙚𝙩𝙚 𝙩𝙝𝙚 𝙚𝙭𝙞𝙨𝙩𝙞𝙣𝙜 𝘽𝙤𝙩 𝙛𝙞𝙧𝙨𝙩.\n"
                f"><code>/delclone {bot_token_existing}</code>"
            )

        if len(message.command) < 2:
            return await message.reply_text(
                "<b>D͟e͟v͟e͟l͟o͟p͟e͟r͟ : @iwillgoforwardsalone</b>\n\n/clone [Bot Token]\n\nGᴇᴛ ʙᴏᴛ ᴛᴏᴋᴇɴ ꜰʀᴏᴍ @BotFather"
            )
        
        bot_token = message.text.split(None, 1)[1]
        
        if not re.match(r'^\d+:[a-zA-Z0-9_-]+$', bot_token):
            return await message.reply_text("❌ 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗕𝗼𝘁 𝗧𝗼𝗸𝗲𝗻.")

        msg = await message.reply_text("🫧 <b>ʀᴇǫᴜᴇsᴛɪɴɢ ᴘᴇʀᴍɪꜱꜱɪᴏɴ ꜰʀᴏᴍ ᴛʜᴇ ᴏᴡɴᴇʀ...</b>\n\nᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ.")

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
            bot_mention = f"[{bot_info.first_name}](tg://user?id={bot_info.id})"
            
            await save_clone(bot_token, user_id, username)
            CLONES.add(bot_token)
            
            details = f"""
<b>✅ 𝗖𝗹𝗼𝗻𝗲 𝗕𝗼𝘁 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 𝗰𝗿𝗲𝗮𝘁𝗲𝗱.</b>

<b>🤖 𝘽𝙤𝙩 𝙉𝙖𝙢𝙚 : </b> {bot_mention}
<b>🔗 𝙐𝙨𝙚𝙣𝙖𝙢𝙚 : </b> @{username}

<i>ᴛᴏ ʟɪꜱᴛᴇɴ ᴛᴏ ᴍᴜꜱɪᴄ, ᴀᴅᴅ ʏᴏᴜʀ ᴄʟᴏɴᴇ ʙᴏᴛ ᴛᴏ ᴛʜᴇ ɢʀᴏᴜᴘ ᴀɴᴅ ɢɪᴠᴇ ɪᴛ ᴀᴅᴍɪɴ ꜱᴛᴀᴛᴜꜱ.</i>
"""
            await msg.edit_text(details)
            
        except AccessTokenInvalid:
            await msg.edit_text("❌ ɪɴᴠᴀʟɪᴅ ʙᴏᴛ ᴛᴏᴋᴇɴ.")
        except Exception as e:
            await msg.edit_text(f"❌ ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ: {e}")
        
    except Exception as e:
        await message.reply_text(f"❌ Unexpected error: {e}")

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
                return await message.reply_text("ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀ ᴄʟᴏɴᴇ ʙᴏᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ.")

        if token:
            await delete_clone(token)
            if token in CLONES:
                CLONES.remove(token)
            await message.reply_text("✅ ᴄʟᴏɴᴇ ʙᴏᴛ ʜᴀꜱ ʙᴇᴇɴ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴜɴɪɴꜱᴛᴀʟʟᴇᴅ.")
        else:
            await message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ᴛᴏᴋᴇɴ ᴏʀ ɴᴏ ᴄʟᴏɴᴇ ʙᴏᴛ ꜰᴏᴜɴᴅ.")
        
    except Exception as e:
        await message.reply_text(f"ᴇʀʀᴏʀ : {e}")

# --- (၁) OWNER ONLY: Clone Bot အရေအတွက် ကြည့်ခြင်း ---
@app.on_message(filters.command("checkbot") & filters.user(OWNER_ID))
async def total_clones_stats(client, message: Message):
    try:
        from maythusharmusic.utils.database import get_clones
        clones = await get_clones()
        
        total = len(clones)
        text = f"📊 <b>𝗖𝗹𝗼𝗻𝗲 𝗕𝗼𝘁 𝗦𝘁𝗮𝘁𝗶𝘀𝘁𝗶𝗰𝘀</b>\n\n"
        text += f"🤖 <b>𝗧𝗼𝘁𝗮𝗹 𝗖𝗹𝗼𝗻𝗲𝘀 : </b> {total}\n\n"
        
        if total > 0:
            text += "<b>𝗕𝗼𝘁 𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲𝘀 : </b>\n"
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
                "𝗪𝗮𝗿𝗻𝗶𝗻𝗴\n"
                "𝗔𝗿𝗲 𝘆𝗼𝘂 𝘀𝘂𝗿𝗲 𝘆𝗼𝘂 𝘄𝗮𝗻𝘁 𝘁𝗼 𝗱𝗲𝗹𝗲𝘁𝗲 𝗮𝗹𝗹 𝗖𝗹𝗼𝗻𝗲 𝗕𝗼𝘁𝘀.\n"
                "𝙄𝙛 𝙮𝙤𝙪 𝙖𝙧𝙚 𝙨𝙪𝙧𝙚, 𝙩𝙮𝙥𝙚 𝙩𝙝𝙚 𝙛𝙤𝙡𝙡𝙤𝙬𝙞𝙣𝙜 :\n"
                "<code>/delallclones confirm</code>"
            )
            
        msg = await message.reply_text("♻️ <b>𝘼𝙡𝙡 𝘾𝙡𝙤𝙣𝙚 𝘽𝙤𝙩𝙨 𝙖𝙧𝙚 𝙗𝙚𝙞𝙣𝙜 𝙙𝙚𝙡𝙚𝙩𝙚𝙙...</b>")
        
        # Database ရှင်းလင်းခြင်း
        await remove_all_clones()
        CLONES.clear()
        
        await msg.edit_text("✅ <b>𝘼𝙡𝙡 𝘾𝙡𝙤𝙣𝙚 𝘽𝙤𝙩𝙨 𝙝𝙖𝙫𝙚 𝙗𝙚𝙚𝙣 𝙨𝙪𝙘𝙘𝙚𝙨𝙨𝙛𝙪𝙡𝙡𝙮 𝙙𝙚𝙡𝙚𝙩𝙚𝙙 𝙛𝙧𝙤𝙢 𝙩𝙝𝙚 𝘿𝙖𝙩𝙖𝙗𝙖𝙨𝙚.</b>\n\n𝙍𝙚𝙨𝙩𝙖𝙧𝙩 𝙩𝙝𝙚 𝙗𝙤𝙩 𝙛𝙤𝙧 𝙩𝙝𝙚 𝙚𝙛𝙛𝙚𝙘𝙩 𝙩𝙤 𝙩𝙖𝙠𝙚 𝙚𝙛𝙛𝙚𝙘𝙩. (/reboot)")
        
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
                print(f"𝗦𝘁𝗮𝗿𝘁𝗲𝗱 𝗖𝗹𝗼𝗻𝗲 : @{clone['bot_username']}")
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
            await message.reply_text("✅ <b>𝘾𝙡𝙤𝙣𝙚 𝘽𝙤𝙩 𝙎𝙮𝙨𝙩𝙚𝙢 𝙝𝙖𝙨 𝙗𝙚𝙚𝙗 𝙖𝙘𝙩𝙞𝙫𝙖𝙩𝙚𝙙.</b>\n𝘼𝙡𝙡 𝘾𝙡𝙤𝙣𝙚 𝘽𝙤𝙩𝙨 𝙬𝙞𝙡𝙡 𝙧𝙚𝙨𝙪𝙢𝙚 𝙣𝙤𝙧𝙢𝙖𝙡 𝙤𝙥𝙚𝙧𝙖𝙩𝙞𝙤𝙣.")
            
        elif state == "off" or state == "disable":
            await set_clones_active(False)
            await message.reply_text("❌ <b>𝙏𝙝𝙚 𝘾𝙡𝙤𝙣𝙚 𝘽𝙤𝙩 𝙎𝙮𝙨𝙩𝙚𝙢 𝙝𝙖𝙨 𝙗𝙚𝙚𝙣 𝙙𝙞𝙨𝙖𝙗𝙡𝙚𝙙.</b>\n𝘼𝙡𝙡 𝘾𝙡𝙤𝙣𝙚 𝘽𝙤𝙩𝙨 𝙬𝙞𝙡𝙡 𝙨𝙝𝙤𝙬 '𝙐𝙣𝙙𝙚𝙧 𝙈𝙖𝙞𝙣𝙩𝙚𝙣𝙖𝙣𝙘𝙚'.")
            
        else:
            await message.reply_text("<b>Usage:</b> <code>/clonebot [on|off]</code>")
            
    except Exception as e:
        await message.reply_text(f"Error: {e}")
