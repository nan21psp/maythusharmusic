#youtube.py (Fast Join + Video/Audio Fix)
import asyncio
import os
import re
import json
from typing import Union

import yt_dlp
import requests  # <-- Error 1: မမြင်ရတဲ့ space ကို ဖယ်ရှားထားသည်
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch

# --- (youtubedatabase.py ကို သီးသန့် import လုပ်ပါ) ---
# --- (get_all_yt_cache function အသစ်ကိုပါ import လုပ်ပါ) ---
try:
    from maythusharmusic.utils.database.youtubedatabase import (
        is_on_off,
        get_yt_cache,
        save_yt_cache,
        get_cached_song_path,
        save_cached_song_path,
        remove_cached_song_path,
        get_all_yt_cache  # <-- Error 2: ကျန်နေတာကို ထပ်ဖြည့်ထားသည်
    )
except ImportError:
    print("FATAL ERROR: youtubedatabase.py ကို ရှာမတွေ့ပါ")
    # ဒီနေရာမှာ bot ကို ရပ်သင့်ရင် ရပ်နိုင်ပါတယ်
    raise
# --- (ဒီနေရာအထိ) ---
from maythusharmusic.utils.formatters import time_to_seconds

import os
import glob
import random
import logging
import aiohttp 

# Logger ကို သတ်မှတ်ခြင်း
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



API_URL = "https://teaminflex.xyz"  # Change to your API server URL
API_KEY = "INFLEX93454428D"

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

def get_cookies():
    """
    သတ်မှတ်ထားသော cookies.txt ဖိုင်၏ path ကို ပြန်ပေးသည်။
    """
    global _cookies_warned
    cookie_path = "maythusharmusic/cookies/cookies.txt"
    
    if not os.path.exists(cookie_path):
        if not _cookies_warned:
            _cookies_warned = True
            logger.warning(f"{cookie_path} ကို ရှာမတွေ့ပါ၊ download များ မအောင်မြင်နိုင်ပါ။")
        return None
        
    return cookie_path

async def save_cookies(urls: list[str]) -> None:
    """
    ပေးလာသော URL များထဲမှ ပထမဆုံး URL မှ cookie ကို cookies.txt တွင် သိမ်းဆည်းသည်။
    """
    if not urls:
        logger.warning("save_cookies သို့ URL များ ပေးပို့မထားပါ။")
        return
    
    logger.info("ပထမဆုံး URL မှ cookie ကို cookies.txt တွင် သိမ်းဆည်းနေပါသည်...")
    url = urls[0]  # ပထမဆုံး URL ကိုသာ အသုံးပြုမည်
    path = "maythusharmusic/cookies/cookies.txt"
    link = url.replace("me/", "me/raw/")
    
    # Cookie သိမ်းဆည်းမည့် directory ရှိမရှိ စစ်ဆေးပြီး မရှိပါက တည်ဆောက်သည်
    os.makedirs(os.path.dirname(path), exist_ok=True)
        
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as resp:
                if resp.status == 200:
                    with open(path, "wb") as fw:
                        fw.write(await resp.read())
                    logger.info("Cookie များကို cookies.txt တွင် အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။")
                else:
                    logger.error(f"{link} မှ cookie download လုပ်ရာတွင် မအောင်မြင်ပါ၊ status: {resp.status}")
    except Exception as e:
        logger.error(f"Cookie သိမ်းဆည်းရာတွင် အမှားအယွင်း ဖြစ်ပွားပါသည်: {e}")


