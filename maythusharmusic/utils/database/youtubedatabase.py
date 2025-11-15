# youtubedatabase.py
# YouTube.py အတွက် သီးသန့် database functions များ
# (core.mongo ကို မသုံးဘဲ connection အသစ် တည်ဆောက်ထားပါသည်)

import logging
from typing import Union

try:
    # MongoDB ကို async အဖြစ် ချိတ်ဆက်ရန် 'motor' ကို သုံးပါမည်
    from motor.motor_asyncio import AsyncIOMotorClient
except ImportError:
    # motor မရှိလျှင် bot ကို run လို့မရအောင် error ပေးပါ
    raise ImportError(
        "motor package ကို ရှာမတွေ့ပါ (pip install motor)"
    )

# --- (Logging ကို အသင့်ပြင်ထားပါ) ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- (User ပေးပို့လိုက်သော MongoDB URL အသစ်) ---
MONGO_URL = "mongodb+srv://wanglinmongodb:wanglin@cluster0.tny5vhz.mongodb.net/?retryWrites=true&w=majority"

# --- (Database Name) ---
# URL ထဲမှာ database name မပါတဲ့အတွက် 'youtubedb' လို့ နာမည်သစ် ပေးလိုက်ပါမယ်။
# ဒီ database ထဲမှာ collection ၃ ခု အသစ် ဆောက်ပါလိမ့်မယ်။
DATABASE_NAME = "youtubedb" 

try:
    # --- (Connection အသစ် တည်ဆောက်ခြင်း) ---
    
    # 1. Client ကို ချိတ်ဆက်ပါ
    _mongo_client = AsyncIOMotorClient(MONGO_URL)
    
    # 2. Database ကို သတ်မှတ်ပါ
    mongodb = _mongo_client[DATABASE_NAME]
    
    logger.info(f"Connecting to new MongoDB for YouTube Cache: {DATABASE_NAME}")

    # --- (YouTube.py က သုံးမယ့် Collection များကို သတ်မှတ်ပါ) ---
    
    # 1. onoffdb (youtube.py ထဲက 'is_on_off' function အတွက်)
    onoffdb = mongodb.onoffper
    
    # 2. Search Result Cache (သီချင်းအချက်အလက်)
    ytcache_db = mongodb.ytcache
    
    # 3. Downloaded File Path Cache
    songfiles_db = mongodb.songfiles
    
    logger.info("New YouTube Database collections initialized successfully.")

except Exception as e:
    logger.critical(f"MongoDB connection အသစ် ({MONGO_URL}) ကို ချိတ်ဆက်ရာတွင် အမှားဖြစ်ပွားပါသည်: {e}")
    # Bot ဆက် run လို့မရအောင် error ပစ်ပါ
    raise ConnectionError(f"YouTube Database connection failed: {e}") from e


# ---------------------------------------------------------------------
# --- (youtube.py က ခေါ်သုံးမည့် Function (၆) ခု) ---
# ---------------------------------------------------------------------

# --- (Function (၁) - is_on_off) ---
async def is_on_off(on_off: int) -> bool:
    """Check if a specific setting (by number) is on or off in the DB."""
    try:
        setting = await onoffdb.find_one({"on_off": on_off})
        # 'setting' document ရှိနေလျှင် True၊ မရှိလျှင် False
        return bool(setting)
    except Exception as e:
        logger.error(f"is_on_off check error for '{on_off}': {e}")
        return False # Error ဖြစ်ရင် default 'False' ကို ပြန်ပေး


# --- (Function (၂) - Search Result Cache) ---
async def get_yt_cache(key: str) -> Union[dict, None]:
    """MongoDB မှ cache လုပ်ထားသော YouTube search results ကို ပြန်ရှာသည်"""
    try:
        cached_result = await ytcache_db.find_one({"key": key})
        if cached_result:
            # 'details' ဆိုတဲ့ field ထဲက data ကိုပဲ ပြန်ပေး
            return cached_result.get("details")
    except Exception as e:
        logger.error(f"Error getting YT cache for key '{key}': {e}")
    return None # မတွေ့ရင် (သို့) error ဖြစ်ရင် None ပြန်ပေး

# --- (Function (၃) - Search Result Cache) ---
async def save_yt_cache(key: str, details: dict):
    """YouTube search results များကို MongoDB တွင် သိမ်းဆည်းသည်"""
    try:
        await ytcache_db.update_one(
            {"key": key}, # ဒီ key နဲ့ ရှာ
            {"$set": {"details": details}}, # ဒီ data ကို ထည့်/အစားထိုး
            upsert=True # key မရှိသေးရင် document အသစ်ဆောက်
        )
    except Exception as e:
        logger.error(f"Error saving YT cache for key '{key}': {e}")

# --- (Function (၄) - Downloaded File Path Cache) ---
async def get_cached_song_path(video_id: str) -> Union[str, None]:
    """MongoDB မှ cache လုပ်ထားသော local file path ကို ပြန်ရှာသည်"""
    try:
        cached_song = await songfiles_db.find_one({"video_id": video_id})
        if cached_song:
            # 'file_path' ဆိုတဲ့ field ထဲက data ကိုပဲ ပြန်ပေး
            return cached_song.get("file_path")
    except Exception as e:
        logger.error(f"Error getting song path cache for vid '{video_id}': {e}")
    return None

# --- (Function (၅) - Downloaded File Path Cache) ---
async def save_cached_song_path(video_id: str, file_path: str):
    """local file path ကို MongoDB တွင် သိမ်းဆည်းသည်"""
    try:
        await songfiles_db.update_one(
            {"video_id": video_id},
            {"$set": {"file_path": file_path}},
            upsert=True
        )
    except Exception as e:
        logger.error(f"Error saving song path cache for vid '{video_id}': {e}")

# --- (Function (၆) - Downloaded File Path Cache) ---
async def remove_cached_song_path(video_id: str):
    """MongoDB cache မှ file path ကို ဖယ်ရှားသည် (Clean Mode ကြောင့်)"""
    try:
        await songfiles_db.delete_one({"video_id": video_id})
    except Exception as e:
        logger.error(f"Error removing song path cache for vid '{video_id}': {e}")
