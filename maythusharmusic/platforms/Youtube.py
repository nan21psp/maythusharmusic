import asyncio
import os
import re
import json
from typing import Union, Tuple
import yt_dlp

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from maythusharmusic.utils.database import is_on_off

import logging
import time


# ✅ Configurable constants
MIN_FILE_SIZE = 51200

# This regex is used in multiple places now
YOUTUBE_REGEX = r"(?:youtube\.com|youtu\.be)"

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
    

async def check_file_size(link):
    async def get_format_info(link):
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--geo-bypass-country", "US",  # <-- Change to US
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
        self.regex = YOUTUBE_REGEX # Use the global regex
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    # Helper function to extract info with yt-dlp
    async def _extract_info(self, link: str, search: bool = False):
        ytdl_opts = {
            'quiet': True,
            'no_warnings': True,
            'geo_bypass_country': 'US',  # <-- Use 'US' instead of generic 'True'
            'skip_download': True,
        }

        # --- Invidious Strategy ---
        original_link = link # Save original link for fallback
        
        # If it's a search query, prepend 'invidious:ytsearch:'
        if search and not link.startswith("http"):
            link = f"invidious:ytsearch:{link}" 
        
        # If it's a direct link, prepend 'invidious:'
        elif not search and re.search(self.regex, link):
             link = f"invidious:{link}"
        # -------------------------

        try:
            ydl = yt_dlp.YoutubeDL(ytdl_opts)
            loop = asyncio.get_running_loop()
            
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(link, download=False))

            if 'entries' in info and info['entries']:
                return info['entries'][0]
            elif 'id' in info:
                return info
            else:
                raise ValueError("No video information found (Invidious).")

        except Exception as e:
            print(f"Failed to fetch details using yt-dlp (Invidious attempt): {e}")
            
            # --- FALLBACK ---
            # If Invidious fails, try one more time with the original link
            print("Invidious failed. Falling back to standard yt-dlp search...")
            
            link = original_link # Reset to original link
            if search and not link.startswith("http"):
                link = f"ytsearch:{link}"
            
            try:
                ydl_fallback = yt_dlp.YoutubeDL(ytdl_opts) # ydl_opts still has geo_bypass_country
                loop_fallback = asyncio.get_running_loop()
                info_fallback = await loop_fallback.run_in_executor(None, lambda: ydl_fallback.extract_info(link, download=False))
                
                if 'entries' in info_fallback and info_fallback['entries']:
                    return info_fallback['entries'][0]
                elif 'id' in info_fallback:
                    return info_fallback
                else:
                    raise ValueError("No video information found (Fallback).")
                    
            except Exception as e_fallback:
                print(f"Fallback yt-dlp fetch failed: {e_fallback}")
                raise e_fallback # Raise the final error

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

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        result = await self._extract_info(link, search=True)

        title = result.get("title", "Unknown Title")
        duration_sec = result.get("duration", 0)
        
        if duration_sec is None:
            duration_sec = 0
        
        if duration_sec == 0:
            duration_min = "00:00"
        else:
            mins, secs = divmod(duration_sec, 60)
            duration_min = f"{int(mins):02d}:{int(secs):02d}"

        vidid = result.get("id", "UnknownID")
        
        thumbnail = "http://googleusercontent.com/youtube.com/4"
        if result.get("thumbnails"):
            thumbnail = result["thumbnails"][-1]["url"].split("?")[0]

        return title, duration_min, int(duration_sec), thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        result = await self._extract_info(link, search=True)
        return result.get("title", "Unknown Title")

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        result = await self._extract_info(link, search=True)
        duration_sec = result.get("duration", 0)
        
        if duration_sec is None:
            duration_sec = 0
        
        if duration_sec == 0:
            return "00:00"
        else:
            mins, secs = divmod(duration_sec, 60)
            return f"{int(mins):02d}:{int(secs):02d}"

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        result = await self._extract_info(link, search=True)
        
        if result.get("thumbnails"):
            return result["thumbnails"][-1]["url"].split("?")[0]
        return "http://googleusercontent.com/youtube.com/4"

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        invidious_link = f"invidious:{link}" if re.search(self.regex, link) else link
        
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--geo-bypass-country", "US", # <-- Use 'US'
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
            f"{invidious_link}", # <-- Try Invidious first
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        else:
            print(f"yt-dlp video (Invidious) failed: {stderr.decode()}. Trying fallback.")
            # --- FALLBACK ---
            proc_fallback = await asyncio.create_subprocess_exec(
                "yt-dlp",
                "--geo-bypass-country", "US",
                "-g",
                "-f",
                "best[height<=?720][width<=?1280]",
                f"{link}", # <-- Use original link
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_fallback, stderr_fallback = await proc_fallback.communicate()
            if stdout_fallback:
                return 1, stdout_fallback.decode().split("\n")[0]
            else:
                return 0, stderr_fallback.decode()

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        
        invidious_link = f"invidious:{link}" if re.search(self.regex, link) else link
        
        playlist = await shell_cmd(
            f"yt-dlp -i --geo-bypass-country US --get-id --flat-playlist --playlist-end {limit} --skip-download {invidious_link}" # <-- Try Invidious first
        )
        
        if not playlist or "ERROR" in playlist.upper():
            print(f"yt-dlp playlist (Invidious) failed. Trying fallback.")
            # --- FALLBACK ---
            playlist = await shell_cmd(
                f"yt-dlp -i --geo-bypass-country US --get-id --flat-playlist --playlist-end {limit} --skip-download {link}" # <-- Use original link
            )

        try:
            result = playlist.split("\n")
            for key in result:
                if key == "":
                    result.remove(key)
        except:
            result = []
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]

        result = await self._extract_info(link, search=True) # Use search=True

        title = result.get("title", "Unknown Title")
        duration_sec = result.get("duration", 0)
        
        if duration_sec is None:
            duration_sec = 0
        
        if duration_sec == 0:
            duration_min = "00:00"
        else:
            mins, secs = divmod(duration_sec, 60)
            duration_min = f"{int(mins):02d}:{int(secs):02d}"
            
        vidid = result.get("id", "UnknownID")
        yturl = result.get("webpage_url", link)
        
        thumbnail = "http://googleusercontent.com/youtube.com/4"
        if result.get("thumbnails"):
            thumbnail = result["thumbnails"][-1]["url"].split("?")[0]
        
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
        ytdl_opts = {"quiet": True, "geo_bypass_country" : "US"} # <-- Use 'US'
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
        query_type: int, # query_type is the index (0-9)
        videoid: Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]

        # Use yt-dlp search with Invidious
        ytdl_opts = {
            'quiet': True,
            'no_warnings': True,
            'geo_bypass_country': 'US', # <-- Use 'US'
            'skip_download': True,
            'default_search': 'ytsearch10', 
        }
        
        # --- Invidious Strategy ---
        search_query = link
        search_query_invidious = f"invidious:ytsearch10:{link}"
        
        try:
            # Try Invidious first
            ydl = yt_dlp.YoutubeDL(ytdl_opts)
            loop = asyncio.get_running_loop()
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(search_query_invidious, download=False))
            
        except Exception as e:
            print(f"Slider (Invidious) failed: {e}. Falling back.")
            # --- FALLBACK ---
            ydl_fallback = yt_dlp.YoutubeDL(ytdl_opts)
            loop_fallback = asyncio.get_running_loop()
            info = await loop_fallback.run_in_executor(None, lambda: ydl_fallback.extract_info(search_query, download=False))
        # -------------------------

        if 'entries' not in info or not info['entries'] or len(info['entries']) <= query_type:
            raise ValueError("Not enough search results for slider.")

        result = info['entries'][query_type] 

        title = result.get("title", "Unknown Title")
        duration_sec = result.get("duration", 0)
        
        if duration_sec is None:
            duration_sec = 0
        
        if duration_sec == 0:
            duration_min = "00:00"
        else:
            mins, secs = divmod(duration_sec, 60)
            duration_min = f"{int(mins):02d}:{int(secs):02d}"
            
        vidid = result.get("id", "UnknownID")
        
        thumbnail = "http://googleusercontent.com/youtube.com/4"
        if result.get("thumbnails"):
            thumbnail = result["thumbnails"][-1]["url"].split("?")[0]
            
        return title, duration_min, thumbnail, vidid
            

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
    ) -> Tuple[str, bool]:
        
        if videoid:
            link = self.base + link
        loop = asyncio.get_running_loop()
        
        # --- Create Invidious link ---
        original_link = link
        invidious_link = link
        if re.search(YOUTUBE_REGEX, link):
            invidious_link = f"invidious:{link}"
        # -----------------------------

        def audio_dl():
            ydl_optssx = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass_country": "US", # <-- Use 'US'
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
            try:
                # --- Try Invidious First ---
                x = yt_dlp.YoutubeDL(ydl_optssx)
                info = x.extract_info(invidious_link, False)
                xyz = os.path.join("downloads", f"{info['id']}.mp3")
                if os.path.exists(xyz):
                    return xyz
                x.download([invidious_link])
                return xyz
            except Exception as e:
                print(f"yt-dlp audio (Invidious) failed: {e}. Trying fallback.")
                # --- FALLBACK ---
                try:
                    x_fallback = yt_dlp.YoutubeDL(ydl_optssx)
                    info_fallback = x_fallback.extract_info(original_link, False) 
                    xyz_fallback = os.path.join("downloads", f"{info_fallback['id']}.mp3")
                    if os.path.exists(xyz_fallback):
                        return xyz_fallback
                    x_fallback.download([original_link])
                    return xyz_fallback
                except Exception as e_fallback:
                    print(f"yt-dlp audio (Fallback) failed: {e_fallback}")
                    return None

        def video_dl():
            ydl_optssx = {
                "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass_country": "US", # <-- Use 'US'
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "merge_output_format": "mp4",
            }
            try:
                # --- Try Invidious First ---
                x = yt_dlp.YoutubeDL(ydl_optssx)
                info = x.extract_info(invidious_link, False)
                xyz = os.path.join("downloads", f"{info['id']}.mp4")
                if os.path.exists(xyz):
                    return xyz
                x.download([invidious_link])
                return xyz
            except Exception as e:
                print(f"yt-dlp video (Invidious) failed: {e}. Trying fallback.")
                # --- FALLBACK ---
                try:
                    x_fallback = yt_dlp.YoutubeDL(ydl_optssx)
                    info_fallback = x_fallback.extract_info(original_link, False)
                    xyz_fallback = os.path.join("downloads", f"{info_fallback['id']}.mp4")
                    if os.path.exists(xyz_fallback):
                        return xyz_fallback
                    x_fallback.download([original_link])
                    return xyz_fallback
                except Exception as e_fallback:
                    print(f"Video download (Fallback) failed: {e_fallback}")
                    return None

        def song_video_dl():
            formats = f"{format_id}+140"
            fpath = f"downloads/{title}"
            ydl_optssx = {
                "format": formats,
                "outtmpl": fpath,
                "geo_bypass_country": "US", # <-- Use 'US'
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "prefer_ffmpeg": True,
                "merge_output_format": "mp4",
            }
            try:
                # --- Try Invidious First ---
                x = yt_dlp.YoutubeDL(ydl_optssx)
                x.download([invidious_link])
                return f"{fpath}.mp4"
            except Exception as e:
                print(f"Song video (Invidious) failed: {e}. Trying fallback.")
                # --- FALLBACK ---
                try:
                    x_fallback = yt_dlp.YoutubeDL(ydl_optssx)
                    x_fallback.download([original_link])
                    return f"{fpath}.mp4"
                except Exception as e_fallback:
                    print(f"Song video download (Fallback) failed: {e_fallback}")
                    return None

        def song_audio_dl():
            fpath = f"downloads/{title}.%(ext)s"
            ydl_optssx = {
                "format": format_id,
                "outtmpl": fpath,
                "geo_bypass_country": "US", # <-- Use 'US'
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "prefer_ffmpeg": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
            try:
                # --- Try Invidious First ---
                x = yt_dlp.YoutubeDL(ydl_optssx)
                x.download([invidious_link])
                return f"downloads/{title}.mp3"
            except Exception as e:
                print(f"Song audio (Invidious) failed: {e}. Trying fallback.")
                # --- FALLBACK ---
                try:
                    x_fallback = yt_dlp.YoutubeDL(ydl_optssx)
                    x_fallback.download([original_link])
                    return f"downloads/{title}.mp3"
                except Exception as e_fallback:
                    print(f"Song audio download (Fallback) failed: {e_fallback}")
                    return None

        try:
            if songvideo:
                downloaded_file = await loop.run_in_executor(None, song_video_dl)
                return downloaded_file, True
            elif songaudio:
                downloaded_file = await loop.run_in_executor(None, song_audio_dl)
                return downloaded_file, True
            elif video:
                if await is_on_off(1):
                    direct = True
                    downloaded_file = await loop.run_in_executor(None, video_dl)
                else:
                    # This block (getting direct link) is already handled by the self.video() method
                    # which we already modified to include Invidious
                    direct = False
                    status, downloaded_file = await self.video(original_link) 
                    if status == 0:
                        # If getting direct link fails, fallback to downloading
                        direct = True
                        downloaded_file = await loop.run_in_executor(None, video_dl)
            else:
                direct = True
                downloaded_file = await loop.run_in_executor(None, audio_dl)
            
            if not downloaded_file or not os.path.exists(downloaded_file):
                print(f"Download failed: {downloaded_file}")
                return None, True
                
            file_size = os.path.getsize(downloaded_file)
            if file_size < MIN_FILE_SIZE:
                print(f"File too small: {file_size} bytes")
                os.remove(downloaded_file)
                return None, True
                
            return downloaded_file, direct
            
        except Exception as e:
            print(f"Download error: {e}")
            return None, True

# Additional function to ensure proper file format
async def ensure_audio_format(file_path: str) -> str:
    """Ensure the downloaded file is in a playable audio format"""
    if not file_path or not os.path.exists(file_path):
        return file_path
        
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.mp3':
        return file_path
        
    if file_ext == '.mp4':
        try:
            output_path = os.path.splitext(file_path)[0] + '.mp3'
            cmd = f'ffmpeg -i "{file_path}" -vn -ar 44100 -ac 2 -b:a 192k "{output_path}" -y'
            process = await asyncio.create_subprocess_shell(cmd)
            await process.wait()
            
            if os.path.exists(output_path):
                os.remove(file_path)
                return output_path
        except Exception as e:
            print(f"Format conversion failed: {e}")
            
    return file_path

# Function to check if file is playable
async def is_file_playable(file_path: str) -> bool:
    """Check if the downloaded file is playable"""
    if not file_path or not os.path.exists(file_path):
        return False
        
    file_size = os.path.getsize(file_path)
    if file_size < MIN_FILE_SIZE:
        print(f"File too small: {file_size} bytes")
        return False
        
    file_ext = os.path.splitext(file_path)[1].lower()
    playable_formats = ['.mp3', '.mp4', '.m4a', '.ogg', 'wav'] # .wav added
    
    if file_ext not in playable_formats:
        print(f"Unplayable format: {file_ext}")
        return False
        
    return True
