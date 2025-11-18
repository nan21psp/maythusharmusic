import asyncio
import importlib
from pyrogram import Client, idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
from maythusharmusic import (
    LOGGER, 
    app,            # __init__.py ထဲက list အလွတ်
    userbot as userbot_global, # __init__.py ထဲက None
    Hotty,          # __init__.py ထဲက Hotty (Client) Class
    Userbot,        # __init__.py ထဲက Userbot (Assistant) Class
    Pytgcalls       # __init__.py ထဲက Pytgcalls (Call) instance
)
from maythusharmusic.misc import sudo
from maythusharmusic.plugins import ALL_MODULES
from maythusharmusic.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS

# (Clone Bot အတွက် DB function တွေ import လုပ်ပါ)
from maythusharmusic.utils.database.clonedb import (
    get_all_clones, 
    get_clone_token
)

# (Global variable တွေကို __main__ မှာ ပြန်သတ်မှတ်ပါ)
userbot = None

async def init():
    global app, userbot

    if (
        not config.STRING1
        and not config.STRING2
        and not config.STRING3
        and not config.STRING4
        and not config.STRING5
    ):
        LOGGER(__name__).error("Assistant client variables not defined, exiting...")
        exit()

    await sudo()
    
    # --- (၁) Main Bot Instance ကို ဖန်တီးပါ ---
    main_bot_client = Hotty()
    app.append(main_bot_client) # __init__ က app list ထဲ ထည့်ပါ
    
    # --- (၂) Clone Bot Instance များကို ဖန်တီးပါ ---
    clones = await get_all_clones()
    LOGGER(__name__).info(f"Found {len(clones)} clone bots in database.")
    
    for clone in clones:
        bot_id = clone["bot_id"]
        bot_token = await get_clone_token(bot_id)
        if not bot_token:
            LOGGER(__name__).error(f"Token not found for clone {bot_id}. Skipping.")
            continue
        
        try:
            # (မှတ်ချက်: Hotty class က config.BOT_TOKEN ကို တိုက်ရိုက်သုံးထားလို့၊
            # Clone bot တွေအတွက် သီးသန့် Client instance ပဲ ဆောက်ရပါမယ်)
            clone_client = Client(
                name=f"clone_{bot_id}",
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                bot_token=bot_token,
                in_memory=True
            )
            app.append(clone_client) # __init__ က app list ထဲ ထည့်ပါ
            LOGGER(__name__).info(f"Successfully loaded clone bot: {bot_id}")
        except Exception as e:
            LOGGER(__name__).error(f"Failed to load clone {bot_id}: {e}")

    # --- (၃) Assistant (Userbot) Instance ကို ဖန်တီးပါ ---
    userbot = Userbot()
    # (Global variable ကို update လုပ်ပါ)
    globals()["userbot_global"] = userbot

    # --- (၄) Plugin များကို Import လုပ်ပါ (အရေးကြီး) ---
    # Client တွေအားလုံး app list ထဲ ရောက်ရှိပြီးမှ Plugin တွေကို import လုပ်ရပါမယ်။
    # ဒါမှ @app.on_message က client အားလုံး (main + clones) မှာ အလုပ်လုပ်ပါမယ်။
    for all_module in ALL_MODULES:
        importlib.import_module("maythusharmusic.plugins" + all_module)
    LOGGER("maythusharmusic.plugins").info("Successfully Imported Modules for ALL Clients...")

    # --- (၅) Banned Users များကို Load လုပ်ပါ ---
    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)
        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except:
        pass

    # --- (၆) Bot Client အားလုံးကို Start ပါ ---
    LOGGER(__name__).info(f"Starting {len(app)} bot clients...")
    for client in app:
        await client.start()
    LOGGER(__name__).info("All bot clients started.")
    
    # --- (၇) Assistant များကို Start ပါ ---
    await userbot.start()
    
    # --- (၈) Pytgcalls ကို Start ပါ ---
    await Pytgcalls.start()
    
    # (ကျန်ရှိသော မူလ __main__ code များ)
    try:
        await Pytgcalls.stream_call("https://graph.org/file/e999c40cb700e7c684b75.mp4")
    except NoActiveGroupCall:
        LOGGER("maythusharmusic").error(
            "Please turn on the videochat of your log group/channel.\n\nStopping Bot..."
        )
        exit()
    except:
        pass
    await Pytgcalls.decorators()
    LOGGER("maythusharmusic").info(
        "ᴅʀᴏᴘ ʏᴏᴜʀ ɢɪʀʟꜰʀɪᴇɴᴅ'ꜱ ɴᴜᴍʙᴇʀ ᴀᴛ @sasukevipmusicbotsupport ᴊᴏɪɴ @sasukevipmusicbot , @sasukevipmusicbotsupport ꜰᴏʀ ᴀɴʏ ɪꜱꜱᴜꜱ"
    )
    
    # --- (Cache Pre-load) ---
    LOGGER(__name__).info("ယာယီမှတ်ဉာဏ် (In-Memory Cache) ကို ကြိုတင်ဖြည့်နေပါသည်...")
    try:
        # YouTube cache အတွက် import လုပ်ပါ
        from maythusharmusic.utils.yt_utils import YouTube
        await YouTube.load_cache() 
    except Exception as e:
        LOGGER(__name__).error(f"YouTube Cache ကို ကြိုတင်ဖြည့်ရာတွင် မအောင်မြင်ပါ: {e}")
    
    await idle()
    
    # --- (Stop Logic) ---
    LOGGER("maythusharmusic").info("Stopping Sasuke Music Bot...")
    for client in app:
        await client.stop()
    await userbot.stop()


if __name__ == "__main__":
    # Python 3.11 အတွက် asyncio event loop အသုံးပြုခြင်း
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(init())
    except KeyboardInterrupt:
        LOGGER("maythusharmusic").info("Process stopped manually.")
    finally:
        loop.close()
