#youtube.py
import asyncio
import os
import re
import json
from typing import Union
import requests
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch
# from maythusharmusic.utils.database import is_on_off # <-- ဒီ import ကို အသစ်နဲ့ အစားထိုးပါမယ်
from maythusharmusic import app
from maythusharmusic.utils.formatters import time_to_seconds
import os
import glob  # <--- glob ကို import လုပ်ထားကြောင်း သေချာပါစေ
import random
import logging
import pymongo
from pymongo import MongoClient
import aiohttp
import config
import traceback # <--- traceback ကို import လုပ်ထားကြောင်း သေချာပါစေ
from maythusharmusic import LOGGER

# ==============================================
# ⬇️⬇️⬇️ DATABASE IMPORTS (User's Request) ⬇️⬇️⬇️
# ==============================================
try:
    from maythusharmusic.utils.database.youtubedatabase import (
        is_on_off,
        get_yt_cache,
        save_yt_cache,
        get_cached_song_path,
        save_cached_song_path,
        remove_cached_song_path,
        get_all_yt_cache
    )
    LOGGER(__name__).info("Successfully imported YouTube cache functions from youtubedatabase.")
except ImportError:
    print("FATAL ERROR: youtubedatabase.py ကို ရှာမတွေ့ပါ")
    # Cache function တွေမရှိရင် ဆက်မလုပ်နိုင်အောင် Error ပစ်ပါ
    raise ImportError("youtubedatabase.py not found, cache functions cannot be loaded.")
except Exception as e:
    print(f"FATAL ERROR: Error importing from youtubedatabase: {e}")
    raise

API_URL = "https://teaminflex.xyz"  # Change to your API server URL
API_KEY = "INFLEX68381428D"

# ==============================================
# 🎵 AUDIO DOWNLOAD
# ==============================================
async def download_song(link: str) -> str:
    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link
    logger = LOGGER("InflexMusic/platforms/Youtube.py")
    logger.info(f"🎵 [AUDIO] Starting download process for ID: {video_id}")

    if not video_id or len(video_id) < 3:
        return

    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.webm")

    if os.path.exists(file_path):
        logger.info(f"🎵 [LOCAL] Found existing file for ID: {video_id}")
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            payload = {"url": video_id, "type": "audio"}
            headers = {
                "Content-Type": "application/json",
                "X-API-KEY": API_KEY
            }

            # 🔹 Step 1: Trigger API and wait until it's ready (API handles waiting)
            async with session.post(f"{API_URL}/download", json=payload, headers=headers) as response:
                if response.status == 401:
                    logger.error("[API] Invalid API key")
                    return
                if response.status != 200:
                    logger.error(f"[AUDIO] API returned {response.status}")
                    return

                data = await response.json()
                if data.get("status") != "success" or not data.get("download_url"):
                    logger.error(f"[AUDIO] API response error: {data}")
                    return

                download_link = f"{API_URL}{data['download_url']}"

            # 🔹 Step 2: Download file (file is ready now)
            async with session.get(download_link) as file_response:
                if file_response.status != 200:
                    logger.error(f"[AUDIO] Download failed ({file_response.status}) for ID: {video_id}")
                    return
                with open(file_path, "wb") as f:
                    async for chunk in file_response.content.iter_chunked(8192):
                        f.write(chunk)

        logger.info(f"🎵 [API] Download completed successfully for ID: {video_id}")
        return file_path

    except Exception as e:
        logger.error(f"[AUDIO] Exception for ID: {video_id} - {e}")
        return


