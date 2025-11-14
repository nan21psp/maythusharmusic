import random
import string
import os 
import logging 
import asyncio 

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InputMediaPhoto, Message
from pytgcalls.exceptions import NoActiveGroupCall

import config
from maythusharmusic import Apple, Resso, SoundCloud, Spotify, Telegram, YouTube, app
from maythusharmusic.core.call import Hotty
from maythusharmusic.utils import seconds_to_min, time_to_seconds
from maythusharmusic.utils.channelplay import get_channeplayCB
from maythusharmusic.utils.decorators.language import languageCB
from maythusharmusic.utils.decorators.play import PlayWrapper
from maythusharmusic.utils.formatters import formats
from maythusharmusic.utils.inline import (
    botplaylist_markup,
    livestream_markup,
    playlist_markup,
    slider_markup,
    track_markup,
)
from maythusharmusic.utils.logger import play_logs
from maythusharmusic.utils.stream.stream import stream

# --- START: DB Cache Imports (L1 & L2) ---
from config import BANNED_USERS, lyrical, STORAGE_CHANNEL_ID
from maythusharmusic.utils.database import (
    get_cached_track, 
    save_cached_track,
    get_search_query,  
    save_search_query  
)
# --- END: DB Cache Imports ---

logger = logging.getLogger(__name__)


