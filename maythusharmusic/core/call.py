import asyncio
import os
import traceback
from datetime import datetime, timedelta
from typing import Union

from ntgcalls import TelegramServerError
from pyrogram import Client, filters
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

autoend = {}
counter = {}

def dynamic_media_stream(path: str, video: bool = False, ffmpeg_params: str = None) -> MediaStream:
    """အရည်အသွေးမြင့် အသံနှင့် ဗီဒီယို stream အတွက် optimized media stream configuration"""
    return MediaStream(
        audio_path=path,
        media_path=path,
        audio_parameters=AudioQuality.HIGH if video else AudioQuality.STUDIO,
        video_parameters=VideoQuality.FULL_HD if video else VideoQuality.HD_720p,
        video_flags=(MediaStream.Flags.REQUIRE_ENCODE if video else MediaStream.Flags.IGNORE),
        ffmpeg_parameters=ffmpeg_params or "-ac 2 -ar 48000 -b:a 192k" if not video else "-c:v libx264 -preset fast -crf 23 -maxrate 2M -bufsize 4M -ac 2 -ar 48000 -b:a 192k",
    )

async def _clear_(chat_id: int) -> None:
    """Chat data များကို ရှင်းလင်းခြင်း"""
    popped = db.pop(chat_id, None)
    if popped:
        await auto_clean(popped)
    db[chat_id] = []
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)
    await set_loop(chat_id, 0)

async def group_assistant(self, chat_id: int):
    """Group အတွက် assistant ရွေးချယ်ခြင်း"""
    try:
        assistants = []
        
        # Check which assistants are available and in call
        if self.one:
            try:
                await self.one.get_participants(chat_id)
                assistants.append(self.one)
            except:
                pass
        
        if self.two:
            try:
                await self.two.get_participants(chat_id)
                assistants.append(self.two)
            except:
                pass
                
        if self.three:
            try:
                await self.three.get_participants(chat_id)
                assistants.append(self.three)
            except:
                pass
                
        if self.four:
            try:
                await self.four.get_participants(chat_id)
                assistants.append(self.four)
            except:
                pass
                
        if self.five:
            try:
                await self.five.get_participants(chat_id)
                assistants.append(self.five)
            except:
                pass
        
        if assistants:
            return assistants[0]  # First available assistant
        else:
            # No assistant in call, use first available one
            if self.one:
                return self.one
            elif self.two:
                return self.two
            elif self.three:
                return self.three
            elif self.four:
                return self.four
            elif self.five:
                return self.five
            else:
                raise AssistantErr("❌ **No assistant available**\nကျေးဇူးပြု၍ session strings များကို စစ်ဆေးပါ။")
    except Exception as e:
        LOGGER(__name__).error(f"Assistant selection error: {str(e)}")
        raise AssistantErr(f"❌ **Assistant selection failed**\nError: {str(e)}")

