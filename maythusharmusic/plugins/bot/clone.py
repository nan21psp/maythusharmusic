# maythusharmusic/plugins/bot/clone.py

import re
import logging
import traceback
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import AccessTokenInvalid

from config import API_ID, API_HASH, OWNER_ID
from maythusharmusic import app

# Clone Bot များကို ယာယီမှတ်ထားရန်
CLONES = set()
# ခွင့်ပြုချက်တောင်းခံမှုများကို ယာယီမှတ်ထားရန်
PENDING_REQUESTS = {}

@app.on_message(filters.command("clone") & filters.private)
async def clone_txt(client, message: Message):
    try:
        # Database function များ import
        try:
            from maythusharmusic.utils.database import save_clone, get_clone_by_user
        except ImportError:
            return await message.reply_text("❌ ᴅᴀᴛᴀʙᴀꜱᴇ ᴇʀʀᴏʀ: ᴅᴀᴛᴀʙᴀꜱᴇ.ᴘʏ ᴅᴏᴇꜱ ɴᴏᴛ ᴄᴏɴᴛᴀɪɴ ꜱᴀᴠᴇ_ᴄʟᴏɴᴇ, ɢᴇᴛ_ᴄʟᴏɴᴇ_ʙʏ_ᴜꜱᴇʀ.")

        # --- (၁) ONE USER ONE BOT LIMIT CHECK ---
        user_id = message.from_user.id
        existing_clone = await get_clone_by_user(user_id)
        
        if existing_clone:
            bot_username = existing_clone.get("bot_username", "Unknown")
            bot_token = existing_clone.get("bot_token", "")
            return await message.reply_text(
                f"⚠️ <b>𝗡𝗼𝘁𝗶𝗰 𝗙𝗼𝗿 𝗨𝘀𝗲𝗿𝘀!</b>\n\n"
                f"𝙔𝙤𝙪 𝙖𝙡𝙧𝙚𝙖𝙙𝙮 𝙝𝙖𝙫𝙚 𝙖 𝘾𝙡𝙤𝙣𝙚 𝘽𝙤𝙩.\n"
                f"🤖 <b>Bot:</b> @{bot_username}\n\n"
                f"𝙄𝙛 𝙮𝙤𝙪 𝙬𝙖𝙣𝙩 𝙩𝙤 𝙘𝙧𝙚𝙖𝙩𝙚 𝙖 𝙣𝙚𝙬 𝙤𝙣𝙚, 𝙙𝙚𝙡𝙚𝙩𝙚 𝙩𝙝𝙚 𝙚𝙭𝙞𝙨𝙩𝙞𝙣𝙜 𝘽𝙤𝙩 𝙛𝙞𝙧𝙨𝙩.\n"
                f"<code>/delclone {bot_token}</code>"
            )
        # ----------------------------------------

        if len(message.command) < 2:
            return await message.reply_text(
                "<b>D͟e͟v͟e͟l͟o͟p͟e͟r͟ : @iwillgoforwardsalone</b>\n\n/clone [Bot Token]\n\nGᴇᴛ ʙᴏᴛ ᴛᴏᴋᴇɴ ꜰʀᴏᴍ @BotFather"
            )
        
        bot_token = message.text.split(None, 1)[1]
        
        # Token Format စစ်ဆေးခြင်း
        if not re.match(r'^\d+:[a-zA-Z0-9_-]+$', bot_token):
            return await message.reply_text("❌ 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗕𝗼𝘁 𝗧𝗼𝗸𝗲𝗻.")

        # User ကို စောင့်ခိုင်းခြင်း
        msg = await message.reply_text("🫧 <b>ʀᴇQᴜᴇꜱᴛɪɴɢ ᴘᴇʀᴍɪꜱꜱɪᴏɴ ꜰʀᴏᴍ ᴛʜᴇ ᴏᴡɴᴇʀ...</b>\n\nᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ.")

        # Owner ထံ ခွင့်ပြုချက်တောင်းခြင်း
        mention = message.from_user.mention

        # Request ကို ယာယီမှတ်ထားမည်
        PENDING_REQUESTS[user_id] = {
            "token": bot_token,
            "msg_id": msg.id
        }

        try:
            await app.send_message(
                OWNER_ID,
                f"👤 <b>ᴄʟᴏɴᴇ ʙᴏᴛ ʀᴇQᴜᴇꜱᴛ</b>\n\n"
                f"<b>ᴜꜱᴇʀ:</b> {mention} (`{user_id}`)\n"
                f"<b>ᴛᴏᴋᴇɴ:</b> `{bot_token}`\n\n"
                f"ᴀʟʟᴏᴡ ᴛʜɪꜱ ᴜꜱᴇʀ ᴛᴏ ᴄʀᴇᴀᴛᴇ ᴀ ᴄʟᴏɴᴇ ʙᴏᴛ?",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ ခွင့်ပြုမည်", callback_data=f"CLONE_DECISION|APPROVE|{user_id}"),
                        InlineKeyboardButton("❌ ငြင်းပယ်မည်", callback_data=f"CLONE_DECISION|DECLINE|{user_id}")
                    ]
                ])
            )
        except Exception as e:
            await msg.edit_text(f"❌ ᴜɴᴀʙʟᴇ ᴛᴏ ꜱᴇɴᴅ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ ᴏᴡɴᴇʀ (ᴏᴡɴᴇʀ ɪᴅ ɪꜱ ɪɴᴄᴏʀʀᴇᴄᴛ ᴏʀ ʙᴏᴛ ɪꜱ ʙʟᴏᴄᴋᴇᴅ).\nError: {e}")

    except Exception as e:
        err_text = traceback.format_exc()
        await message.reply_text(f"🐞 <b>Error:</b>\n`{err_text}`")


