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
            return await message.reply_text("❌ Database Error: database.py တွင် save_clone, get_clone_by_user မရှိပါ။")

        # --- (၁) ONE USER ONE BOT LIMIT CHECK ---
        user_id = message.from_user.id
        existing_clone = await get_clone_by_user(user_id)
        
        if existing_clone:
            bot_username = existing_clone.get("bot_username", "Unknown")
            bot_token = existing_clone.get("bot_token", "")
            return await message.reply_text(
                f"⚠️ <b>ကန့်သတ်ချက်!</b>\n\n"
                f"သင့်တွင် Clone Bot တစ်ခု ရှိပြီးသား ဖြစ်နေပါသည်။\n"
                f"🤖 <b>Bot:</b> @{bot_username}\n\n"
                f"နောက်တစ်ခု အသစ်ထပ်လုပ်လိုပါက ရှိပြီးသား Bot ကို အရင်ဖျက်ပေးပါ:\n"
                f"<code>/delclone {bot_token}</code>"
            )
        # ----------------------------------------

        if len(message.command) < 2:
            return await message.reply_text(
                "<b>D͟e͟v͟e͟l͟o͟p͟e͟r͟ : @iwillgoforwardsalone</b>\n\n/clone [Bot Token]\n\nBot Token ကို @BotFather ထံမှ ရယူပါ။"
            )
        
        bot_token = message.text.split(None, 1)[1]
        
        # Token Format စစ်ဆေးခြင်း
        if not re.match(r'^\d+:[a-zA-Z0-9_-]+$', bot_token):
            return await message.reply_text("❌ မှားယွင်းသော Bot Token ဖြစ်ပါသည်။")

        # User ကို စောင့်ခိုင်းခြင်း
        msg = await message.reply_text("⏳ <b>Owner ထံ ခွင့်ပြုချက် တောင်းခံနေပါသည်...</b>\n\nကျေးဇူးပြု၍ စောင့်ဆိုင်းပါ။")

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
                f"👤 <b>Clone Bot Request</b>\n\n"
                f"<b>User:</b> {mention} (`{user_id}`)\n"
                f"<b>Token:</b> `{bot_token}`\n\n"
                f"ဒီ User ကို Clone Bot ဖန်တီးခွင့် ပေးမလား?",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ ခွင့်ပြုမည်", callback_data=f"CLONE_DECISION|APPROVE|{user_id}"),
                        InlineKeyboardButton("❌ ငြင်းပယ်မည်", callback_data=f"CLONE_DECISION|DECLINE|{user_id}")
                    ]
                ])
            )
        except Exception as e:
            await msg.edit_text(f"❌ Owner ထံ စာပို့မရပါ (Owner ID မှားနေခြင်း (သို့) Bot ကို Block ထားခြင်း)။\nError: {e}")

    except Exception as e:
        err_text = traceback.format_exc()
        await message.reply_text(f"🐞 <b>Error:</b>\n`{err_text}`")


# Owner ၏ ဆုံးဖြတ်ချက်ကို ကိုင်တွယ်ခြင်း
@app.on_callback_query(filters.regex("CLONE_DECISION"))
async def clone_decision_handler(client, query: CallbackQuery):
    if query.from_user.id != OWNER_ID:
        return await query.answer("သင်သည် Owner မဟုတ်ပါ။", show_alert=True)

    data = query.data.split("|")
    decision = data[1]
    user_id = int(data[2])

    if user_id not in PENDING_REQUESTS:
        return await query.answer("⚠️ ဤ Request သက်တမ်းကုန်သွားပါပြီ။", show_alert=True)

    request_data = PENDING_REQUESTS[user_id]
    bot_token = request_data["token"]
    
    try:
        from maythusharmusic.utils.database import save_clone
    except ImportError:
        return await query.answer("Database Error", show_alert=True)

    if decision == "DECLINE":
        await query.message.edit_text(f"❌ User {user_id} ၏ Clone Request ကို ငြင်းပယ်လိုက်ပါသည်။")
        await app.send_message(user_id, "❌ <b>စိတ်မကောင်းပါ၊ သင်၏ Clone Bot ဖန်တီးခွင့်ကို Owner မှ ငြင်းပယ်လိုက်ပါသည်။</b>")
        del PENDING_REQUESTS[user_id]
        
    elif decision == "APPROVE":
        await query.message.edit_text(f"✅ User {user_id} ၏ Clone Request ကို လက်ခံလိုက်ပါသည်။\nBot ဖန်တီးနေသည်...")
        status_msg = await app.send_message(user_id, "✅ <b>Owner မှ ခွင့်ပြုလိုက်ပါသည်။</b>\n♻️ Clone Bot ဖန်တီးနေပါသည်...")

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
<b>✅ Clone Bot အောင်မြင်စွာ ဖန်တီးပြီးပါပြီ!</b>

<b>🤖 Bot Name:</b> {bot_info.first_name}
<b>🔗 Username:</b> @{username}

<i>⚠️မှတ်ချက်: သီချင်းနားထောင်ရန် သင့် Clone Bot ကို Group ထဲထည့်ပြီး Admin ပေးထားပါ။</i>
"""
            await status_msg.edit_text(details)
            await query.message.reply_text(f"✅ @{username} အောင်မြင်စွာ Run ပါပြီ။")
            
        except AccessTokenInvalid:
            await status_msg.edit_text("❌ Bot Token မှားယွင်းနေပါသည်။")
            await query.message.reply_text("❌ User ပေးသော Token မှားနေသဖြင့် မအောင်မြင်ပါ။")
        except Exception as e:
            await status_msg.edit_text(f"❌ အမှားဖြစ်ပွားခဲ့သည်: {e}")
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
                return await message.reply_text("⚠️ မိတ်ဆွေတွင် ဖျက်စရာ Clone Bot မရှိပါ။")

        await delete_clone(token)
        await message.reply_text("✅ Clone Bot ကို အောင်မြင်စွာ ဖျက်သိမ်းလိုက်ပါပြီ။\nယခု အသစ်တစ်ခု ထပ်လုပ်နိုင်ပါပြီ။")
        
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