# ==============================================
# 🎥 VIDEO DOWNLOAD
# ==============================================
async def download_video(link: str) -> str:
    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link
    logger = LOGGER("InflexMusic/platforms/Youtube.py")
    logger.info(f"🎥 [VIDEO] Starting download process for ID: {video_id}")

    if not video_id or len(video_id) < 3:
        return

    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mkv")

    if os.path.exists(file_path):
        logger.info(f"🎥 [LOCAL] Found existing file for ID: {video_id}")
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            payload = {"url": video_id, "type": "video"}
            headers = {
                "Content-Type": "application/json",
                "X-API-KEY": API_KEY
            }

            # 🔹 Step 1: Trigger API (it waits internally until file is ready)
            async with session.post(f"{API_URL}/download", json=payload, headers=headers) as response:
                if response.status == 401:
                    logger.error("[API] Invalid API key")
                    return
                if response.status != 200:
                    logger.error(f"[VIDEO] API returned {response.status}")
                    return

                data = await response.json()
                if data.get("status") != "success" or not data.get("download_url"):
                    logger.error(f"[VIDEO] API response error: {data}")
                    return

                download_link = f"{API_URL}{data['download_url']}"

            # 🔹 Step 2: Download the ready file
            async with session.get(download_link) as file_response:
                if file_response.status != 200:
                    logger.error(f"[VIDEO] Download failed ({file_response.status}) for ID: {video_id}")
                    return
                with open(file_path, "wb") as f:
                    async for chunk in file_response.content.iter_chunked(8192):
                        f.write(chunk)

        logger.info(f"🎥 [API] Download completed successfully for ID: {video_id}")
        return file_path

    except Exception as e:
        logger.error(f"[VIDEO] Exception for ID: {video_id} - {e}")
        return

async def check_file_size(link):
    async def get_format_info(link):
        # cookie_file = cookie_txt_file()
        cookie_file = "maythusharmusic/cookies/cookies.txt" # <--- ဒီမှာပြင်လိုက်ပါပြီ (1)
        if not cookie_file or not os.path.exists(cookie_file): # Check if file exists
            print("No cookies found or path is incorrect. Cannot check file size.")
            return None
            
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--cookies", cookie_file,
            "-J",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            print(f'Error:\n{stderr.decode()}')
            return None
        return json.loads(stdout.decode())

    def parse_size(formats):
        total_size = 0
        for format in formats:
            if 'filesize' in format and format['filesize']:
                total_size += format['filesize']
        return total_size

    info = await get_format_info(link)
    if info is None:
        return None
    
    formats = info.get('formats', [])
    if not formats:
        print("No formats found.")
        return None
    
    total_size = parse_size(formats)
    return total_size

async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")