# Owner ၏ ဆုံးဖြတ်ချက်ကို ကိုင်တွယ်ခြင်း
@app.on_callback_query(filters.regex("CLONE_DECISION"))
async def clone_decision_handler(client, query: CallbackQuery):
    if query.from_user.id != OWNER_ID:
        return await query.answer("ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴛʜᴇ ᴏᴡɴᴇʀ.", show_alert=True)

    data = query.data.split("|")
    decision = data[1]
    user_id = int(data[2])

    if user_id not in PENDING_REQUESTS:
        return await query.answer("⚠️ 𝗧𝗵𝗶𝘀 𝗿𝗲𝗾𝘂𝗲𝘀𝘁 𝗵𝗮𝘀 𝗲𝘅𝗽𝗶𝗿𝗲𝗱.", show_alert=True)

    request_data = PENDING_REQUESTS[user_id]
    bot_token = request_data["token"]
    
    try:
        from maythusharmusic.utils.database import save_clone
    except ImportError:
        return await query.answer("Database Error", show_alert=True)

    if decision == "DECLINE":
        await query.message.edit_text(f"❌ 𝗨𝘀𝗲𝗿'𝘀 {user_id} 𝗰𝗹𝗼𝗻𝗲 𝗿𝗲𝗾𝘂𝗲𝘀𝘁 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗿𝗲𝗷𝗲𝗰𝘁𝗲𝗱.")
        await app.send_message(user_id, "❌ <b>𝙎𝙤𝙧𝙧𝙮, 𝙮𝙤𝙪𝙧 𝙥𝙚𝙧𝙢𝙞𝙨𝙨𝙞𝙤𝙣 𝙩𝙤 𝙘𝙧𝙚𝙖𝙩𝙚 𝙖 𝘾𝙡𝙤𝙣𝙚 𝘽𝙤𝙩 𝙝𝙖𝙨 𝙗𝙚𝙚𝙣 𝙙𝙚𝙣𝙞𝙚𝙙 𝙗𝙮 𝙩𝙝𝙚 𝙊𝙬𝙣𝙚𝙧.</b>")
        del PENDING_REQUESTS[user_id]
        
    elif decision == "APPROVE":
        await query.message.edit_text(f"✅ 𝗨𝘀𝗲𝗿'𝘀 {user_id} 𝗖𝗹𝗼𝗻𝗲 𝗥𝗲𝗾𝘂𝗲𝘀𝘁 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗮𝗰𝗰𝗲𝗽𝘁𝗲𝗱.\n𝘾𝙧𝙚𝙖𝙩𝙞𝙣𝙜 𝙗𝙤𝙩...")
        status_msg = await app.send_message(user_id, "✅ <b>𝗣𝗲𝗿𝗺𝗶𝘀𝘀𝗶𝗼𝗻 𝗴𝗿𝗮𝗻𝘁𝗲𝗱 𝗯𝘆 𝘁𝗵𝗲 𝗼𝘄𝗻𝗲𝗿.</b>\n♻️ 𝘾𝙧𝙚𝙖𝙩𝙞𝙣𝙜 𝘾𝙡𝙤𝙣𝙚 𝘽𝙤𝙩...")

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
            
            # Database တွင် သိမ်းဆည်းခြင်း
            await save_clone(bot_token, user_id, username)
            CLONES.add(bot_token)
            
            details = f"""
<b>✅ 𝗖𝗹𝗼𝗻𝗲 𝗕𝗼𝘁 𝘀𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 𝗰𝗿𝗲𝗮𝘁𝗲𝗱.</b>

<b>🤖 Bot Name:</b> {bot_info.first_name}
<b>🔗 Username:</b> @{username}

<i>ᴛᴏ ʟɪꜱᴛᴇɴ ᴛᴏ ᴍᴜꜱɪᴄ, ᴀᴅᴅ ʏᴏᴜʀ ᴄʟᴏɴᴇ ʙᴏᴛ ᴛᴏ ᴛʜᴇ ɢʀᴏᴜᴘ ᴀɴᴅ ɢɪᴠᴇ ɪᴛ ᴀᴅᴍɪɴ ꜱᴛᴀᴛᴜꜱ.</i>
"""
            await status_msg.edit_text(details)
            await query.message.reply_text(f"✅ @{username} ʀᴜɴ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ...")
            
        except AccessTokenInvalid:
            await status_msg.edit_text("❌ ɪɴᴠᴀʟɪᴅ ʙᴏᴛ ᴛᴏᴋᴇɴ.")
            await query.message.reply_text("❌ ᴛʜᴇ ᴛᴏᴋᴇɴ ᴘʀᴏᴠɪᴅᴇᴅ ʙʏ ᴛʜᴇ ᴜꜱᴇʀ ɪꜱ ɪɴᴠᴀʟɪᴅ ᴀɴᴅ ꜰᴀɪʟᴇᴅ.")
        except Exception as e:
            await status_msg.edit_text(f"❌ ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ: {e}")
            await query.message.reply_text(f"❌ Error: {e}")
        
        del PENDING_REQUESTS[user_id]


@app.on_message(filters.command("delclone") & filters.private)
async def delete_clone_bot(client, message: Message):
    try:
        from maythusharmusic.utils.database import delete_clone, get_clone_by_user
        
        token = None
        
        # Token ပါမပါ စစ်ဆေးခြင်း
        if len(message.command) >= 2:
            token = message.text.split(None, 1)[1]
        else:
            # Token မပါရင် User ရဲ့ Bot ကို Auto ရှာဖျက်မယ်
            user_clone = await get_clone_by_user(message.from_user.id)
            if user_clone:
                token = user_clone.get("bot_token")
            else:
                return await message.reply_text("ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀ ᴄʟᴏɴᴇ ʙᴏᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ.")

        await delete_clone(token)
        await message.reply_text("✅ ᴄʟᴏɴᴇ ʙᴏᴛ ʜᴀꜱ ʙᴇᴇɴ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴄᴀɴᴄᴇʟᴇᴅ.\nɴᴏᴡ ʏᴏᴜ ᴄᴀɴ ᴍᴀᴋᴇ ᴀ ɴᴇᴡ ᴏɴᴇ.")
        
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
