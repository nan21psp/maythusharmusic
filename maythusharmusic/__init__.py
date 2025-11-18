# maythusharmusic/__init__.py (ပြင်ဆင်ပြီး)

import asyncio
import os
from pyrogram import Client
from telethon import TelegramClient

from maythusharmusic.logging import LOGGER
import config

# --- (၁) Helper တွေနဲ့ Variable တွေကို အရင် ကြေညာပါ ---

# (Circular Import Error ဖြေရှင်းရန်)
# YouTube helper ကို အရင်ဆုံး instance ဆောက်ပါ
from .platforms import *
YouTube = YouTubeAPI()

# Bot client တွေ ထည့်မယ့် list
app = []
userbot = None  # Assistant (None)

# Telethon client
telethn = TelegramClient("maythushar", config.API_ID, config.API_HASH)


# --- (၂) Core Class/Instance တွေကို အခုမှ Import လုပ်ပါ ---
# (ဒီ module တွေက အပေါ်က 'app', 'YouTube' တွေကို ပြန် import လုပ်နိုင်ပါပြီ)

from .core.bot import Hotty          # Main Bot Class
from .core.userbot import Userbot      # Assistant Class
from .core.call import Hotty as Pytgcalls # Call Instance (Call())