# ==============================================
# ❌❌❌ CACHE FUNCTIONS & MONGO SETUP REMOVED ❌❌❌
# (They are now imported from youtubedatabase.py)
# ==============================================


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        
        # --- (၁) ဒီစာကြောင်းလေး ထပ်ထည့်ပေးပါ (Cache သိမ်းဖို့ Dictionary) ---
        self.cache = {} 
        # -------------------------------------------------------------

    # --- (၂) ဒီ Function အသစ်ကို Class ထဲမှာ ထည့်ပေးပါ ---
    async def load_cache(self):
        """Bot စဖွင့်ချိန်တွင် Database မှ Cache များကို Memory ထဲသို့ ကြိုတင်ထည့်သွင်းသည်"""
        try:
            if hasattr(self, 'cache'):
                data = await get_all_yt_cache()
                if data:
                    self.cache.update(data)
                    print(f"✅ YouTube Cache Loaded: {len(data)} items.")
                else:
                    print("ℹ️ No YouTube Cache found in Database.")
        except Exception as e:
            print(f"❌ Failed to load YouTube Cache: {e}")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset: entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    # =================================================================
    # ⬇️⬇️⬇️ CACHE ကိုသုံးရန် ဒီ FUNCTION ကို ပြင်ဆင်ထားပါသည် ⬇️⬇️⬇️
    # (Imported functions များကို သုံးစွဲပါမည်)
    # =================================================================
    async def details(self, link: str, videoid: Union[bool, str] = None):
        vid_id_for_cache = None
        if videoid:
            vid_id_for_cache = link # 'videoid' mode မှာ link က id ပဲ ဖြစ်တယ်
            link = self.base + link
        else:
            if "&" in link:
                link = link.split("&")[0]
            # Attempt to get video_id for caching
            try:
                if 'v=' in link:
                    vid_id_for_cache = link.split('v=')[-1].split('&')[0]
                elif "youtu.be" in link:
                     vid_id_for_cache = link.split('/')[-1].split('?')[0]
                
                if not vid_id_for_cache:
                    vid_id_for_cache = link # Fallback
            except:
                vid_id_for_cache = link # Fallback
        
        # Check cache (using imported function)
        if vid_id_for_cache:
            cached_data = await get_yt_cache(vid_id_for_cache)
            if cached_data:
                # Return data in the same tuple format
                return (
                    cached_data.get("title"),
                    cached_data.get("duration_min"),
                    cached_data.get("duration_sec"),
                    cached_data.get("thumbnail"),
                    cached_data.get("vidid")
                )

        # If not in cache, fetch using VideosSearch
        results = VideosSearch(link, limit=1)
        try:
            video_result = (await results.next())["result"][0]
        except Exception as e:
            LOGGER("InflexMusic/platforms/Youtube.py").error(f"VideosSearch failed for {link}: {e}")
            return None, None, 0, None, None # Failed to fetch

        title = video_result["title"]
        duration_min = video_result["duration"]
        thumbnail = video_result["thumbnails"][0]["url"].split("?")[0]
        vidid = video_result["id"] # This is the canonical ID
        duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
        
        # Save to cache (using imported function)
        if vidid: 
            details_to_cache = {
                "video_id": vidid, # Store against the canonical ID
                "title": title,
                "duration_min": duration_min,
                "duration_sec": duration_sec,
                "thumbnail": thumbnail,
                "vidid": vidid, 
            }
            await save_yt_cache(vidid, details_to_cache)
            
            # user က link (သို့) short id (vid_id_for_cache) နဲ့ ရှာခဲ့ရင်
            # အဲ့ဒီ key နဲ့လည်း cache ကို သိမ်းပါ
            if vid_id_for_cache and vid_id_for_cache != vidid:
                 await save_yt_cache(vid_id_for_cache, details_to_cache)

        return title, duration_min, duration_sec, thumbnail, vidid
    
    # ⬆️⬆️⬆️ (details function အဆုံး) ⬆️⬆️⬆️

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["title"]

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["duration"]

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["thumbnails"][0]["url"].split("?")[0]

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            downloaded_file = await download_video(link)
            if downloaded_file:
                return 1, downloaded_file
            else:
                return 0, "Video API did not return a valid file."
        except Exception as e:
            print(f"Video API failed: {e}")
            return 0, f"Video API failed: {e}"

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        # cookie_file = cookie_txt_file()
        cookie_file = "maythusharmusic/cookies/cookies.txt" # <--- ဒီမှာပြင်လိုက်ပါပြီ (2)
        if not cookie_file or not os.path.exists(cookie_file): # Check if file exists
            return []
        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --cookies {cookie_file} --playlist-end {limit} --skip-download {link}"
        )
        try:
            result = [key for key in playlist.split("\n") if key]
        except:
            result = []
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        # cookie_file = cookie_txt_file()
        cookie_file = "maythusharmusic/cookies/cookies.txt" # <--- ဒီမှာပြင်လိုက်ပါပြီ (3)
        if not cookie_file or not os.path.exists(cookie_file): # Check if file exists
            return [], link
        ytdl_opts = {"quiet": True, "cookiefile": cookie_file}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    if "dash" not in str(format["format"]).lower():
                        formats_available.append(
                            {
                                "format": format["format"],
                                "filesize": format.get("filesize"),
                                "format_id": format["format_id"],
                                "ext": format["ext"],
                                "format_note": format["format_note"],
                                "yturl": link,
                            }
                        )
                except:
                    continue
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    # =================================================================
    # ⬇️⬇️⬇️ CACHE ကိုသုံးရန် ဒီ FUNCTION ကို ပြင်ဆင်ထားပါသည် ⬇️⬇️⬇️
    # (Imported functions များကို သုံးစွဲပါမည်)
    # =================================================================

    async def download(
        self,
        link: str,
        mystic, # Pyrogram Message
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link

        logger = LOGGER("InflexMusic/platforms/Youtube.py")
        
        # Determine video_id for caching
        video_id_for_cache = None
        try:
            if videoid:
                 video_id_for_cache = link # 'videoid' mode မှာ link က id ပဲ ဖြစ်တယ်
            elif 'v=' in link:
                video_id_for_cache = link.split('v=')[-1].split('&')[0]
            elif "youtu.be" in link:
                video_id_for_cache = link.split('/')[-1].split('?')[0]
            
            if not video_id_for_cache:
                 video_id_for_cache = link # Fallback
        except:
             video_id_for_cache = None # Cannot determine ID, caching will be skipped
        
        # ================================
        # 0. CHECK CACHE FIRST (Audio only)
        # ================================
        if video_id_for_cache and not video and not songvideo: # Only cache audio
             cached_path = await get_cached_song_path(video_id_for_cache) # Using imported function
             if cached_path: # This function already checks os.path.exists
                 logger.info(f"[Downloader] Using cached file for {video_id_for_cache}: {cached_path}")
                 return cached_path, True # Return cached file

        downloaded_file = None

        # ================================
        # 1. API ကို အရင် ကြိုးစားပါ
        # ================================
        try:
            if songvideo: # songvideo က video ကိုပဲ တောင်းတာ
                logger.info(f"[Downloader] Trying API download (Video) for {link}")
                downloaded_file = await download_video(link)
            elif video: # video က video ကိုပဲ တောင်းတာ
                logger.info(f"[Downloader] Trying API download (Video) for {link}")
                downloaded_file = await download_video(link)
            elif songaudio: # audio
                logger.info(f"[Downloader] Trying API download (Audio) for {link}")
                downloaded_file = await download_song(link)
            else: # Default to audio
                logger.info(f"[Downloader] Trying API download (Audio) for {link}")
                downloaded_file = await download_song(link)
            
            if downloaded_file and os.path.exists(downloaded_file):
                logger.info(f"[Downloader] API download successful: {downloaded_file}")
                # Save to cache if it was audio
                if video_id_for_cache and not video and not songvideo:
                    await save_cached_song_path(video_id_for_cache, downloaded_file) # Using imported function
                return downloaded_file, True # API အောင်မြင်
            else:
                logger.warning(f"[Downloader] API download failed or file not found for {link}.")

        except Exception as e:
            logger.error(f"[Downloader] API download exception for {link}: {e}")
            downloaded_file = None # Exception ဖြစ်ခဲ့ရင် None ဖြစ်ကြောင်း သေချာပါစေ

        # ================================
        # 2. API မအောင်မြင်ပါက YT-DLP (cookies.txt) ဖြင့် ဆက်ကြိုးစားပါ
        # ================================
        logger.warning(f"[Downloader] Falling back to yt-dlp (cookies) for {link}")
        
        try:
            # mystic message ကို update လုပ်ပါ (pyrogram message object ဖြစ်ရမည်)
            if mystic and hasattr(mystic, "edit_text"):
                await mystic.edit_text("Downloader: API failed, trying backup (yt-dlp)...")
        except:
            pass # message ကို edit မလုပ်နိုင်လည်း ဆက်သွားပါ

        cookie_file = "maythusharmusic/cookies/cookies.txt"
        if not os.path.exists(cookie_file):
            logger.warning("[Downloader] cookies.txt not found. yt-dlp will proceed without cookies.")
            cookie_file = None
        
        # Use the video_id_for_cache if available
        video_id = video_id_for_cache if video_id_for_cache else "video"

        # filename အတွက် title ကို သုံးပါ၊ မရှိမှ video_id ကို သုံးပါ
        file_name_base = title
        if title:
             file_name_base = re.sub(r"[^\w\s-]", "", str(file_name_base)) # str() ထည့်ပြီး title က None ဖြစ်မနေတာ သေချာပါစေ
             file_name_base = file_name_base.strip().replace(" ", "_")
             file_name_base = file_name_base[:50] # အရှည် ကန့်သတ်ပါ
        if not file_name_base: # title မရှိရင် (သို့) ရှင်းလိုက်လို့ ကုန်သွားရင်
             file_name_base = video_id
        
        DOWNLOAD_DIR = "downloads"
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        # yt-dlp options
        ydl_opts = {
            "nocheckcertificate": True,
            "outtmpl": os.path.join(DOWNLOAD_DIR, f"{file_name_base}.%(ext)s"),
            "geo_bypass": True,
            "quiet": True,
            "retries": 10,
            "fragment_retries": 10,
        }

        if cookie_file:
            ydl_opts["cookiefile"] = cookie_file

        final_file_path = ""
        is_video_download = bool(video or songvideo) # video ဒါမှမဟုတ် songvideo တစ်ခုခု true ဖြစ်ရင် video download 
        
        if is_video_download: # Video လိုချင်လျှင်
            ydl_opts["format"] = (
                f"{format_id}+bestaudio" if format_id else "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
            )
            ydl_opts["merge_output_format"] = "mkv"
            final_file_path = os.path.join(DOWNLOAD_DIR, f"{file_name_base}.mkv")
            ydl_opts["outtmpl"] = os.path.join(DOWNLOAD_DIR, f"{file_name_base}") # yt-dlp က .mkv ကို ထည့်ပါလိမ့်မယ်
        
        else: # Audio သာ
            ydl_opts["format"] = (
                format_id if format_id else "bestaudio/best"
            )
            ydl_opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "opus", # .opus file ကို ထုတ်ပါမယ်
                    "preferredquality": "320",
                }
            ]
            final_file_path = os.path.join(DOWNLOAD_DIR, f"{file_name_base}.opus")
            ydl_opts["outtmpl"] = os.path.join(DOWNLOAD_DIR, f"{file_name_base}") # yt-dlp က .opus ကို ထည့်ပါလိမ့်မယ်

        # Download ကို ကြိုးစားပါ
        try:
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, ydl.download, [link])
            
            # Download လုပ်ပြီးသား file ကို စစ်ဆေးပါ
            if os.path.exists(final_file_path):
                 logger.info(f"[Downloader] yt-dlp download successful: {final_file_path}")
                 # Save to cache if it was audio
                 if video_id_for_cache and not is_video_download:
                     await save_cached_song_path(video_id_for_cache, final_file_path) # Using imported function
                 return final_file_path, True
            else:
                 logger.error(f"[Downloader] yt-dlp ran, but expected file not found: {final_file_path}")
                 # glob သုံးပြီး နောက်ဆုံးတစ်ခေါက် ထပ်ရှာပါ
                 glob_path = os.path.join(DOWNLOAD_DIR, f"{file_name_base}.*")
                 files = glob.glob(glob_path)
                 files = [f for f in files if not f.endswith((".part", ".ytdl"))] # မပြည့်စုံတဲ့ file တွေ မပါစေနဲ့
                 if files:
                    found_file = files[0] # တွေ့တဲ့ ပထမဆုံး file ကို ယူပါ
                    logger.warning(f"[Downloader] Found file via glob: {found_file}")
                    # Save to cache if it was audio
                    if video_id_for_cache and not is_video_download:
                        await save_cached_song_path(video_id_for_cache, found_file) # Using imported function
                    return found_file, True
                 else:
                    logger.error(f"[Downloader] Glob search also failed for {glob_path}")
                    return None, False # yt-dlp လည်း မအောင်မြင်ပါ

        except Exception as e:
            logger.error(f"[Downloader] yt-dlp download exception: {e}\n{traceback.format_exc()}")
            return None, False
    
    # ⬆️⬆️⬆️ (download function အဆုံး) ⬆️⬆️⬆️