async def check_file_size(link):
    async def get_format_info(link):
        
        # --- Cookie Logic ---
        # 1. (ဒီ file ထဲမှာ ရှိပြီးသား) get_cookies() function ကို ခေါ်သုံးပါ
        cookie_file = get_cookies() 
        
        # 2. Command arguments တွေကို list အနေနဲ့ တည်ဆောက်ပါ
        proc_args = [
            "yt-dlp",
            "-J", # JSON output
        ]
        
        # 3. Cookie file ရှိခဲ့ရင် command ထဲကို ထည့်ပါ
        if cookie_file:
            proc_args.extend(["--cookies", cookie_file])
        
        # 4. နောက်ဆုံးမှာ link ကို ထည့်ပါ
        proc_args.append(link)
        # --- End Cookie Logic ---

        proc = await asyncio.create_subprocess_exec(
            *proc_args,  # List ကို unpack လုပ်ပြီး ထည့်ပါ
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
            if 'filesize' in format:
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


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        
        # --- Caching အတွက် Dictionary (Bot run ချိန်မှာ အလွတ်ဖြစ်နေပါမယ်) ---
        self._search_cache = {}

    # --- (FUNCTION အသစ် - Bot Startup တွင် ခေါ်ရန်) ---
    async def load_cache(self):
        """
        Bot startup တွင် MongoDB မှ cache များကို ယာယီမှတ်ဉာဏ်ထဲသို့ ကြိုတင်ဖြည့်သည်
        (Hydrates the in-memory cache from permanent DB on startup)
        """
        logger.info("MongoDB မှ YouTube search cache များကို ကြိုတင်ဖြည့်နေပါသည်...")
        try:
            # youtubedatabase.py ထဲက function အသစ်ကို ခေါ်ပါ
            all_cache = await get_all_yt_cache() 
            if all_cache:
                # DB ကရလာတဲ့ data တွေအားလုံးကို ယာယီမှတ်ဉာဏ်ထဲ ထည့်ပါ
                self._search_cache = all_cache
                logger.info(f"Cache {len(all_cache)} ခုကို ယာယီမှတ်ဉာဏ်ထဲသို့ အောင်မြင်စွာ ကြိုဖြည့်ပြီးပါပြီ။")
            else:
                logger.info("MongoDB တွင် ကြိုတင်ဖြည့်ရန် cache တစုံတရာ မရှိပါ။")
        except Exception as e:
            logger.error(f"YouTube cache ကြိုတင်ဖြည့်ရာတွင် အမှားဖြစ်ပွား: {e}")
    # --- (FUNCTION အသစ် ဒီမှာဆုံး) ---


    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if re.search(self.regex, link):
            return True
        else:
            return False

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset in (None,):
            return None
        return text[offset : offset + length]

    # --- START: Caching Logic Functions (MongoDB ထည့်သွင်းထားသည်) ---

    async def _fetch_from_youtube(self, link: str):
        """
        YouTube ကို တကယ်သွားရှာမယ့် private function
        (MongoDB Cache သို့ သိမ်းဆည်းခြင်း ထပ်တိုးထားသည်)
        """
        results = VideosSearch(link, limit=1)
        try:
            result = (await results.next())["result"][0]
        except IndexError:
            logger.error(f"YouTube မှာ {link} ကို ရှာမတွေ့ပါ။")
            return None

        title = result["title"]
        duration_min = result["duration"]
        thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        vidid = result["id"]
        yturl = result["link"] # track method အတွက် link ကိုပါ ယူထားပါ

        if str(duration_min) == "None":
            duration_sec = 0
        else:
            duration_sec = int(time_to_seconds(duration_min))
            
        # အချက်အလက် အစုံအလင်ကို Dictionary အဖြစ် တည်ဆောက်ပါ
        video_details = {
            "title": title,
            "duration_min": duration_min,
            "duration_sec": duration_sec,
            "thumbnail": thumbnail,
            "vidid": vidid,
            "link": yturl, # track method အတွက်
        }
        
        # --- START: Cache Logic (In-Memory & MongoDB) ---
        
        # 1. In-memory cache ထဲကို vidid ကို key အနေနဲ့ သုံးပြီး သိမ်းထားပါ
        self._search_cache[vidid] = video_details
        # 2. In-memory cache ထဲကို Link ကို key အနေနဲ့ သုံးပြီးလည်း သိမ်းထားပါ
        self._search_cache[link] = video_details
        
        # 3. MongoDB Cache (ytcache_db) ထဲကို vidid ကို key အနေနဲ့ သုံးပြီး သိမ်းပါ
        await save_yt_cache(vidid, video_details)
        # 4. MongoDB Cache (ytcache_db) ထဲကို Link ကို key အနေနဲ့ သုံးပြီးလည်း သိမ်းပါ
        await save_yt_cache(link, video_details)
        
        logger.info(f"Saved Search Result to MongoDB Cache: {vidid} / {link}")
        
        # --- END: Cache Logic ---
        
        return video_details

    async def _get_video_details(self, link: str, videoid: Union[bool, str] = None):
        """
        အချက်အလက် လိုအပ်တိုင်း ဒီ function ကို ခေါ်သုံးပါမယ်။
        ဒါက Cache ကို အရင်စစ်ပါမယ်။ (In-Memory + MongoDB)
        """
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]

        # 1. Cache Key ကို သတ်မှတ်ပါ (link ကို key အဖြစ် သုံးပါမည်)
        cache_key = link

        # 2. ယာယီမှတ်ဉာဏ် (Pre-load လုပ်ထားတဲ့) ထဲမှာ အရင်ရှာပါ
        if cache_key in self._search_cache:
            logger.info(f"Cache Hit (Memory): {cache_key}")
            return self._search_cache[cache_key]
            
        # 3. ယာယီထဲမှာ မရှိမှ MongoDB (အမြဲတမ်း မှတ်ဉာဏ်) ထဲမှာ ရှာကြည့်ပါ
        mongo_details = await get_yt_cache(cache_key)
        if mongo_details:
            logger.info(f"Cache Hit (MongoDB): {cache_key}")
            # MongoDB မှာတွေ့ရင် In-Memory cache ထဲကို ပြန်ထည့်ပါ
            self._search_cache[cache_key] = mongo_details
            if mongo_details.get("vidid"):
                self._search_cache[mongo_details["vidid"]] = mongo_details  # <-- Error 4: IndentationError ကို ပြင်ထားသည်
            return mongo_details
            
        # 4. Cache ထဲမှာမရှိရင် YouTube ကို တကယ်သွားရှာပါ
        logger.info(f"Cache Miss. Fetching from YouTube: {cache_key}")
        details = await self._fetch_from_youtube(link)
        
        # 5. _fetch_from_youtube က cache ထဲ သိမ်းပြီးသားဖြစ်ပါမည်
        
        return details

    # --- END: Caching Logic Functions ---


    # --- START: Caching ကို အသုံးပြုထားသော Functions များ (မူလအတိုင်း) ---

    async def details(self, link: str, videoid: Union[bool, str] = None):
        details = await self._get_video_details(link, videoid)
        if not details:
            return None, None, 0, None, None
            
        return (
            details["title"],
            details["duration_min"],
            details["duration_sec"],
            details["thumbnail"],
            details["vidid"],
        )

    async def title(self, link: str, videoid: Union[bool, str] = None):
        details = await self._get_video_details(link, videoid)
        return details["title"] if details else "Unknown Title"

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        details = await self._get_video_details(link, videoid)
        return details["duration_min"] if details else "00:00"

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        details = await self._get_video_details(link, videoid)
        return details["thumbnail"] if details else None

    async def track(self, link: str, videoid: Union[bool, str] = None):
        details = await self._get_video_details(link, videoid)
        if not details:
            return {}, None
            
        track_details = {
            "title": details["title"],
            "link": details["link"],
            "vidid": details["vidid"],
            "duration_min": details["duration_min"],
            "thumb": details["thumbnail"],
        }
        return track_details, details["vidid"]

    # --- END: Caching ကို အသုံးပြုထားသော Functions များ ---

    # --- START: Live Stream အတွက် Function (ဒါကိုပါ ပြင်ရပါမယ်) ---

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        cookie_file = get_cookies() # <-- Cookie ကိုပါ သုံးပါ
        proc_args = [
            "yt-dlp",
            "-g",
            "-f",
            # --- (Live Stream မှာလည်း အသံပါအောင် ပြင်ဆင်ထားသည်) ---
            "best[height<=?720][acodec!=none]/best[height<=?720]",
        ]
        if cookie_file:
            proc_args.extend(["--cookies", cookie_file])
        proc_args.append(link)
            
        proc = await asyncio.create_subprocess_exec(
            *proc_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        else:
            return 0, stderr.decode()

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
        )
        try:
            result = playlist.split("\n")
            for key in result:
                if key == "":
                    result.remove(key)
        except:
            result = []
        return result

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        ytdl_opts = { "quiet": True } 
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    str(format["format"])
                except:
                    continue
                if not "dash" in str(format["format"]).lower():
                    try:
                        format["format"]
                        format["filesize"]
                        format["format_id"]
                        format["ext"]
                        format["format_note"]
                    except:
                        continue
                    formats_available.append(
                        {
                            "format": format["format"],
                            "filesize": format["filesize"],
                            "format_id": format["format_id"],
                            "ext": format["ext"],
                            "format_note": format["format_note"],
                            "yturl": link,
                        }
                    )
            return formats_available, link

    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[bool, str] = None,
    ):
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

    # --- END: မူလ Functions များ ---
    
    # --- START: FAST JOIN (2-SECOND) MODIFICATION ---
    # --- ဒီ 'download' function တစ်ခုလုံးကို အသစ် လဲထည့်ပါ ---
    
    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> tuple[str, bool]:
        if videoid:
            link = self.base + link
        loop = asyncio.get_running_loop()
        cookie_file = get_cookies()

        # --- (Slow Download) Fallback Functions ---
        def audio_dl_fallback():
            """Slow Download (Fallback) for Audio"""
            ydl_optssx = {
                "format": "bestaudio[ext=m4a]/bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
            }
            if cookie_file:
                ydl_optssx["cookiefile"] = cookie_file
            x = yt_dlp.YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if not os.path.exists(xyz):
                x.download([link])
            return xyz

        def video_dl_fallback():
            """Slow Download (Fallback) for Video"""
            ydl_optssx = {
                "format": "bestvideo[height<=?720][width<=?1280]+bestaudio/best[height<=?720][width<=?1280]",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "prefer_ffmpeg": True,
                "merge_output_format": "mp4",
            }
            if cookie_file:
                ydl_optssx["cookiefile"] = cookie_file
            x = yt_dlp.YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.mp4")
            if not os.path.exists(xyz):
                x.download([link])
            return xyz
        
        # --- (songaudio/songvideo - এগুলোকে fast join এর দরকার নেই) ---
        if songvideo:
            # This part is for /song command, not /play or /vplay
            # It needs to download, so we use the original logic (but fixed)
            def song_video_dl():
                formats = f"{format_id}+140"
                fpath = f"downloads/{title}"
                ydl_optssx = {"format": formats, "outtmpl": fpath, "geo_bypass": True, "nocheckcertificate": True, "quiet": True, "no_warnings": True, "prefer_ffmpeg": True, "merge_output_format": "mp4"}
                if cookie_file: ydl_optssx["cookiefile"] = cookie_file
                x = yt_dlp.YoutubeDL(ydl_optssx); x.download([link])
            await loop.run_in_executor(None, song_video_dl)
            fpath = f"downloads/{title}.mp4"
            return fpath, True  # Return as (filepath, direct=True)
            
        elif songaudio:
            # This part is for /song command, not /play or /vplay
            def song_audio_dl():
                fpath = f"downloads/{title}.%(ext)s"
                ydl_optssx = {"format": format_id, "outtmpl": fpath, "geo_bypass": True, "nocheckcertificate": True, "quiet": True, "no_warnings": True, "prefer_ffmpeg": True, "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "320"}]}
                if cookie_file: ydl_optssx["cookiefile"] = cookie_file
                x = yt_dlp.YoutubeDL(ydl_optssx); x.download([link])
            await loop.run_in_executor(None, song_audio_dl)
            fpath = f"downloads/{title}.mp3"
            return fpath, True # Return as (filepath, direct=True)

        # --- (Fast Join) Logic for /play and /vplay ---
        
        # 'is_on_off(1)' check ကို 'if False:' လို့ ပြောင်းပြီး stream mode ကို force လုပ်ပါ
        # ဒါက slow download (video_dl/audio_dl) ကို လုံးဝ မခေါ်တော့ပါဘူး
        if await is_on_off(1) and not video: # API/DB Cache logic only for AUDIO
             # --- START: API Logic (DB File Path Cache ဖြင့်) ---
            downloaded_file = None
            direct = True  # API or audio_dl will be a direct file path
            video_id = None # video_id ကို အစပြုထားပါ

            try:
                video_id = extract_video_id(link)
                cached_path = await get_cached_song_path(video_id)
                if cached_path:
                    if os.path.exists(cached_path):
                        logger.info(f"DB Cache Hit (File Exists): {cached_path}")
                        downloaded_file = cached_path
                        return downloaded_file, direct # ချက်ချင်းပြန်ပေးလိုက်ပါ
                    else:
                        logger.warning(f"DB Cache Stale (File Missing): {cached_path}. Removing entry.")
                        await remove_cached_song_path(video_id)
                
                logger.info(f"DB Cache Miss. Attempting API download for {video_id}...")
                downloaded_file = await loop.run_in_executor(None, api_dl, video_id)

            except ValueError as e:
                logger.warning(f"Could not extract video ID for API download: {e}")
                downloaded_file = None
            except Exception as e:
                logger.error(f"An error occurred during API download attempt: {e}")
                downloaded_file = None

            if not downloaded_file:
                logger.warning(f"API download failed for {link}. Falling back to yt-dlp (cookies)...")
                downloaded_file = await loop.run_in_executor(None, audio_dl_fallback)
            else:
                logger.info(f"API download successful: {downloaded_file}")
                
            if downloaded_file and video_id:
                await save_cached_song_path(video_id, downloaded_file)
            elif downloaded_file and not video_id:
                try:
                    vid_from_path = os.path.basename(downloaded_file).split('.')[0]
                    if len(vid_from_path) == 11:
                        await save_cached_song_path(vid_from_path, downloaded_file)
                except Exception as e:
                    logger.error(f"Could not save fallback path to DB: {e}")
            
            return downloaded_file, direct
            
        else:
            # --- This is the FAST JOIN (2-Second) part ---
            if video:
                logger.info(f"Fast Join (Video) requested for: {link}")
                # --- (START: အသံမပါတဲ့ ပြဿနာကို ဖြေရှင်းရန်) ---
                # "bestvideo+bestaudio" (အသံမပါ) အစား "ရုပ်ရောသံရောပါတဲ့" format ကို တောင်းပါ
                format = "best[height<=?720][acodec!=none]/best[ext=mp4][height<=?720]/best[height<=?720]"
                # --- (END: ဖြေရှင်းရန်) ---
                fallback_func = video_dl_fallback
            else:
                logger.info(f"Fast Join (Audio) requested for: {link}")
                format = "bestaudio[ext=m4a]/bestaudio/best"
                fallback_func = audio_dl_fallback

            proc_args = ["yt-dlp", "-g", "-f", format]
            if cookie_file:
                proc_args.extend(["--cookies", cookie_file])
            proc_args.append(link)

            proc = await asyncio.create_subprocess_exec(
                *proc_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            
            if stdout:
                stream_link = stdout.decode().split("\n")[0]
                logger.info(f"Fast Join (Stream Link) found: {stream_link[:50]}...")
                return stream_link, False  # Return (URL, direct=False)
            else:
                logger.warning(f"FAST STREAM မရပါ ({'Video' if video else 'Audio'})။ SLOW DOWNLOAD သို့ Fallback လုပ်နေပါသည်: {stderr.decode()}")
                downloaded_file = await loop.run_in_executor(None, fallback_func)
                return downloaded_file, True # Return (Local File Path, direct=True)
