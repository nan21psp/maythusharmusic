import asyncio
import os
import traceback
from datetime import datetime, timedelta
from typing import Union

from ntgcalls import TelegramServerError
from pyrogram import Client
from pyrogram.errors import FloodWait, ChatAdminRequired
from pyrogram.types import InlineKeyboardMarkup
from pytgcalls import PyTgCalls
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.types import AudioQuality, ChatUpdate, MediaStream, StreamEnded, Update, VideoQuality

import config
from strings import get_string
from maythusharmusic import LOGGER, YouTube, app
from maythusharmusic.misc import db
from maythusharmusic.utils.database import (
    add_active_chat,
    add_active_video_chat,
    get_lang,
    get_loop,
    group_assistant,
    is_autoend,
    music_on,
    remove_active_chat,
    remove_active_video_chat,
    set_loop,
)
from maythusharmusic.utils.exceptions import AssistantErr
from maythusharmusic.utils.formatters import check_duration, seconds_to_min, speed_converter
from maythusharmusic.utils.inline.play import stream_markup
from maythusharmusic.utils.stream.autoclear import auto_clean
from maythusharmusic.utils.thumbnails import get_thumb
from maythusharmusic.utils.errors import capture_internal_err, send_large_error

# Global variables for stream management
autoend = {}
counter = {}


def dynamic_media_stream(path: str, video: bool = False, ffmpeg_params: str = None) -> MediaStream:
    """
    Create a dynamic media stream configuration with optimized audio/video quality
    """
    return MediaStream(
        audio_path=path,
        media_path=path,
        audio_parameters=AudioQuality.STUDIO,  # Always use studio quality audio
        video_parameters=VideoQuality.HD_720p if video else VideoQuality.SD_360p,
        video_flags=(MediaStream.Flags.AUTO_DETECT if video else MediaStream.Flags.IGNORE),
        ffmpeg_parameters=ffmpeg_params,
    )


async def _clear_(chat_id: int) -> None:
    """
    Clear all data and cleanup for a specific chat
    """
    try:
        popped = db.pop(chat_id, None)
        if popped:
            await auto_clean(popped)
        
        db[chat_id] = []
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        await set_loop(chat_id, 0)
        
        LOGGER(__name__).info(f"Cleared all data for chat {chat_id}")
    except Exception as e:
        LOGGER(__name__).error(f"Error clearing chat {chat_id}: {e}")


