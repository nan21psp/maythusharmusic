import asyncio
import os
import re
import json
from typing import Union, Tuple
import yt_dlp

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
# from youtubesearchpython.__future__ import VideosSearch  # <-- ဖြုတ်လိုက်ပါပြီ
from maythusharmusic.utils.database import is_on_off
# from maythusharmusic.utils.formatters import time_to_seconds # <-- ဖြုတ်လိုက်ပါပြီ
# from config import API_BASE_URL, API_KEY # <-- ဖြုတ်လိုက်ပါပြီ

# import glob # <-- ဖြုတ်လိုက်ပါပြီ
# import random # <-- ဖြုတ်လိုက်ပါပြီ
import logging
# import requests # <-- ဖြုတ်လိုက်ပါပြီ
import time


# ✅ Configurable constants
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
    
# api_dl function ကို ဖြုတ်လိုက်ပါပြီ
# cookie_txt_file function ကို ဖြုတ်လိုက်ပါပြီ

async def check_file_size(link):
    async def get_format_info(link):
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            # "--cookies", cookie_txt_file(), # <-- ဖြုတ်လိုက်ပါပြီ
            "--geo-bypass",  # <-- geo-bypass ထည့်သွင်းထားပါသည်
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
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    # Helper function to extract info with yt-dlp
    async def _extract_info(self, link: str, search: bool = False):
        ytdl_opts = {
            'quiet': True,
            'no_warnings': True,
            'geo_bypass': True,  # <-- Location problem အတွက် အဓိက ပြင်ဆင်မှု
            'skip_download': True,
        }

        # If it's a search query, prepend 'ytsearch:'
        if search and not link.startswith("http"):
            link = f"ytsearch:{link}"
        
        try:
            ydl = yt_dlp.YoutubeDL(ytdl_opts)
            loop = asyncio.get_running_loop()
            
            # Use extract_info, which works for both links and search queries
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(link, download=False))

            if 'entries' in info and info['entries']:
                # It was a search or playlist, return the first entry
                return info['entries'][0]
            elif 'id' in info:
                # It was a direct link
                return info
            else:
                raise ValueError("No video information found.")

        except Exception as e:
            print(f"Failed to fetch details using yt-dlp: {e}")
            raise e

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if re.search(self.regex, link):
            return True
        else:
            return False

    async def url(self, message_1: Message) -> Union[str, None]:
        # This function doesn't make external calls, so it's fine
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
        
        result = await self._extract_info(link, search=True) # Use search=True to handle non-links

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
        
        thumbnail = "http://googleusercontent.com/youtube.com/4" # default
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
        return "http://googleusercontent.com/youtube.com/4" # default

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--geo-bypass", # <-- Added geo-bypass
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
        
        # This was already fixed to use geo-bypass
        playlist = await shell_cmd(
            f"yt-dlp -i --geo-bypass --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
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
        ytdl_opts = {"quiet": True, "geo_bypass" : True} # <-- This was already fixed
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

        # Use yt-dlp search instead
        ytdl_opts = {
            'quiet': True,
            'no_warnings': True,
            'geo_bypass': True,
            'skip_download': True,
            'default_search': 'ytsearch10', # Search for 10 results
        }
        
        try:
            ydl = yt_dlp.YoutubeDL(ytdl_opts)
            loop = asyncio.get_running_loop()
            
            # Use 'link' as the search query
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(link, download=False))

            if 'entries' not in info or not info['entries'] or len(info['entries']) <= query_type:
                raise ValueError("Not enough search results for slider.")

            result = info['entries'][query_type] # Get the specific result by index

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
            
        except Exception as e:
            print(f"Failed to fetch slider details using yt-dlp: {e}")
            raise e

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
        # This function was already fixed in the previous response
        # to use yt-dlp with geo-bypass and no cookies.
        if videoid:
            link = self.base + link
        loop = asyncio.get_running_loop()
        
        def audio_dl():
            ydl_optssx = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
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
                x = yt_dlp.YoutubeDL(ydl_optssx)
                info = x.extract_info(link, False)
                xyz = os.path.join("downloads", f"{info['id']}.mp3")
                if os.path.exists(xyz):
                    return xyz
                x.download([link])
                return xyz
            except Exception as e:
                print(f"yt-dlp audio failed: {e}")
                return None

        def video_dl():
            ydl_optssx = {
                "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "merge_output_format": "mp4",
            }
            
            try:
                x = yt_dlp.YoutubeDL(ydl_optssx)
                info = x.extract_info(link, False)
                xyz = os.path.join("downloads", f"{info['id']}.mp4")
                if os.path.exists(xyz):
                    return xyz
                x.download([link])
                return xyz
            except Exception as e:
                print(f"Video download failed: {e}")
                return None

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
            try:
                x = yt_dlp.YoutubeDL(ydl_optssx)
                x.download([link])
                return f"{fpath}.mp4"
            except Exception as e:
                print(f"Song video download failed: {e}")
                return None

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
                        "preferredquality": "192",
                    }
                ],
            }
            try:
                x = yt_dlp.YoutubeDL(ydl_optssx)
                x.download([link])
                return f"downloads/{title}.mp3"
            except Exception as e:
                print(f"Song audio download failed: {e}")
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
                    proc = await asyncio.create_subprocess_exec(
                        "yt-dlp",
                        "--geo-bypass", # <-- Already fixed
                        "-g",
                        "-f",
                        "best[height<=?720][width<=?1280]",
                        f"{link}",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await proc.communicate()
                    if stdout:
                        downloaded_file = stdout.decode().split("\n")[0]
                        direct = False
                    else:
                        file_size = await check_file_size(link)
                        if not file_size:
                            print("None file Size")
                            return None, True
                        total_size_mb = file_size / (1024 * 1024)
                        if total_size_mb > 250:
                            print(f"File size {total_size_mb:.2f} MB exceeds the 250MB limit.")
                            return None, True
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
    
    # If it's already mp3, return as is
    if file_ext == '.mp3':
        return file_path
        
    # If it's mp4 but we need audio, convert to mp3
    if file_ext == '.mp4':
        try:
            output_path = os.path.splitext(file_path)[0] + '.mp3'
            cmd = f'ffmpeg -i "{file_path}" -vn -ar 44100 -ac 2 -b:a 192k "{output_path}" -y'
            process = await asyncio.create_subprocess_shell(cmd)
            await process.wait()
            
            if os.path.exists(output_path):
                os.remove(file_path)  # Remove original mp4
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
    playable_formats = ['.mp3', '.mp4', '.m4a', '.ogg', '.wav']
    
    if file_ext not in playable_formats:
        print(f"Unplayable format: {file_ext}")
        return False
        
    return True
