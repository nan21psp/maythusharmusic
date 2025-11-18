import asyncio
import os
from pyrogram import Client
from telethon import TelegramClient

# Logger ကို import လုပ်ပါ
from maythusharmusic.logging import LOGGER

# --- Core Class တွေကို Import လုပ်ပါ ---
# (Instance တွေ မဟုတ်ဘဲ Class တွေကိုပဲ ခေါ်ထားပါ)
from .core.bot import Hotty
from .core.userbot import Userbot
from .core.call import Hotty as Pytgcalls # Pytgcalls instance (Hotty = Call())
from .core.youtube import YouTubeAPI

import config

# --- Telethon Client ---
# (ဒါက asyncio loop မစခင် ကြေညာလို့ရပါတယ်)
telethn = TelegramClient("maythushar", config.API_ID, config.API_HASH)

# --- (RuntimeError Fix နှင့် Clone Bot အတွက် ပြင်ဆင်ချက်) ---
# Pyrogram Client instance တွေကို ဒီမှာ မဆောက်တော့ပါဘူး။
# __main__.py ထဲမှာ asyncio.run() ခေါ်ပြီးမှ ဆောက်ပါမယ်။

app = []      # 🟢 Clone Bot စနစ်အတွက် list အလွတ် အဖြစ် ကြေညာပါ
userbot = None  # 🟢 __main__.py မှာမှ instance ဆောက်ဖို့ None ထားပါ

# --- Helpers ---
# (ဒါတွေက Client မဟုတ်လို့ ဒီမှာ ဆောက်လို့ရပါတယ်)
from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()