@app.on_message(
    filters.command(
        [
            "play",
            "vplay",
            "cplay",
            "cvplay",
            "playforce",
            "vplayforce",
            "cplayforce",
            "cvplayforce",
        ],
        prefixes=["/", ""],
    )
    & filters.group
    & ~BANNED_USERS
)
@PlayWrapper
async def play_commnd(
    client,
    message: Message,
    _,
    chat_id,
    video,
    channel,
    playmode,
    url,
    fplay,
):
    mystic = await message.reply_text(
        _["play_2"].format(channel) if channel else _["play_1"]
    )
    plist_id = None
    slider = None
    plist_type = None
    spotify = None
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    audio_telegram = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )
    video_telegram = (
        (message.reply_to_message.video or message.reply_to_message.document)
        if message.reply_to_message
        else None
    )
    
    # --- Telegram Audio/Video (Cache မလိုအပ်ပါ) ---
    if audio_telegram:
        if audio_telegram.file_size > 104857600:
            return await mystic.edit_text(_["play_5"])
        duration_min = seconds_to_min(audio_telegram.duration)
        if (audio_telegram.duration) > config.DURATION_LIMIT:
            return await mystic.edit_text(
                _["play_6"].format(config.DURATION_LIMIT_MIN, app.mention)
            )
        file_path = await Telegram.get_filepath(audio=audio_telegram)
        if await Telegram.download(_, message, mystic, file_path):
            message_link = await Telegram.get_link(message)
            file_name = await Telegram.get_filename(audio_telegram, audio=True)
            dur = await Telegram.get_duration(audio_telegram, file_path)
            details = {
                "title": file_name,
                "link": message_link,
                "path": file_path,
                "dur": dur, 
            }

            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    streamtype="telegram",
                    forceplay=fplay,
                )
            except Exception as e:
                print(f"Error: {e}")
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                return await mystic.edit_text(err)
            return await mystic.delete()
        return
    elif video_telegram:
        if message.reply_to_message.document:
            try:
                ext = video_telegram.file_name.split(".")[-1]
                if ext.lower() not in formats:
                    return await mystic.edit_text(
                        _["play_7"].format(f"{' | '.join(formats)}")
                    )
            except:
                return await mystic.edit_text(
                    _["play_7"].format(f"{' | '.join(formats)}")
                )
        if video_telegram.file_size > config.TG_VIDEO_FILESIZE_LIMIT:
            return await mystic.edit_text(_["play_8"])
        file_path = await Telegram.get_filepath(video=video_telegram)
        if await Telegram.download(_, message, mystic, file_path):
            message_link = await Telegram.get_link(message)
            file_name = await Telegram.get_filename(video_telegram)
            dur = await Telegram.get_duration(video_telegram, file_path)
            details = {
                "title": file_name,
                "link": message_link,
                "path": file_path,
                "dur": dur, 
            }
            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    video=True,
                    streamtype="telegram",
                    forceplay=fplay,
                )
            except Exception as e:
                print(f"Error: {e}")
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                return await mystic.edit_text(err)
            return await mystic.delete()
        return
    
    # --- URL or Search Query ---
    elif url:
        if await YouTube.exists(url):
            if "playlist" in url:
                try:
                    details = await YouTube.playlist(
                        url,
                        config.PLAYLIST_FETCH_LIMIT,
                        message.from_user.id,
                    )
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "yt"
                if "&" in url:
                    plist_id = (url.split("=")[1]).split("&")[0]
                else:
                    plist_id = url.split("=")[1]
                img = config.PLAYLIST_IMG_URL
                cap = _["play_9"]
            else:
                try:
                    details, track_id = await YouTube.track(url)
                    if "duration_min" in details:
                        details["dur"] = details["duration_min"] 
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "youtube"
                img = details["thumb"]
                cap = _["play_10"].format(
                    details["title"],
                    details["duration_min"],
                )
        elif await Spotify.valid(url):
            spotify = True
            if not config.SPOTIFY_CLIENT_ID and not config.SPOTIFY_CLIENT_SECRET:
                return await mystic.edit_text(
                    "» sᴘᴏᴛɪғʏ ɪs ɴᴏᴛ sᴜᴘᴘᴏʀᴛᴇᴅ ʏᴇᴛ.\n\nᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ."
                )
            if "track" in url:
                try:
                    details, track_id = await Spotify.track(url)
                    if "duration_min" in details:
                        details["dur"] = details["duration_min"] 
                except Exception as e:
                    print(f"play_3 error: fail to process your query | Exception: {e}")
                    return await mystic.edit_text(_["play_3"])
                streamtype = "youtube"
                img = details["thumb"]
                cap = _["play_10"].format(details["title"], details["duration_min"])
            elif "playlist" in url:
                try:
                    details, plist_id = await Spotify.playlist(url)
                except Exception as e:
                    print(f"play_3 error: fail to process your query | Exception: {e}")
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "spplay"
                img = config.SPOTIFY_PLAYLIST_IMG_URL
                cap = _["play_11"].format(app.mention, message.from_user.mention)
            elif "album" in url:
                try:
                    details, plist_id = await Spotify.album(url)
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "spalbum"
                img = config.SPOTIFY_ALBUM_IMG_URL
                cap = _["play_11"].format(app.mention, message.from_user.mention)
            elif "artist" in url:
                try:
                    details, plist_id = await Spotify.artist(url)
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "spartist"
                img = config.SPOTIFY_ARTIST_IMG_URL
                cap = _["play_11"].format(message.from_user.first_name)
            else:
                return await mystic.edit_text(_["play_15"])
        elif await Apple.valid(url):
            if "album" in url:
                try:
                    details, track_id = await Apple.track(url)
                    if "duration_min" in details:
                        details["dur"] = details["duration_min"] 
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "youtube"
                img = details["thumb"]
                cap = _["play_10"].format(details["title"], details["duration_min"])
            elif "playlist" in url:
                spotify = True
                try:
                    details, plist_id = await Apple.playlist(url)
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "apple"
                cap = _["play_12"].format(app.mention, message.from_user.mention)
                img = url
            else:
                return await mystic.edit_text(_["play_3"])
        elif await Resso.valid(url):
            try:
                details, track_id = await Resso.track(url)
                if "duration_min" in details:
                    details["dur"] = details["duration_min"] 
            except:
                return await mystic.edit_text(_["play_3"])
            streamtype = "youtube"
            img = details["thumb"]
            cap = _["play_10"].format(details["title"], details["duration_min"])
        elif await SoundCloud.valid(url):
            try:
                details, track_path = await SoundCloud.download(url)
                details["path"] = track_path 
                details["dur"] = details["duration_min"] 
            except:
                return await mystic.edit_text(_["play_3"])
            duration_sec = details["duration_sec"]
            if duration_sec > config.DURATION_LIMIT:
                return await mystic.edit_text(
                    _["play_6"].format(
                        config.DURATION_LIMIT_MIN,
                        app.mention,
                    )
                )
            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    streamtype="soundcloud", 
                    forceplay=fplay,
                )
            except Exception as e:
                print(f"Error: {e}")
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                return await mystic.edit_text(err)
            return await mystic.delete()
        else:
            try:
                await Hotty.stream_call(url)
            except NoActiveGroupCall:
                await mystic.edit_text(_["black_9"])
                return await app.send_message(
                    chat_id=config.LOG_GROUP_ID,
                    text=_["play_17"],
                )
            except Exception as e:
                print(f"Error: {e}")
                return await mystic.edit_text(_["general_2"].format(type(e).__name__))
            await mystic.edit_text(_["str_2"])
            try:
                await stream(
                    _,
                    mystic,
                    message.from_user.id,
                    url,
                    chat_id,
                    message.from_user.first_name,
                    message.chat.id,
                    video=video,
                    streamtype="index",
                    forceplay=fplay,
                )
            except Exception as e:
                print(f"Error: {e}")
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                return await mystic.edit_text(err)
            return await play_logs(message, streamtype="M3u8 or Index Link")
    
    # --- START: L1 (Search Query) Cache Logic ---
    else:
        if len(message.command) < 2:
            buttons = botplaylist_markup(_)
            return await mystic.edit_text(
                _["play_18"],
                reply_markup=InlineKeyboardMarkup(buttons),
            )
        slider = True
        query = message.text.split(None, 1)[1]
        if "-v" in query:
            query = query.replace("-v", "")

        track_id = None
        details = None
        
        cached_search_details = await get_search_query(query)
        
        if cached_search_details:
            logger.info(f"[L1 Cache HIT] Found search query: {query}")
            details = cached_search_details
            track_id = details["vidid"]
            
            if "dur" not in details and "duration_min" in details:
                details["dur"] = details["duration_min"]
                
        else:
            logger.info(f"[L1 Cache MISS] Searching YouTube for: {query}")
            try:
                details, track_id = await YouTube.track(query)
                
                current_duration = details.get("duration_min")
                details["dur"] = current_duration 
                
                clean_details = {
                    "title": details.get("title"),
                    "link": details.get("link"),
                    "vidid": details.get("vidid"),
                    "duration_min": current_duration,
                    "thumb": details.get("thumb"),
                    "dur": current_duration, 
                }
                asyncio.create_task(save_search_query(query, clean_details))
                
            except Exception as e:
                logger.error(f"YouTube.track failed for query '{query}': {e}")
                return await mystic.edit_text(_["play_3"])
        
        if not details or not track_id:
             return await mystic.edit_text(_["play_3"])
        
        streamtype = "youtube"
    # --- END: L1 (Search Query) Cache Logic ---


    # --- Playmode Logic (Direct or Inline) ---
    if str(playmode) == "Direct":
        if not plist_type: 
            if details["duration_min"]:
                duration_sec = time_to_seconds(details["duration_min"])
                if duration_sec > config.DURATION_LIMIT:
                    return await mystic.edit_text(
                        _["play_6"].format(config.DURATION_LIMIT_MIN, app.mention)
                    )
            else: 
                buttons = livestream_markup(
                    _,
                    track_id,
                    user_id,
                    "v" if video else "a",
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )
                return await mystic.edit_text(
                    _["play_13"],
                    reply_markup=InlineKeyboardMarkup(buttons),
                )

        # --- START: L2 (File ID) Cache Logic (Single Tracks Only) ---
        if not plist_type and streamtype == "youtube":
            video_id = details.get("vidid")
            title = details.get("title")
            duration_min = details.get("duration_min")

            cached_track = await get_cached_track(video_id)
            
            if cached_track:
                # --- L2 CACHE HIT ---
                logger.info(f"[L2 Cache HIT] Playing from DB: {title} ({video_id})")
                
                details = cached_track 
                details["path"] = cached_track["file_id"] 
                
                if "dur" not in details and "duration_min" in details:
                    details["dur"] = details["duration_min"]
                
                try:
                    await stream(
                        _,
                        mystic,
                        user_id,
                        details, 
                        chat_id,
                        user_name,
                        message.chat.id,
                        video=video,
                        streamtype="telegram", 
                        spotify=spotify,
                        forceplay=fplay,
                    )
                except Exception as e:
                    print(f"Error: {e}")
                    ex_type = type(e).__name__
                    err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                    return await mystic.edit_text(err)
                
                await mystic.delete()
                return await play_logs(message, streamtype="Cached YouTube")
            
            else:
                # --- L2 CACHE MISS ---
                logger.info(f"[L2 Cache MISS] Downloading: {title} ({video_id})")
                await mystic.edit_text(f"📥 Download ဆွဲနေပါသည်: {title}")
                
                downloaded_path = None
                try:
                    # --- [FIX] _ ကို _direct လို့ ပြောင်းလိုက်ပါ ---
                    downloaded_path, _direct = await YouTube.download(
                        link=details["link"],
                        mystic=mystic,
                        video=video, 
                    )
                    
                    if not downloaded_path or not os.path.exists(downloaded_path):
                        raise Exception("Download failed, file path not found.")

                    details["path"] = downloaded_path 
                    
                    await stream(
                        _,
                        mystic,
                        user_id,
                        details, 
                        chat_id,
                        user_name,
                        message.chat.id,
                        video=video,
                        streamtype="telegram", 
                        spotify=spotify,
                        forceplay=fplay,
                    )
                    
                    async def cache_and_cleanup():
                        try:
                            sent_media = None
                            if video:
                                sent_media = await app.send_video(
                                    chat_id=STORAGE_CHANNEL_ID,
                                    video=downloaded_path,
                                    caption=f"Title: {title}\nID: {video_id}\nDuration: {duration_min}"
                                )
                                file_id_to_cache = sent_media.video.file_id
                            else:
                                sent_media = await app.send_audio(
                                    chat_id=STORAGE_CHANNEL_ID,
                                    audio=downloaded_path,
                                    caption=f"Title: {title}\nID: {video_id}\nDuration: {duration_min}"
                                )
                                file_id_to_cache = sent_media.audio.file_id
                            
                            await save_cached_track(
                                video_id=video_id,
                                file_id=file_id_to_cache,
                                title=title,
                                duration=duration_min 
                            )
                        except Exception as e:
                            logger.error(f"Failed to cache to storage channel: {e}")
                        finally:
                            if os.path.exists(downloaded_path):
                                os.remove(downloaded_path)
                    
                    asyncio.create_task(cache_and_cleanup()) 
                    
                    await mystic.delete()
                    return await play_logs(message, streamtype="Downloaded YouTube")

                except Exception as e:
                    if downloaded_path and os.path.exists(downloaded_path):
                        os.remove(downloaded_path) 
                    print(f"Error: {e}")
                    ex_type = type(e).__name__
                    err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                    return await mystic.edit_text(err)
        
        else:
            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    video=video,
                    streamtype=streamtype,
                    spotify=spotify,
                    forceplay=fplay,
                )
            except Exception as e:
                print(f"Error: {e}")
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                return await mystic.edit_text(err)
            
            await mystic.delete()
            return await play_logs(message, streamtype=streamtype)
    
    # --- Inline Mode (Buttons) ---
    else:
        if plist_type:
            ran_hash = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=10)
            )
            lyrical[ran_hash] = plist_id
            buttons = playlist_markup(
                _,
                ran_hash,
                message.from_user.id,
                plist_type,
                "c" if channel else "g",
                "f" if fplay else "d",
            )
            await mystic.delete()
            await message.reply_photo(
                photo=img,
                caption=cap,
                reply_markup=InlineKeyboardMarkup(buttons),
            )
            return await play_logs(message, streamtype=f"Playlist : {plist_type}")
        else:
            if slider:
                buttons = slider_markup(
                    _,
                    track_id,
                    message.from_user.id,
                    query,
                    0,
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )
                await mystic.delete()
                await message.reply_photo(
                    photo=details["thumb"],
                    caption=_["play_10"].format(
                        details["title"].title(),
                        details["duration_min"],
                    ),
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
                return await play_logs(message, streamtype=f"Searched on Youtube")
            else:
                buttons = track_markup(
                    _,
                    track_id,
                    message.from_user.id,
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )
                await mystic.delete()
                await message.reply_photo(
                    photo=img,
                    caption=cap,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
                return await play_logs(message, streamtype=f"URL Searched Inline")


@app.on_callback_query(filters.regex("MusicStream") & ~BANNED_USERS)
@languageCB
async def play_music(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    vidid, user_id, mode, cplay, fplay = callback_request.split("|")
    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(_["playcb_1"], show_alert=True)
        except:
            return
    try:
        chat_id, channel = await get_channeplayCB(_, cplay, CallbackQuery)
    except:
        return
    user_name = CallbackQuery.from_user.first_name
    try:
        await CallbackQuery.message.delete()
        await CallbackQuery.answer()
    except:
        pass
    mystic = await CallbackQuery.message.reply_text(
        _["play_2"].format(channel) if channel else _["play_1"]
    )
    try:
        details, track_id = await YouTube.track(vidid, True)
        if "duration_min" in details:
            details["dur"] = details["duration_min"] 
    except:
        return await mystic.edit_text(_["play_3"])
    
    if details["duration_min"]:
        duration_sec = time_to_seconds(details["duration_min"])
        if duration_sec > config.DURATION_LIMIT:
            return await mystic.edit_text(
                _["play_6"].format(config.DURATION_LIMIT_MIN, app.mention)
            )
    else:
        buttons = livestream_markup(
            _,
            track_id,
            CallbackQuery.from_user.id,
            mode,
            "c" if cplay == "c" else "g",
            "f" if fplay else "d",
        )
        return await mystic.edit_text(
            _["play_13"],
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    
    video = True if mode == "v" else None
    ffplay = True if fplay == "f" else None
    
    # --- START: L2 (File ID) Cache Logic (Callback) ---
    video_id = details.get("vidid")
    title = details.get("title")
    duration_min = details.get("duration_min")

    cached_track = await get_cached_track(video_id)
    
    if cached_track:
        # --- L2 CACHE HIT ---
        logger.info(f"[L2 Cache HIT] Playing from DB: {title} ({video_id})")
        
        details = cached_track
        details["path"] = cached_track["file_id"]

        if "dur" not in details and "duration_min" in details:
            details["dur"] = details["duration_min"]
        
        try:
            await stream(
                _,
                mystic,
                CallbackQuery.from_user.id,
                details, 
                chat_id,
                user_name,
                CallbackQuery.message.chat.id,
                video,
                streamtype="telegram", 
                forceplay=ffplay,
            )
        except Exception as e:
            print(f"Error: {e}")
            ex_type = type(e).__name__
            err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
            return await mystic.edit_text(err)
        
        return await mystic.delete()

    else:
        # --- L2 CACHE MISS ---
        logger.info(f"[L2 Cache MISS] Downloading: {title} ({video_id})")
        await mystic.edit_text(f"📥 Download ဆွဲနေပါသည်: {title}")
        
        downloaded_path = None
        try:
            # --- [FIX] _ ကို _direct လို့ ပြောင်းလိုက်ပါ ---
            downloaded_path, _direct = await YouTube.download(
                link=details["link"],
                mystic=mystic,
                video=video,
            )
            
            if not downloaded_path or not os.path.exists(downloaded_path):
                raise Exception("Download failed, file path not found.")

            details["path"] = downloaded_path
            
            await stream(
                _,
                mystic,
                CallbackQuery.from_user.id,
                details, 
                chat_id,
                user_name,
                CallbackQuery.message.chat.id,
                video,
                streamtype="telegram", 
                forceplay=ffplay,
            )
            
            async def cache_and_cleanup():
                try:
                    sent_media = None
                    if video:
                        sent_media = await app.send_video(
                            chat_id=STORAGE_CHANNEL_ID,
                            video=downloaded_path,
                            caption=f"Title: {title}\nID: {video_id}\nDuration: {duration_min}"
                        )
                        file_id_to_cache = sent_media.video.file_id
                    else:
                        sent_media = await app.send_audio(
                            chat_id=STORAGE_CHANNEL_ID,
                            audio=downloaded_path,
                            caption=f"Title: {title}\nID: {video_id}\nDuration: {duration_min}"
                        )
                        file_id_to_cache = sent_media.audio.file_id
                    
                    await save_cached_track(
                        video_id=video_id,
                        file_id=file_id_to_cache,
                        title=title,
                        duration=duration_min
                    )
                except Exception as e:
                    logger.error(f"Failed to cache to storage channel: {e}")
                finally:
                    if os.path.exists(downloaded_path):
                        os.remove(downloaded_path)
            
            asyncio.create_task(cache_and_cleanup())
            
            return await mystic.delete()

        except Exception as e:
            if downloaded_path and os.path.exists(downloaded_path):
                os.remove(downloaded_path)
            print(f"Error: {e}")
            ex_type = type(e).__name__
            err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
            return await mystic.edit_text(err)
    # --- END: L2 (File ID) Cache Logic ---


@app.on_callback_query(filters.regex("AnonymousAdmin") & ~BANNED_USERS)
async def anonymous_check(client, CallbackQuery):
    try:
        await CallbackQuery.answer(
            "» ʀᴇᴠᴇʀᴛ ʙᴀᴄᴋ ᴛᴏ ᴜsᴇʀ ᴀᴄᴄᴏᴜɴᴛ :\n\nᴏᴘᴇɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ sᴇᴛᴛɪɴɢs.\n-> ᴀᴅᴍɪɴɪsᴛʀᴀᴛᴏʀs\n-> ᴄʟɪᴄᴋ ᴏɴ ʏᴏᴜʀ ɴᴀᴍᴇ\n-> ᴜɴᴄʜᴇᴄᴋ ᴀɴᴏɴʏᴍᴏᴜs ᴀᴅᴍɪɴ ᴘᴇʀᴍɪssɪᴏɴs.",
            show_alert=True,
        )
    except:
        pass


@app.on_callback_query(filters.regex("HottyPlaylists") & ~BANNED_USERS)
@languageCB
async def play_playlists_command(client, CallbackQuery, _):
    # (Playlist ဖွင့်တာဖြစ်လို့ Cache Logic မထည့်ပါ)
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    (
        videoid,
        user_id,
        ptype,
        mode,
        cplay,
        fplay,
    ) = callback_request.split("|")
    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(_["playcb_1"], show_alert=True)
        except:
            return
    try:
        chat_id, channel = await get_channeplayCB(_, cplay, CallbackQuery)
    except:
        return
    user_name = CallbackQuery.from_user.first_name
    await CallbackQuery.message.delete()
    try:
        await CallbackQuery.answer()
    except:
        pass
    mystic = await CallbackQuery.message.reply_text(
        _["play_2"].format(channel) if channel else _["play_1"]
    )
    videoid = lyrical.get(videoid)
    video = True if mode == "v" else None
    ffplay = True if fplay == "f" else None
    spotify = True
    if ptype == "yt":
        spotify = False
        try:
            result = await YouTube.playlist(
                videoid,
                config.PLAYLIST_FETCH_LIMIT,
                CallbackQuery.from_user.id,
                True,
            )
        except:
            return await mystic.edit_text(_["play_3"])
    if ptype == "spplay":
        try:
            result, spotify_id = await Spotify.playlist(videoid)
        except:
            return await mystic.edit_text(_["play_3"])
    if ptype == "spalbum":
        try:
            result, spotify_id = await Spotify.album(videoid)
        except:
            return await mystic.edit_text(_["play_3"])
    if ptype == "spartist":
        try:
            result, spotify_id = await Spotify.artist(videoid)
        except:
            return await mystic.edit_text(_["play_3"])
    if ptype == "apple":
        try:
            result, apple_id = await Apple.playlist(videoid, True)
        except:
            return await mystic.edit_text(_["play_3"])
    try:
        await stream(
            _,
            mystic,
            user_id,
            result,
            chat_id,
            user_name,
            CallbackQuery.message.chat.id,
            video,
            streamtype="playlist",
            spotify=spotify,
            forceplay=ffplay,
        )
    except Exception as e:
        print(f"Error: {e}")
        ex_type = type(e).__name__
        err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
        return await mystic.edit_text(err)
    return await mystic.delete()


@app.on_callback_query(filters.regex("slider") & ~BANNED_USERS)
@languageCB
async def slider_queries(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    (
        what,
        rtype,
        query,
        user_id,
        cplay,
        fplay,
    ) = callback_request.split("|")
    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(_["playcb_1"], show_alert=True)
        except:
            return
    what = str(what)
    rtype = int(rtype)
    if what == "F":
        if rtype == 9:
            query_type = 0
        else:
            query_type = int(rtype + 1)
        try:
            await CallbackQuery.answer(_["playcb_2"])
        except:
            pass
        title, duration_min, thumbnail, vidid = await YouTube.slider(query, query_type)
        buttons = slider_markup(_, vidid, user_id, query, query_type, cplay, fplay)
        med = InputMediaPhoto(
            media=thumbnail,
            caption=_["play_10"].format(
                title.title(),
                duration_min,
            ),
        )
        return await CallbackQuery.edit_message_media(
            media=med, reply_markup=InlineKeyboardMarkup(buttons)
        )
    if what == "B":
        if rtype == 0:
            query_type = 9
        else:
            query_type = int(rtype - 1)
        try:
            await CallbackQuery.answer(_["playcb_2"])
        except:
            pass
        title, duration_min, thumbnail, vidid = await YouTube.slider(query, query_type)
        buttons = slider_markup(_, vidid, user_id, query, query_type, cplay, fplay)
        med = InputMediaPhoto(
            media=thumbnail,
            caption=_["play_10"].format(
                title.title(),
                duration_min,
            ),
        )
        return await CallbackQuery.edit_message_media(
            media=med, reply_markup=InlineKeyboardMarkup(buttons)
        )