class Call:
    def __init__(self):
        """High-quality voice call management system initialization"""
        # Session 1 - Primary High Quality
        self.userbot1 = Client(
            "maythusharmusic1", 
            config.API_ID, 
            config.API_HASH, 
            session_string=config.STRING1
        ) if config.STRING1 else None
        self.one = PyTgCalls(self.userbot1) if self.userbot1 else None

        # Session 2 - Backup High Quality
        self.userbot2 = Client(
            "maythusharmusic2", 
            config.API_ID, 
            config.API_HASH, 
            session_string=config.STRING2
        ) if config.STRING2 else None
        self.two = PyTgCalls(self.userbot2) if self.userbot2 else None

        # Session 3 - Additional Capacity
        self.userbot3 = Client(
            "maythusharmusic3", 
            config.API_ID, 
            config.API_HASH, 
            session_string=config.STRING3
        ) if config.STRING3 else None
        self.three = PyTgCalls(self.userbot3) if self.userbot3 else None

        # Session 4 - Load Balancing
        self.userbot4 = Client(
            "maythusharmusic4", 
            config.API_ID, 
            config.API_HASH, 
            session_string=config.STRING4
        ) if config.STRING4 else None
        self.four = PyTgCalls(self.userbot4) if self.userbot4 else None

        # Session 5 - Redundancy
        self.userbot5 = Client(
            "maythusharmusic5", 
            config.API_ID, 
            config.API_HASH, 
            session_string=config.STRING5
        ) if config.STRING5 else None
        self.five = PyTgCalls(self.userbot5) if self.userbot5 else None

        self.active_calls: set[int] = set()

    @capture_internal_err
    async def pause_stream(self, chat_id: int) -> None:
        """Stream ကို ခေတ္တရပ်ဆိုင်းခြင်း"""
        assistant = await group_assistant(self, chat_id)
        await assistant.pause(chat_id)

    @capture_internal_err
    async def resume_stream(self, chat_id: int) -> None:
        """Stream ကို ပြန်လည်စတင်ခြင်း"""
        assistant = await group_assistant(self, chat_id)
        await assistant.resume(chat_id)

    @capture_internal_err
    async def mute_stream(self, chat_id: int) -> None:
        """Stream အသံကို ပိတ်ခြင်း"""
        assistant = await group_assistant(self, chat_id)
        await assistant.mute(chat_id)

    @capture_internal_err
    async def unmute_stream(self, chat_id: int) -> None:
        """Stream အသံကို ပြန်ဖွင့်ခြင်း"""
        assistant = await group_assistant(self, chat_id)
        await assistant.unmute(chat_id)

    @capture_internal_err
    async def stop_stream(self, chat_id: int) -> None:
        """Stream ကို ရပ်ဆိုင်းခြင်း"""
        assistant = await group_assistant(self, chat_id)
        await _clear_(chat_id)
        if chat_id not in self.active_calls:
            return
        try:
            await assistant.leave_call(chat_id)
        except NoActiveGroupCall:
            pass
        except Exception:
            pass
        finally:
            self.active_calls.discard(chat_id)

    @capture_internal_err
    async def force_stop_stream(self, chat_id: int) -> None:
        """Stream ကို အတင်းအဓမ္မ ရပ်ဆိုင်းခြင်း"""
        assistant = await group_assistant(self, chat_id)
        try:
            check = db.get(chat_id)
            if check:
                check.pop(0)
        except (IndexError, KeyError):
            pass
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        await _clear_(chat_id)
        if chat_id not in self.active_calls:
            return
        try:
            await assistant.leave_call(chat_id)
        except NoActiveGroupCall:
            pass
        except Exception:
            pass
        finally:
            self.active_calls.discard(chat_id)

    @capture_internal_err
    async def skip_stream(self, chat_id: int, link: str, video: Union[bool, str] = None, image: Union[bool, str] = None) -> None:
        """နောက် track သို့ ခုန်ကူးခြင်း"""
        assistant = await group_assistant(self, chat_id)
        stream = dynamic_media_stream(path=link, video=bool(video))
        await assistant.play(chat_id, stream)

    @capture_internal_err
    async def vc_users(self, chat_id: int) -> list:
        """Voice chat ထဲရှိ user များစာရင်း"""
        assistant = await group_assistant(self, chat_id)
        participants = await assistant.get_participants(chat_id)
        return [p.user_id for p in participants if not p.is_muted]

    @capture_internal_err
    async def change_volume(self, chat_id: int, volume: int) -> None:
        """အသံပမာဏ ပြောင်းလည်းခြင်း"""
        assistant = await group_assistant(self, chat_id)
        await assistant.change_volume_call(chat_id, volume)

    @capture_internal_err
    async def seek_stream(self, chat_id: int, file_path: str, to_seek: str, duration: str, mode: str) -> None:
        """Stream ကို သတ်မှတ်နေရာသို့ ခုန်ကူးခြင်း"""
        assistant = await group_assistant(self, chat_id)
        ffmpeg_params = f"-ss {to_seek} -to {duration}"
        is_video = mode == "video"
        stream = dynamic_media_stream(path=file_path, video=is_video, ffmpeg_params=ffmpeg_params)
        await assistant.play(chat_id, stream)

    @capture_internal_err
    async def speedup_stream(self, chat_id: int, file_path: str, speed: float, playing: list) -> None:
        """Stream အရှိန်ပြောင်းလည်းခြင်း"""
        if not isinstance(playing, list) or not playing or not isinstance(playing[0], dict):
            raise AssistantErr("Invalid stream info for speedup.")

        assistant = await group_assistant(self, chat_id)
        base = os.path.basename(file_path)
        chatdir = os.path.join("playback", str(speed))
        os.makedirs(chatdir, exist_ok=True)
        out = os.path.join(chatdir, base)

        if not os.path.exists(out):
            vs = str(2.0 / float(speed))
            cmd = f"ffmpeg -i {file_path} -filter:v setpts={vs}*PTS -filter:a atempo={speed} -c:a aac -b:a 192k -ar 48000 {out}"
            proc = await asyncio.create_subprocess_shell(cmd, stdin=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            await proc.communicate()

        dur = int(await asyncio.get_event_loop().run_in_executor(None, check_duration, out))
        played, con_seconds = speed_converter(playing[0]["played"], speed)
        duration_min = seconds_to_min(dur)
        is_video = playing[0]["streamtype"] == "video"
        ffmpeg_params = f"-ss {played} -to {duration_min}"
        stream = dynamic_media_stream(path=out, video=is_video, ffmpeg_params=ffmpeg_params)

        if chat_id in db and db[chat_id] and db[chat_id][0].get("file") == file_path:
            await assistant.play(chat_id, stream)
        else:
            raise AssistantErr("Stream mismatch during speedup.")

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
        """Test stream call with high quality audio"""
        assistant = await group_assistant(self, config.LOGGER_ID)
        try:
            await assistant.play(config.LOGGER_ID, MediaStream(link))
            await asyncio.sleep(8)
        finally:
            try:
                await assistant.leave_call(config.LOGGER_ID)
            except:
                pass

    @capture_internal_err
    async def force_join_call(self, chat_id: int) -> bool:
        """Voice chat ထဲသို့ အတင်းဝင်ခြင်း"""
        try:
            assistant = await group_assistant(self, chat_id)
            
            # Leave if already in call
            try:
                await assistant.leave_call(chat_id)
                await asyncio.sleep(2)
            except:
                pass
            
            # Join call without stream first
            try:
                await assistant.join_call(chat_id)
                await asyncio.sleep(3)
                LOGGER(__name__).info(f"Successfully joined call {chat_id} without stream")
                self.active_calls.add(chat_id)
                await add_active_chat(chat_id)
                return True
            except Exception as e:
                LOGGER(__name__).error(f"Force join error: {str(e)}")
                return False
                
        except Exception as e:
            LOGGER(__name__).error(f"Force join call error: {str(e)}")
            return False

    @capture_internal_err
    async def join_call(
        self,
        chat_id: int,
        original_chat_id: int,
        link: str,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ) -> None:
        """Voice chat ထဲသို့ join ဝင်ခြင်း"""
        assistant = await group_assistant(self, chat_id)
        lang = await get_lang(chat_id)
        _ = get_string(lang)
        
        LOGGER(__name__).info(f"Joining call in chat {chat_id} with assistant {assistant}")

        try:
            # First, ensure we're in the group call
            try:
                participants = await assistant.get_participants(chat_id)
                LOGGER(__name__).info(f"Found {len(participants)} participants in call")
            except NoActiveGroupCall:
                LOGGER(__name__).warning("No active group call")
                error_msg = "❌ **မ� aktif voice chat ရှိပါဘူး**\n\nကျေးဇူးပြု၍ group ထဲမှာ voice chat စတင်ပါ။"
                raise AssistantErr(error_msg)

            # Now join the call with stream
            stream = dynamic_media_stream(path=link, video=bool(video))
            LOGGER(__name__).info("Starting to play stream...")
            
            await assistant.play(chat_id, stream)
            LOGGER(__name__).info("Successfully joined and started playing")

        except NoActiveGroupCall:
            error_msg = "❌ **မ� aktif voice chat ရှိပါဘူး**\n\nကျေးဇူးပြု၍ group ထဲမှာ voice chat စတင်ပါ။"
            raise AssistantErr(error_msg)
        except ChatAdminRequired:
            error_msg = "❌ **Admin permission လိုအပ်ပါသည်**\n\nBot က admin ဖြစ်ပြီး 'Manage Voice Chats' permission ရှိရပါမယ်။"
            raise AssistantErr(error_msg)
        except TelegramServerError:
            raise AssistantErr(_["call_10"])
        except Exception as e:
            LOGGER(__name__).error(f"Join call error: {str(e)}")
            error_msg = f"❌ **Voice chat ထဲသို့ ဝင်ရောက်၍မရပါ**\n\nError: {str(e)}"
            raise AssistantErr(error_msg)

        # Success - update states
        self.active_calls.add(chat_id)
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video:
            await add_active_video_chat(chat_id)

        LOGGER(__name__).info(f"Successfully joined voice chat {chat_id}")

        # Autoend setup
        if await is_autoend():
            counter[chat_id] = {}
            users = len(await assistant.get_participants(chat_id))
            if users == 1:
                autoend[chat_id] = datetime.now() + timedelta(minutes=1)

    @capture_internal_err
    async def debug_video_call(self, chat_id: int) -> str:
        """Voice call issue များကို debug လုပ်ခြင်း"""
        try:
            assistant = await group_assistant(self, chat_id)
            
            # 1. Check if assistant is connected
            if not assistant.is_connected:
                return "❌ Assistant not connected"
            
            # 2. Check group call status
            try:
                participants = await assistant.get_participants(chat_id)
                participant_count = len(participants)
            except NoActiveGroupCall:
                return "❌ No active group call"
            except Exception as e:
                return f"❌ Group call error: {str(e)}"
            
            # 3. Check if bot has admin permissions
            try:
                chat_member = await app.get_chat_member(chat_id, (await assistant.get_me()).id)
                if not chat_member.privileges:
                    return "❌ Bot needs admin permissions"
            except:
                return "❌ Cannot check admin permissions"
            
            return f"✅ All checks passed\n👥 Participants: {participant_count}"
        
        except Exception as e:
            return f"❌ Debug error: {str(e)}"

    @capture_internal_err
    async def check_sessions(self):
        """Session strings များ စစ်ဆေးခြင်း"""
        sessions = []
        try:
            if self.one and await self.one.get_me():
                sessions.append("Session 1: ✅ Working")
            else:
                sessions.append("Session 1: ❌ Failed")
        except:
            sessions.append("Session 1: ❌ Failed")
        
        try:
            if self.two and await self.two.get_me():
                sessions.append("Session 2: ✅ Working") 
            else:
                sessions.append("Session 2: ❌ Failed")
        except:
            sessions.append("Session 2: ❌ Failed")
            
        try:
            if self.three and await self.three.get_me():
                sessions.append("Session 3: ✅ Working")
            else:
                sessions.append("Session 3: ❌ Failed")
        except:
            sessions.append("Session 3: ❌ Failed")
            
        try:
            if self.four and await self.four.get_me():
                sessions.append("Session 4: ✅ Working")
            else:
                sessions.append("Session 4: ❌ Failed")
        except:
            sessions.append("Session 4: ❌ Failed")
            
        try:
            if self.five and await self.five.get_me():
                sessions.append("Session 5: ✅ Working")
            else:
                sessions.append("Session 5: ❌ Failed")
        except:
            sessions.append("Session 5: ❌ Failed")
        
        return "\n".join(sessions)

    @capture_internal_err
    async def play(self, client, chat_id: int) -> None:
        """High-quality audio playback system"""
        check = db.get(chat_id)
        popped = None
        loop = await get_loop(chat_id)
        
        if not check:
            await _clear_(chat_id)
            return

        try:
            if loop == 0:
                popped = check.pop(0)
            else:
                loop = loop - 1
                await set_loop(chat_id, loop)
            await auto_clean(popped)
            if not check:
                    await _clear_(chat_id)
                    if chat_id in self.active_calls:
                        try:
                            await client.leave_call(chat_id)
                        except NoActiveGroupCall:
                            pass
                        except Exception:
                            pass
                        finally:
                            self.active_calls.discard(chat_id)
                    return
        except:
            try:
                await _clear_(chat_id)
                return await client.leave_call(chat_id)
            except:
                return
        else:
            queued = check[0]["file"]
            language = await get_lang(chat_id)
            _ = get_string(language)
            title = (check[0]["title"]).title()
            user = check[0]["by"]
            original_chat_id = check[0]["chat_id"]
            streamtype = check[0]["streamtype"]
            videoid = check[0]["vidid"]
            db[chat_id][0]["played"] = 0

            exis = (check[0]).get("old_dur")
            if exis:
                db[chat_id][0]["dur"] = exis
                db[chat_id][0]["seconds"] = check[0]["old_second"]
                db[chat_id][0]["speed_path"] = None
                db[chat_id][0]["speed"] = 1.0

            video = True if str(streamtype) == "video" else False

            # Ensure we're in voice chat before playing
            if chat_id not in self.active_calls:
                try:
                    LOGGER(__name__).info(f"Not in call, joining chat {chat_id} first...")
                    success = await self.force_join_call(chat_id)
                    if not success:
                        LOGGER(__name__).error("Failed to join call, trying direct join...")
                        # Try direct join with stream
                        await self.join_call(chat_id, original_chat_id, queued, video=video)
                    await asyncio.sleep(2)
                except Exception as e:
                    LOGGER(__name__).error(f"Failed to join call: {e}")
                    return await app.send_message(original_chat_id, f"❌ Voice chat ထဲသို့ ဝင်ရောက်၍မရပါ\nError: {str(e)}")

            if "live_" in queued:
                n, link = await YouTube.video(videoid, True)
                if n == 0:
                    return await app.send_message(original_chat_id, text=_["call_6"])

                stream = dynamic_media_stream(path=link, video=video)
                try:
                    await client.play(chat_id, stream)
                except Exception as e:
                    LOGGER(__name__).error(f"Live stream play error: {e}")
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

            elif "vid_" in queued:
                mystic = await app.send_message(original_chat_id, _["call_7"])
                try:
                    file_path, direct = await YouTube.download(
                        videoid,
                        mystic,
                        videoid=True,
                        video=True if str(streamtype) == "video" else False,
                    )
                except:
                    return await mystic.edit_text(
                        _["call_6"], disable_web_page_preview=True
                    )

                stream = dynamic_media_stream(path=file_path, video=video)
                try:
                    await client.play(chat_id, stream)
                except Exception as e:
                    LOGGER(__name__).error(f"Video stream play error: {e}")
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

            elif "index_" in queued:
                stream = dynamic_media_stream(path=videoid, video=video)
                try:
                    await client.play(chat_id, stream)
                except Exception as e:
                    LOGGER(__name__).error(f"Index stream play error: {e}")
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

            else:
                stream = dynamic_media_stream(path=queued, video=video)
                try:
                    await client.play(chat_id, stream)
                except Exception as e:
                    LOGGER(__name__).error(f"Audio stream play error: {e}")
                    return await app.send_message(original_chat_id, text=_["call_6"])

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
                        LOGGER(__name__).warning(f"FloodWait: Sleeping for {e.value}")
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
        """PyTgCalls Clients များကို စတင်ခြင်း"""
        LOGGER(__name__).info("Starting High Quality PyTgCalls Clients...")
        if config.STRING1:
            await self.one.start()
        if config.STRING2:
            await self.two.start()
        if config.STRING3:
            await self.three.start()
        if config.STRING4:
            await self.four.start()
        if config.STRING5:
            await self.five.start()

    @capture_internal_err
    async def ping(self) -> str:
        """Connection ping စစ်ဆေးခြင်း"""
        pings = []
        if config.STRING1:
            pings.append(await self.one.ping)
        if config.STRING2:
            pings.append(await self.two.ping)
        if config.STRING3:
            pings.append(await self.three.ping)
        if config.STRING4:
            pings.append(await self.four.ping)
        if config.STRING5:
            pings.append(await self.five.ping)
        return str(round(sum(pings) / len(pings), 3)) if pings else "0.0"

    @capture_internal_err
    async def decorators(self) -> None:
        """Event handlers များ သတ်မှတ်ခြင်း"""
        assistants = list(filter(None, [self.one, self.two, self.three, self.four, self.five]))

        CRITICAL_FLAGS = (
            ChatUpdate.Status.KICKED |
            ChatUpdate.Status.LEFT_GROUP |
            ChatUpdate.Status.CLOSED_VOICE_CHAT |
            ChatUpdate.Status.DISCARDED_CALL |
            ChatUpdate.Status.BUSY_CALL
        )

        async def unified_update_handler(client, update: Update) -> None:
            try:
                if isinstance(update, ChatUpdate):
                    if update.status & ChatUpdate.Status.LEFT_CALL or update.status & CRITICAL_FLAGS:
                        await self.stop_stream(update.chat_id)
                        return

                elif isinstance(update, StreamEnded) and update.stream_type == StreamEnded.Type.AUDIO:
                    assistant = await group_assistant(self, update.chat_id)
                    await self.play(assistant, update.chat_id)

            except Exception as e:
                import sys
                exc_type, exc_obj, exc_tb = sys.exc_info()
                full_trace = "".join(traceback.format_exception(exc_type, exc_obj, exc_tb))
                caption = (
                    f"🚨 <b>Stream Update Error</b>\n"
                    f"📍 <b>Update Type:</b> <code>{type(update).__name__}</code>\n"
                    f"📍 <b>Error Type:</b> <code>{exc_type.__name__}</code>"
                )
                filename = f"update_error_{getattr(update, 'chat_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                await send_large_error(full_trace, caption, filename)

        for assistant in assistants:
            assistant.on_update()(unified_update_handler)

# Debug commands for testing
@app.on_message(filters.command("joincheck"))
async def join_check(_, message):
    chat_id = message.chat.id
    try:
        debug_info = await Hotty.debug_video_call(chat_id)
        await message.reply(f"🔍 **Voice Chat Status**\n\n{debug_info}")
    except Exception as e:
        await message.reply(f"❌ Check failed: {str(e)}")

@app.on_message(filters.command("forcejoin"))
async def force_join(_, message):
    chat_id = message.chat.id
    try:
        success = await Hotty.force_join_call(chat_id)
        if success:
            await message.reply("✅ **Voice chat ထဲသို့ အောင်မြင်စွာဝင်ရောက်ပြီး**")
        else:
            await message.reply("❌ **Voice chat ထဲသို့ ဝင်ရောက်၍မရပါ**")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

@app.on_message(filters.command("sessions"))
async def check_sessions_cmd(_, message):
    try:
        session_status = await Hotty.check_sessions()
        await message.reply(f"🔧 **Session Status**\n\n{session_status}")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

Hotty = Call()
