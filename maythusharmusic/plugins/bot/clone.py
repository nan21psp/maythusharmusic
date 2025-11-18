# maythusharmusic/plugins/bot/clone.py

import re
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import AccessTokenInvalid

from config import API_ID, API_HASH
from maythusharmusic import app

# Clone Bot များကို ယာယီမှတ်ထားရန်
CLONES = set()

@app.on_message(filters.command("clone") & filters.private)
async def clone_txt(client, message: Message):
    # Database function များကို ဤနေရာမှ ခေါ်သုံးမှ Import Error မတက်မည်
    try:
        from maythusharmusic.utils.database import save_clone
    except ImportError:
        return await message.reply_text("❌ Database Error: database.py တွင် save_clone function မရှိပါ။")

    if len(message.command) < 2:
        return await message.reply_text(
            "<b>အသုံးပြုပုံ :</b>\n\n/clone [Bot Token]\n\nBot Token ကို @BotFather ထံမှ ရယူပါ။"
        )
    
    bot_token = message.text.split(None, 1)[1]
    
    # Token Format စစ်ဆေးခြင်း (နံပါတ်များ:စာသားများ)
    if not re.match(r'^\d+:[a-zA-Z0-9_-]+$', bot_token):
        return await message.reply_text("❌ မှားယွင်းသော Bot Token ဖြစ်ပါသည်။")

    msg = await message.reply_text("♻️ Clone Bot ဖန်တီးနေပါသည်... ခေတ္တစောင့်ပါ...")

    try:
        # Clone Client စမ်းသပ်ခြင်း
        ai = Client(
            name=bot_token,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=bot_token,
            plugins=dict(root="maythusharmusic.plugins"),
        )
        
        await ai.start()
        bot_info = await ai.get_me()
        username = bot_info.username
        
        # Database တွင် သိမ်းဆည်းခြင်း
        await save_clone(bot_token, message.from_user.id, username)
        CLONES.add(bot_token)
        
        details = f"""
<b>✅ Clone Bot အောင်မြင်စွာ ဖန်တီးပြီးပါပြီ!</b>

<b>🤖 Bot Name:</b> {bot_info.first_name}
<b>🔗 Username:</b> @{username}

<i>⚠️မှတ်ချက်: သီချင်းနားထောင်ရန် သင့် Clone Bot ကို Group ထဲထည့်ပြီး Admin ပေးထားပါ။</i>
"""
        await msg.edit_text(details)
        
    except AccessTokenInvalid:
        await msg.edit_text("❌ Bot Token မှားယွင်းနေပါသည်။ ကျေးဇူးပြု၍ ပြန်စစ်ဆေးပါ။")
    except Exception as e:
        await msg.edit_text(f"❌ အမှားဖြစ်ပွားခဲ့သည်: {e}")


@app.on_message(filters.command("delclone") & filters.private)
async def delete_clone_bot(client, message: Message):
    try:
        from maythusharmusic.utils.database import delete_clone
    except ImportError:
        return await message.reply_text("❌ Database Error")

    if len(message.command) < 2:
        return await message.reply_text("<b>အသုံးပြုပုံ :</b> /delclone [Bot Token]")
    
    token = message.text.split(None, 1)[1]
    await delete_clone(token)
    await message.reply_text("✅ Clone Bot ကို ဖျက်သိမ်းလိုက်ပါပြီ။")


async def restart_clones():
    # Bot စဖွင့်ချိန်တွင် Database မှ Clone များကို ပြန် run ပေးသည့် function
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
                    plugins=dict(root="maythusharmusic.plugins"),
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
