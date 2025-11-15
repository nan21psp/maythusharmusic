# youtube.py (ပြင်ဆင်ပြီး)

import asyncio
import os
import re
import json
from typing import Union

import yt_dlp
import requests 
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch

# --- (youtubedatabase.py ကို သီးသန့် import လုပ်ပါ) ---
# --- (get_all_yt_cache function အသစ်ကိုပါ import လုပ်ပါ) ---
from maythusharmusic.utils.database.youtubedatabase import (
    is_on_off,
    get_yt_cache,
    save_yt_cache,
    get_cached_song_path,
    save_cached_song_path,
    remove_cached_song_path,
    get_all_yt_cache  # <-- (Function အသစ်)
)
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

# ... (API_KEYS, api_dl, get_cookies, save_cookies, check_file_size, shell_cmd functions တွေ ဒီအတိုင်းရှိနေပါမယ်) ...
# ... (ခင်ဗျားပို့ထားတဲ့ code အတိုင်း မပြောင်းလဲပါ) ...

# ✅ Configurable constants
API_KEYS = [
    "AIzaSyCVwFq4QsxUsdpVY3lFr2sW48-YiS6wQQw",
    "AIzaSyDElbd6obEzWVcnnKHu8ioWlk64pzqLLP8",
    "AIzaSyCUMRm288rXsdj2jP4x6-9femdZ_WL7Y9g",
    "AIzaSyCqJ3KJhoWTnYC5N0jzRWWeDxTaj4nnhPE",
    "AIzaSyC7ar1C5OBsIxhkZz6-l1fjJuRFqatxV_k",
    "AIzaSyBxbgHrDdAZrMMRd74xjT56Ekbbm7r2C7o",
    "AIzaSyCkBCShmwhFNU_bybOIqdvUghWhH1nYPj4",
    "AIzaSyDf5befJSwPCDey0p1yPd_VaneoIFbSJhA",
    "AIzaSyDw5sEKPhxaOs9qU4Y7WsrL4JvpFQRXQDY",
    "AIzaSyB_Ta275uWxtX_kkieTW7Kut11RIY1FLwU",
    "AIzaSyAeI8Pz3CeteoAkUVIO3fnBRdSNRHEpwfw",
    "AIzaSyDs-1JGzNChWKkW3MqXbO-2upYOmUjvhE4",
    "AIzaSyAKJl_SuQh5xeEBRSskL7VBZLSKJaT-j9s",
    "AIzaSyAPsHm8tlYJJyrdI6QpVF8p3BIWrY4qnBg",
    "AIzaSyAgj6SbEncvCKnF6-1cffeckBSbk7IXBNk",
    "AIzaSyDwUT_cdur25HlAL01xLHrLfZRIPzzmf7s",
    "AIzaSyB7370l-ModxTfuhIlXnz7k8yR7LzuCOzI",
    "AIzaSyAsxU61WrtIE1dRe1YZDV0XkP_n8sJggPk",
    "AIzaSyA70vtRZ-HtXAdwQTNIhaiAhb5RUPQHJVA",
    "AIzaSyDMUPINKHWjXfH3rX2kwYiH8sGtiQF4bHs",
    "AIzaSyAfCk6zut2ggu_qJ3WrH_iYlvVc3upG9lk" 
]
def get_random_api_key():
    return random.choice(API_KEYS)

API_BASE_URL = "http://deadlinetech.site"
MIN_FILE_SIZE = 51200