class Call:
    """
    Main call handler class for managing multiple PyTgCalls instances
    """
    
    def __init__(self):
        # Initialize multiple client instances for load balancing
        self.clients = []
        self.assistants = []
        
        # Client 1
        if config.STRING1:
            self.userbot1 = Client(
                "maythusharmusic1", 
                config.API_ID, 
                config.API_HASH, 
                session_string=config.STRING1
            )
            self.one = PyTgCalls(self.userbot1)
            self.clients.append(self.userbot1)
            self.assistants.append(self.one)
        else:
            self.userbot1 = None
            self.one = None

        # Client 2
        if config.STRING2:
            self.userbot2 = Client(
                "maythusharmusic2", 
                config.API_ID, 
                config.API_HASH, 
                session_string=config.STRING2
            )
            self.two = PyTgCalls(self.userbot2)
            self.clients.append(self.userbot2)
            self.assistants.append(self.two)
        else:
            self.userbot2 = None
            self.two = None

        # Client 3
        if config.STRING3:
            self.userbot3 = Client(
                "maythusharmusic3", 
                config.API_ID, 
                config.API_HASH, 
                session_string=config.STRING3
            )
            self.three = PyTgCalls(self.userbot3)
            self.clients.append(self.userbot3)
            self.assistants.append(self.three)
        else:
            self.userbot3 = None
            self.three = None

        # Client 4
        if config.STRING4:
            self.userbot4 = Client(
                "maythusharmusic4", 
                config.API_ID, 
                config.API_HASH, 
                session_string=config.STRING4
            )
            self.four = PyTgCalls(self.userbot4)
            self.clients.append(self.userbot4)
            self.assistants.append(self.four)
        else:
            self.userbot4 = None
            self.four = None

        # Client 5
        if config.STRING5:
            self.userbot5 = Client(
                "maythusharmusic5", 
                config.API_ID, 
                config.API_HASH, 
                session_string=config.STRING5
            )
            self.five = PyTgCalls(self.userbot5)
            self.clients.append(self.userbot5)
            self.assistants.append(self.five)
        else:
            self.userbot5 = None
            self.five = None

        # Track active calls
        self.active_calls: set[int] = set()
        
        LOGGER(__name__).info(f"Initialized {len(self.assistants)} PyTgCalls assistants")


    @capture_internal_err
    async def pause_stream(self, chat_id: int) -> None:
        """Pause the current stream"""
        assistant = await group_assistant(self, chat_id)
        await assistant.pause(chat_id)
        LOGGER(__name__).info(f"Paused stream in chat {chat_id}")


    @capture_internal_err
    async def resume_stream(self, chat_id: int) -> None:
        """Resume the paused stream"""
        assistant = await group_assistant(self, chat_id)
        await assistant.resume(chat_id)
        LOGGER(__name__).info(f"Resumed stream in chat {chat_id}")


    @capture_internal_err
    async def mute_stream(self, chat_id: int) -> None:
        """Mute the stream audio"""
        assistant = await group_assistant(self, chat_id)
        await assistant.mute(chat_id)
        LOGGER(__name__).info(f"Muted stream in chat {chat_id}")


    @capture_internal_err
    async def unmute_stream(self, chat_id: int) -> None:
        """Unmute the stream audio"""
        assistant = await group_assistant(self, chat_id)
        await assistant.unmute(chat_id)
        LOGGER(__name__).info(f"Unmuted stream in chat {chat_id}")


    @capture_internal_err
    async def stop_stream(self, chat_id: int) -> None:
        """Stop the stream and cleanup"""
        assistant = await group_assistant(self, chat_id)
        
        # Clear all data first
        await _clear_(chat_id)
        
        # Leave call if active
        if chat_id in self.active_calls:
            try:
                await assistant.leave_call(chat_id)
                LOGGER(__name__).info(f"Left call in chat {chat_id}")
            except NoActiveGroupCall:
                LOGGER(__name__).warning(f"No active call in chat {chat_id}")
            except Exception as e:
                LOGGER(__name__).error(f"Error leaving call in chat {chat_id}: {e}")
            finally:
                self.active_calls.discard(chat_id)


    @capture_internal_err
    async def force_stop_stream(self, chat_id: int) -> None:
        """Force stop stream with additional cleanup"""
        assistant = await group_assistant(self, chat_id)
        
        # Remove first item from queue
        try:
            check = db.get(chat_id)
            if check:
                check.pop(0)
                LOGGER(__name__).info(f"Removed first item from queue in chat {chat_id}")
        except (IndexError, KeyError):
            pass
        
        # Clear all active data
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        await _clear_(chat_id)
        
        # Leave call if active
        if chat_id in self.active_calls:
            try:
                await assistant.leave_call(chat_id)
                LOGGER(__name__).info(f"Force left call in chat {chat_id}")
            except NoActiveGroupCall:
                LOGGER(__name__).warning(f"No active call to force leave in chat {chat_id}")
            except Exception as e:
                LOGGER(__name__).error(f"Error force leaving call in chat {chat_id}: {e}")
            finally:
                self.active_calls.discard(chat_id)


    @capture_internal_err
    async def skip_stream(self, chat_id: int, link: str, video: Union[bool, str] = None, image: Union[bool, str] = None) -> None:
        """Skip to next stream"""
        assistant = await group_assistant(self, chat_id)
        stream = dynamic_media_stream(path=link, video=bool(video))
        await assistant.play(chat_id, stream)
        LOGGER(__name__).info(f"Skipped to next stream in chat {chat_id}")


    @capture_internal_err
    async def vc_users(self, chat_id: int) -> list:
        """Get list of users in voice chat who are not muted"""
        assistant = await group_assistant(self, chat_id)
        participants = await assistant.get_participants(chat_id)
        return [p.user_id for p in participants if not p.is_muted]


    @capture_internal_err
    async def change_volume(self, chat_id: int, volume: int) -> None:
        """Change stream volume"""
        assistant = await group_assistant(self, chat_id)
        await assistant.change_volume_call(chat_id, volume)
        LOGGER(__name__).info(f"Changed volume to {volume} in chat {chat_id}")


    @capture_internal_err
    async def seek_stream(self, chat_id: int, file_path: str, to_seek: str, duration: str, mode: str) -> None:
        """Seek to specific position in stream"""
        assistant = await group_assistant(self, chat_id)
        ffmpeg_params = f"-ss {to_seek} -to {duration}"
        is_video = mode == "video"
        stream = dynamic_media_stream(path=file_path, video=is_video, ffmpeg_params=ffmpeg_params)
        await assistant.play(chat_id, stream)
        LOGGER(__name__).info(f"Seeked stream to {to_seek} in chat {chat_id}")


    @capture_internal_err
    async def speedup_stream(self, chat_id: int, file_path: str, speed: float, playing: list) -> None:
        """Speed up or slow down the stream"""
        if not isinstance(playing, list) or not playing or not isinstance(playing[0], dict):
            raise AssistantErr("Invalid stream info for speedup.")

        assistant = await group_assistant(self, chat_id)
        base = os.path.basename(file_path)
        chatdir = os.path.join("playback", str(speed))
        os.makedirs(chatdir, exist_ok=True)
        out = os.path.join(chatdir, base)

        # Create speed-adjusted file if it doesn't exist
        if not os.path.exists(out):
            vs = str(2.0 / float(speed))
            cmd = f"ffmpeg -i {file_path} -filter:v setpts={vs}*PTS -filter:a atempo={speed} {out}"
            
            LOGGER(__name__).info(f"Creating speed-adjusted file: {cmd}")
            proc = await asyncio.create_subprocess_shell(
                cmd, 
                stdin=asyncio.subprocess.PIPE, 
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()

        # Get duration and calculate playback position
        dur = int(await asyncio.get_event_loop().run_in_executor(None, check_duration, out))
        played, con_seconds = speed_converter(playing[0]["played"], speed)
        duration_min = seconds_to_min(dur)
        is_video = playing[0]["streamtype"] == "video"
        ffmpeg_params = f"-ss {played} -to {duration_min}"
        stream = dynamic_media_stream(path=out, video=is_video, ffmpeg_params=ffmpeg_params)

        # Play the speed-adjusted stream
        if chat_id in db and db[chat_id] and db[chat_id][0].get("file") == file_path:
            await assistant.play(chat_id, stream)
            LOGGER(__name__).info(f"Speed adjusted to {speed}x in chat {chat_id}")
        else:
            raise AssistantErr("Stream mismatch during speedup.")

        # Update database with new stream info
        db[chat_id][0].update({
            "played": con_seconds,
            "dur": duration_min,
            "seconds": dur,
            "speed_path": out,
            "speed": speed,
            "old_dur": db[chat_id][0].get("dur"),
            "old_second": db[chat_id][0].get("seconds"),
        })


    @capture_internal_err
    async def stream_call(self, link: str) -> None:
        """Test stream call in logger group"""
        assistant = await group_assistant(self, config.LOGGER_ID)
        try:
            await assistant.play(config.LOGGER_ID, MediaStream(link))
            await asyncio.sleep(8)
            LOGGER(__name__).info("Test stream call completed successfully")
        except Exception as e:
            LOGGER(__name__).error(f"Test stream call failed: {e}")
        finally:
            try:
                await assistant.leave_call(config.LOGGER_ID)
            except Exception as e:
                LOGGER(__name__).warning(f"Error leaving test call: {e}")


    @capture_internal_err
    async def join_call(
        self,
        chat_id: int,
        original_chat_id: int,
        link: str,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ) -> None:
        """Join voice chat and start streaming"""
        assistant = await group_assistant(self, chat_id)
        lang = await get_lang(chat_id)
        _ = get_string(lang)
        stream = dynamic_media_stream(path=link, video=bool(video))

        try:
            await assistant.play(chat_id, stream)
            LOGGER(__name__).info(f"Successfully joined call in chat {chat_id}")
        except NoActiveGroupCall:
            raise AssistantErr(_["call_8"])
        except ChatAdminRequired:
            raise AssistantErr(_["call_9"])
        except TelegramServerError:
            raise AssistantErr(_["call_10"])
        except Exception as e:
            error_msg = f"Unable to join the group call.\nReason: {str(e)}"
            LOGGER(__name__).error(error_msg)
            raise AssistantErr(error_msg)

        # Update active calls and settings
        self.active_calls.add(chat_id)
        await add_active_chat(chat_id)
        await music_on(chat_id)
        
        if video:
            await add_active_video_chat(chat_id)
            LOGGER(__name__).info(f"Added video chat for {chat_id}")

        # Setup autoend if enabled
        if await is_autoend():
            counter[chat_id] = {}
            users = len(await assistant.get_participants(chat_id))
            if users == 1:
                autoend[chat_id] = datetime.now() + timedelta(minutes=1)
                LOGGER(__name__).info(f"Autoend scheduled for chat {chat_id}")


    @capture_internal_err
    async def play(self, client, chat_id: int) -> None:
        """Play next item in queue"""
        check = db.get(chat_id)
        popped = None
        loop = await get_loop(chat_id)
        
        try:
            if loop == 0:
                popped = check.pop(0)
                LOGGER(__name__).info(f"Removed completed track from queue in chat {chat_id}")
            else:
                loop = loop - 1
                await set_loop(chat_id, loop)
                LOGGER(__name__).info(f"Loop count updated to {loop} in chat {chat_id}")
            
            await auto_clean(popped)
            
            # Clear if queue is empty
            if not check:
                await _clear_(chat_id)
                if chat_id in self.active_calls:
                    try:
                        await client.leave_call(chat_id)
                        LOGGER(__name__).info(f"Left empty call in chat {chat_id}")
                    except NoActiveGroupCall:
                        pass
                    except Exception as e:
                        LOGGER(__name__).error(f"Error leaving empty call: {e}")
                    finally:
                        self.active_calls.discard(chat_id)
                return
                
        except Exception as e:
            LOGGER(__name__).error(f"Error in play handler: {e}")
            try:
                await _clear_(chat_id)
                await client.leave_call(chat_id)
            except Exception as e:
                LOGGER(__name__).error(f"Error during cleanup: {e}")
            return

        # Play next track
        queued = check[0]["file"]
        language = await get_lang(chat_id)
        _ = get_string(language)
        title = (check[0]["title"]).title()
        user = check[0]["by"]
        original_chat_id = check[0]["chat_id"]
        streamtype = check[0]["streamtype"]
        videoid = check[0]["vidid"]
        db[chat_id][0]["played"] = 0

        # Restore original duration if speed was adjusted
        exis = (check[0]).get("old_dur")
        if exis:
            db[chat_id][0]["dur"] = exis
            db[chat_id][0]["seconds"] = check[0]["old_second"]
            db[chat_id][0]["speed_path"] = None
            db[chat_id][0]["speed"] = 1.0

        video = True if str(streamtype) == "video" else False

        # Handle different stream types
        if "live_" in queued:
            await self._handle_live_stream(chat_id, original_chat_id, videoid, video, _, title, user, check)
            
        elif "vid_" in queued:
            await self._handle_video_stream(chat_id, original_chat_id, videoid, video, _, title, user, check, streamtype)
            
        elif "index_" in queued:
            await self._handle_index_stream(chat_id, original_chat_id, videoid, video, _, user)
            
        else:
            await self._handle_regular_stream(chat_id, original_chat_id, queued, video, _, title, user, check, streamtype, videoid)


    async def _handle_live_stream(self, chat_id, original_chat_id, videoid, video, _, title, user, check):
        """Handle live YouTube streams"""
        n, link = await YouTube.video(videoid, True)
        if n == 0:
            return await app.send_message(original_chat_id, text=_["call_6"])

        stream = dynamic_media_stream(path=link, video=video)
        try:
            assistant = await group_assistant(self, chat_id)
            await assistant.play(chat_id, stream)
        except Exception as e:
            LOGGER(__name__).error(f"Error playing live stream: {e}")
            return await app.send_message(original_chat_id, text=_["call_6"])

        img = await get_thumb(videoid)
        button = stream_markup(_, chat_id)
        run = await app.send_photo(
            chat_id=original_chat_id,
            photo=img,
            caption=_["stream_1"].format(
                f"https://t.me/{app.username}?start=info_{videoid}",
                title[:23],
                check[0]["dur"],
                user,
            ),
            reply_markup=InlineKeyboardMarkup(button),
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "tg"


    async def _handle_video_stream(self, chat_id, original_chat_id, videoid, video, _, title, user, check, streamtype):
        """Handle video streams"""
        mystic = await app.send_message(original_chat_id, _["call_7"])
        try:
            file_path, direct = await YouTube.download(
                videoid,
                mystic,
                videoid=True,
                video=True if str(streamtype) == "video" else False,
            )
        except Exception as e:
            LOGGER(__name__).error(f"Error downloading video: {e}")
            return await mystic.edit_text(_["call_6"], disable_web_page_preview=True)

        stream = dynamic_media_stream(path=file_path, video=video)
        try:
            assistant = await group_assistant(self, chat_id)
            await assistant.play(chat_id, stream)
        except Exception as e:
            LOGGER(__name__).error(f"Error playing video stream: {e}")
            return await app.send_message(original_chat_id, text=_["call_6"])

        img = await get_thumb(videoid)
        button = stream_markup(_, chat_id)
        await mystic.delete()
        run = await app.send_photo(
            chat_id=original_chat_id,
            photo=img,
            caption=_["stream_1"].format(
                f"https://t.me/{app.username}?start=info_{videoid}",
                title[:23],
                check[0]["dur"],
                user,
            ),
            reply_markup=InlineKeyboardMarkup(button),
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "stream"


    async def _handle_index_stream(self, chat_id, original_chat_id, videoid, video, _, user):
        """Handle index streams"""
        stream = dynamic_media_stream(path=videoid, video=video)
        try:
            assistant = await group_assistant(self, chat_id)
            await assistant.play(chat_id, stream)
        except Exception as e:
            LOGGER(__name__).error(f"Error playing index stream: {e}")
            return await app.send_message(original_chat_id, text=_["call_6"])

        button = stream_markup(_, chat_id)
        run = await app.send_photo(
            chat_id=original_chat_id,
            photo=config.STREAM_IMG_URL,
            caption=_["stream_2"].format(user),
            reply_markup=InlineKeyboardMarkup(button),
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "tg"


    async def _handle_regular_stream(self, chat_id, original_chat_id, queued, video, _, title, user, check, streamtype, videoid):
        """Handle regular audio/video streams"""
        stream = dynamic_media_stream(path=queued, video=video)
        try:
            assistant = await group_assistant(self, chat_id)
            await assistant.play(chat_id, stream)
        except Exception as e:
            LOGGER(__name__).error(f"Error playing regular stream: {e}")
            return await app.send_message(original_chat_id, text=_["call_6"])

        # Handle different stream sources
        if videoid == "telegram":
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                chat_id=original_chat_id,
                photo=(
                    config.TELEGRAM_AUDIO_URL
                    if str(streamtype) == "audio"
                    else config.TELEGRAM_VIDEO_URL
                ),
                caption=_["stream_1"].format(
                    config.SUPPORT_CHAT, title[:23], check[0]["dur"], user
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

        elif videoid == "soundcloud":
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                chat_id=original_chat_id,
                photo=config.SOUNCLOUD_IMG_URL,
                caption=_["stream_1"].format(
                    config.SUPPORT_CHAT, title[:23], check[0]["dur"], user
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

        else:
            img = await get_thumb(videoid)
            button = stream_markup(_, chat_id)
            try:
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        title[:23],
                        check[0]["dur"],
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
            except FloodWait as e:
                LOGGER(__name__).warning(f"FloodWait: Sleeping for {e.value} seconds")
                await asyncio.sleep(e.value)
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        title[:23],
                        check[0]["dur"],
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"


    async def start(self) -> None:
        """Start all PyTgCalls clients"""
        LOGGER(__name__).info("Starting PyTgCalls Clients...")
        
        for i, assistant in enumerate(self.assistants, 1):
            try:
                await assistant.start()
                LOGGER(__name__).info(f"Assistant {i} started successfully")
            except Exception as e:
                LOGGER(__name__).error(f"Failed to start assistant {i}: {e}")
        
        LOGGER(__name__).info("All PyTgCalls clients started successfully")


    @capture_internal_err
    async def ping(self) -> str:
        """Calculate average ping of all assistants"""
        pings = []
        for i, assistant in enumerate(self.assistants, 1):
            try:
                ping = await assistant.ping()
                pings.append(ping)
                LOGGER(__name__).debug(f"Assistant {i} ping: {ping}")
            except Exception as e:
                LOGGER(__name__).warning(f"Failed to get ping for assistant {i}: {e}")
        
        if pings:
            avg_ping = round(sum(pings) / len(pings), 3)
            LOGGER(__name__).info(f"Average ping: {avg_ping}")
            return str(avg_ping)
        else:
            LOGGER(__name__).warning("No assistants available for ping")
            return "0.0"


    @capture_internal_err
    async def decorators(self) -> None:
        """Setup event handlers for all assistants"""
        CRITICAL_FLAGS = (
            ChatUpdate.Status.KICKED |
            ChatUpdate.Status.LEFT_GROUP |
            ChatUpdate.Status.CLOSED_VOICE_CHAT |
            ChatUpdate.Status.DISCARDED_CALL |
            ChatUpdate.Status.BUSY_CALL
        )

        async def unified_update_handler(client, update: Update) -> None:
            """Handle updates from voice chats"""
            try:
                chat_id = getattr(update, 'chat_id', None)
                
                if isinstance(update, ChatUpdate):
                    if update.status & ChatUpdate.Status.LEFT_CALL or update.status & CRITICAL_FLAGS:
                        LOGGER(__name__).info(f"Critical update detected for chat {chat_id}, stopping stream")
                        await self.stop_stream(chat_id)
                        return

                elif isinstance(update, StreamEnded) and update.stream_type == StreamEnded.Type.AUDIO:
                    LOGGER(__name__).info(f"Stream ended in chat {chat_id}, playing next")
                    assistant = await group_assistant(self, chat_id)
                    await self.play(assistant, chat_id)

            except Exception as e:
                error_msg = f"Error in update handler: {str(e)}"
                LOGGER(__name__).error(error_msg)
                
                # Send detailed error report
                exc_type, exc_obj, exc_tb = sys.exc_info()
                full_trace = "".join(traceback.format_exception(exc_type, exc_obj, exc_tb))
                caption = (
                    f"🚨 <b>Stream Update Error</b>\n"
                    f"📍 <b>Update Type:</b> <code>{type(update).__name__}</code>\n"
                    f"📍 <b>Error Type:</b> <code>{exc_type.__name__}</code>"
                )
                filename = f"update_error_{chat_id or 'unknown'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                await send_large_error(full_trace, caption, filename)

        # Register handlers for all assistants
        for i, assistant in enumerate(self.assistants, 1):
            try:
                assistant.on_update()(unified_update_handler)
                LOGGER(__name__).info(f"Registered update handler for assistant {i}")
            except Exception as e:
                LOGGER(__name__).error(f"Failed to register handler for assistant {i}: {e}")


# Global instance
Hotty = Call()
