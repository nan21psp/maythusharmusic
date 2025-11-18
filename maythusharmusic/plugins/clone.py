import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import (
    ApiIdInvalid, 
    AuthKeyUnregistered, 
    UserDeactivated, 
    SessionPasswordNeeded
)

import config
from maythusharmusic import app
from maythusharmusic.utils.database.clonedb import (
    save_clone_token, 
    save_clonebot_owner, 
    save_clonebot_username,
    get_clonebot_owner # Bot ရှိပြီးသားလား စစ်ဖို့
)

# User တစ်ယောက်ချင်းစီရဲ့ state ကို ခဏမှတ်ထားဖို့
user_states = {}

@app.on_message(filters.command("clone") & filters.private & ~filters.forwarded)
async def clone_bot(client, message: Message):
    user_id = message.from_user.id
    
    # --- (လုံခြုံရေး) Bot Owner (SUDOERS) များကိုသာ ခွင့်ပြုပါ ---
    if user_id not in config.SUDOERS:
        return await message.reply_text(
            "Bot Clone ပြုလုပ်ခြင်းသည် Bot Owner များအတွက်သာ သီးသန့်ဖြစ်ပါသည်။"
        )
        
    # --- State ကို သတ်မှတ်ပြီး token တောင်းပါ ---
    user_states[user_id] = "awaiting_token"
    await message.reply_text(
        "**Bot Clone ပြုလုပ်ရန်:**\n\n"
        "1. @BotFather သို့ သွားပါ။\n"
        "2. `/newbot` command ကို သုံးပြီး bot အသစ်တစ်ခု ဖန်တီးပါ။\n"
        "3. BotFather က ပြန်ပေးလိုက်တဲ့ **HTTP API Token** ကို copy ယူပါ။\n"
        "4. ထို token ကို ဒီမှာ လာထည့်ပါ (forward မလုပ်ပါနဲ့)။"
    )

@app.on_message(filters.text & filters.private & ~filters.forwarded & ~filters.command("clone"))
async def receive_token(client, message: Message):
    user_id = message.from_user.id
    
    # User က token ပို့ဖို့ စောင့်နေတဲ့ state ဟုတ်မဟုတ် စစ်ပါ
    if user_states.get(user_id) == "awaiting_token":
        bot_token = message.text.strip()
        
        # State ကို ရှင်းလင်းပါ
        user_states.pop(user_id, None)
        
        # Token format မှန်မမှန် အကြမ်းဖျင်း စစ်ပါ
        if ":" not in bot_token:
            return await message.reply_text("ပို့လိုက်သော Token ပုံစံ မှားယွင်းနေပါသည်။")

        checking_msg = await message.reply_text("🔍 Token ကို စစ်ဆေးနေပါသည်... ခဏစောင့်ပါ။")

        # --- Token အလုပ်လုပ်မလုပ် စမ်းသပ်ပါ ---
        temp_client = Client(
            name=f"temp_clone_{user_id}",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=bot_token,
            in_memory=True # Session file မဆောက်ဘဲ memory ထဲမှာပဲ run မယ်
        )
        
        try:
            await temp_client.start()
            bot_info = await temp_client.get_me()
            bot_id = bot_info.id
            bot_username = bot_info.username
            
            # Bot ကို ရပ်လိုက်ပါ
            await temp_client.stop()
            
            # --- Bot ရှိပြီးသားလား စစ်ပါ ---
            existing_owner = await get_clonebot_owner(bot_id)
            if existing_owner:
                if existing_owner == user_id:
                    return await checking_msg.edit_text(
                        f"သင်သည် @{bot_username} ကို clone ပြုလုပ်ပြီးသား ဖြစ်ပါသည်။"
                    )
                else:
                    return await checking_msg.edit_text(
                        f"@{bot_username} bot ကို အခြားတစ်ယောက်မှ clone ပြုလုပ်ထားပြီး ဖြစ်ပါသည်။"
                    )

            # --- အောင်မြင်ရင် Database ထဲ သိမ်းပါ ---
            await save_clonebot_owner(bot_id, user_id)
            await save_clonebot_username(bot_id, bot_username)
            await save_clone_token(bot_id, bot_token)
            
            await checking_msg.edit_text(
                f"✅ အောင်မြင်ပါသည်။\n\n"
                f"သင်၏ bot **@{bot_username}** ကို clone ပြုလုပ်ပြီးပါပြီ။\n"
                f"ကျေးဇူးပြု၍ သင့် bot (@{bot_username}) ကို Group များတွင် Admin အဖြစ် ထည့်သွင်း အသုံးပြုနိုင်ပါပြီ။"
            )

        except (ApiIdInvalid, AuthKeyUnregistered, UserDeactivated) as e:
            await checking_msg.edit_text(f"❌ Token မှားယွင်းနေပါသည်။\n\n**Error:** `{e}`")
        except SessionPasswordNeeded:
            await checking_msg.edit_text("❌ ဤ bot token သည် 2-Step Verification ဖြင့် ကာကွယ်ထားပြီး၊ clone ပြုလုပ်၍ မရပါ။")
        except Exception as e:
            await checking_msg.edit_text(f"❌ Bot ကို စတင်ရာတွင် အမှားဖြစ်ပွားပါသည်:\n\n`{e}`")