def extract_video_id(link: str) -> str:
    patterns = [
        r'youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=)([0-9A-Za-z_-]{11})',
        r'youtu\.be\/([0-9A-Za-z_-]{11})',
        r'youtube\.com\/(?:playlist\?list=[^&]+&v=|v\/)([0-9A-Za-z_-]{11})',
        r'youtube\.com\/(?:.*\?v=|.*\/)([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, link)
        if match:
            return match.group(1)
    raise ValueError("Invalid YouTube link provided.")
    
def api_dl(video_id: str) -> str | None:
    api_key = get_random_api_key()
    api_url = f"{API_BASE_URL}/download/song/{video_id}?key={api_key}"
    file_path = os.path.join("downloads", f"{video_id}.mp3")
    if os.path.exists(file_path):
        logger.info(f"{file_path} already exists. Skipping download.")
        return file_path
    try:
        response = requests.get(api_url, stream=True, timeout=10)
        if response.status_code == 200:
            os.makedirs("downloads", exist_ok=True)
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            file_size = os.path.getsize(file_path)
            if file_size < MIN_FILE_SIZE:
                logger.warning(f"Downloaded file is too small ({file_size} bytes). Removing.")
                os.remove(file_path)
                return None
            logger.info(f"Downloaded {file_path} ({file_size} bytes) using API key: {api_key[:10]}...")
            return file_path
        else:
            logger.warning(f"Failed to download {video_id}. Status: {response.status_code} using API key: {api_key[:10]}...")
            return None
    except requests.RequestException as e:
        logger.error(f"Download error for {video_id}: {e} using API key: {api_key[:10]}...")
        return None
    except OSError as e:
        logger.error(f"File error for {video_id}: {e}")
        return None

_cookies_warned = False
def get_cookies():
    global _cookies_warned
    cookie_path = "maythusharmusic/cookies/cookies.txt"
    if not os.path.exists(cookie_path):
        if not _cookies_warned:
            _cookies_warned = True
            logger.warning(f"{cookie_path} ကို ရှာမတွေ့ပါ၊ download များ မအောင်မြင်နိုင်ပါ။")
        return None
    return cookie_path

async def save_cookies(urls: list[str]) -> None:
    if not urls:
        logger.warning("save_cookies သို့ URL များ ပေးပို့မထားပါ။")
        return
    logger.info("ပထမဆုံး URL မှ cookie ကို cookies.txt တွင် သိမ်းဆည်းနေပါသည်...")
    url = urls[0]
    path = "maythusharmusic/cookies/cookies.txt"
    link = url.replace("me/", "me/raw/")
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
        cookie_file = get_cookies() 
        proc_args = [ "yt-dlp", "-J" ]
        if cookie_file:
            proc_args.extend(["--cookies", cookie_file])
        proc_args.append(link)
        proc = await asyncio.create_subprocess_exec(
            *proc_args,
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
    if info is None: return None
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

    # --- (FUNCTION အသစ် - ဒီနေရာမှာ ထည့်ပါ) ---
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
        yturl = result["link"] 
        if str(duration_min) == "None":
            duration_sec = 0
        else:
            duration_sec = int(time_to_seconds(duration_min))
        video_details = {
            "title": title,
            "duration_min": duration_min,
            "duration_sec": duration_sec,
            "thumbnail": thumbnail,
            "vidid": vidid,
            "link": yturl,
        }
        # --- START: Cache Logic (In-Memory & MongoDB) ---
        self._search_cache[vidid] = video_details
        self._search_cache[link] = video_details
        await save_yt_cache(vidid, video_details)
        await save_yt_cache(link, video_details)
        logger.info(f"Saved Search Result to MongoDB Cache: {vidid} / {link}")
        # --- END: Cache Logic ---
        return video_details

    async def _get_video_details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        cache_key = link

        # 1. ယာယီမှတ်ဉာဏ် (Pre-load လုပ်ထားတဲ့) ထဲမှာ အရင်ရှာပါ
        if cache_key in self._search_cache:
            logger.info(f"Cache Hit (Memory): {cache_key}")
            return self._search_cache[cache_key]
            
        # 2. ယာယီထဲမှာ မရှိမှ MongoDB (အမြဲတမ်း မှတ်ဉာဏ်) ထဲမှာ ရှာကြည့်ပါ
        mongo_details = await get_yt_cache(cache_key)
        if mongo_details:
            logger.info(f"Cache Hit (MongoDB): {cache_key}")
            self._search_cache[cache_key] = mongo_details
            if mongo_details.get("vidid"):
                 self._search_cache[mongo_details["vidid"]] = mongo_details
            return mongo_details
            
        # 3. Cache ထဲမှာမရှိရင် YouTube ကို တကယ်သွားရှာပါ
        logger.info(f"Cache Miss. Fetching from YouTube: {cache_key}")
        details = await self._fetch_from_youtube(link)
        return details

    # --- (ကျန်တဲ့ class methods တွေ (details, title, duration, download, etc.) ဒီအတိုင်းရှိနေပါမယ်) ---
    # ... (ခင်ဗျားပို့ထားတဲ့ code အတိုင်း မပြောင်းလဲပါ) ...

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

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
            f"{link}",
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
ci         result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    # --- START: API-First Download Function (DB File Path Cache ဖြင့် ပြင်ဆင်ပြီး) ---
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
    ) -> str:
        if videoid:
            link = self.base + link
        loop = asyncio.get_running_loop()
        cookie_file = get_cookies()

        def audio_dl():
            ydl_optssx = {
                "format": "bestaudio/best",
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
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def video_dl():
            ydl_optssx = {
                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
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
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def song_video_dl():
            formats = f"{format_id}+140"
            fpath = f"downloads/{title}"
            ydl_optssx = {
                "format": formats,
                "outtmpl": fpath,
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
            x.download([link])

        def song_audio_dl():
            fpath = f"downloads/{title}.%(ext)s"
            ydl_optssx = {
                "format": format_id,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "prefer_ffmpeg": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                      D-quality": "320",
                    }
                ],
            }
            if cookie_file:
                ydl_optssx["cookiefile"] = cookie_file
            x = yt_dlp.YoutubeDL(ydl_optssx)
            x.download([link])

        if songvideo:
            await loop.run_in_executor(None, song_video_dl)
            fpath = f"downloads/{title}.mp4"
            return fpath
        elif songaudio:
            await loop.run_in_executor(None, song_audio_dl)
            fpath = f"downloads/{title}.mp3"
            return fpath
        elif video:
            if await is_on_off(1):
                direct = True
                downloaded_file = await loop.run_in_executor(None, video_dl)
            else:
                proc_args = [
                    "yt-dlp",
                    "-g",
                    "-f",
                    "best[height<=?720][width<=?1280]",
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
                    downloaded_file = stdout.decode().split("\n")[0]
                    direct = False
                else:
                    direct = True
                    downloaded_file = await loop.run_in_executor(None, video_dl)
        else:
            downloaded_file = None
            direct = True 
            video_id = None 
            try:
                video_id = extract_video_id(link)
                cached_path = await get_cached_song_path(video_id)
                if cached_path:
                    if os.path.exists(cached_path):
                        logger.info(f"DB Cache Hit (File Exists): {cached_path}")
                        downloaded_file = cached_path
                        return downloaded_file, direct
                    else:
                        logger.warning(f"DB Cache Stale (File Missing): {cached_path}. Removing entry.")
                        await remove_cached_song_path(video_id)
                logger.info(f"DB Cache Miss. Attempting API download for {video_id}...")
                downloaded_file = await loop.run_in_executor(
                    None, 
                    api_dl,
                    video_id
                )
            except ValueError as e:
                logger.warning(f"Could not extract video ID for API download: {e}")
                downloaded_file = None
            except Exception as e:
                logger.error(f"An error occurred during API download attempt: {e}")
                downloaded_file = None

            if not downloaded_file:
                logger.warning(f"API download failed for {link}. Falling back to yt-dlp (cookies)...")
                downloaded_file = await loop.run_in_executor(None, audio_dl)
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
