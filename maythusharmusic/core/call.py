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
from pytgcalls.exceptions import NoActiveGroupCall, NotConnectedError
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
        
        # Check which assistants are available
        if self.one and await self.is_assistant_connected(self.one):
            assistants.append(self.one)
        
        if self.two and await self.is_assistant_connected(self.two):
            assistants.append(self.two)
                
        if self.three and await self.is_assistant_connected(self.three):
            assistants.append(self.three)
                
        if self.four and await self.is_assistant_connected(self.four):
            assistants.append(self.four)
                
        if self.five and await self.is_assistant_connected(self.five):
            assistants.append(self.five)
        
        if assistants:
            LOGGER(__name__).info(f"Using assistant from {len(assistants)} available assistants")
            return assistants[0]  # First available assistant
        else:
            # No assistant available, use first configured one
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

    async def is_assistant_connected(self, assistant) -> bool:
        """Assistant connected ဖြစ်မဖြစ် စစ်ဆေးခြင်း"""
        try:
            # Try to get ping to check if connected
            await assistant.ping
            return True
        except:
            return False

    @capture_internal_err
    async def debug_video_call(self, chat_id: int) -> str:
        """Voice call issue များကို debug လုပ်ခြင်း"""
        try:
            # 1. Check if any assistant is available
            available_assistants = []
            if self.one and await self.is_assistant_connected(self.one):
                available_assistants.append("Session 1")
            if self.two and await self.is_assistant_connected(self.two):
                available_assistants.append("Session 2")
            if self.three and await self.is_assistant_connected(self.three):
                available_assistants.append("Session 3")
            if self.four and await self.is_assistant_connected(self.four):
                available_assistants.append("Session 4")
            if self.five and await self.is_assistant_connected(self.five):
                available_assistants.append("Session 5")
            
            if not available_assistants:
                return "❌ **No assistants connected**\nSession strings များကို စစ်ဆေးပါ။"
            
            assistant = await group_assistant(self, chat_id)
            
            # 2. Check group call status
            try:
                participants = await assistant.get_participants(chat_id)
                participant_count = len(participants)
                call_status = f"✅ **Active group call**\n👥 Participants: {participant_count}"
            except NoActiveGroupCall:
                call_status = "❌ **No active group call**\nVoice chat ကို စတင်ပါ။"
            except Exception as e:
                call_status = f"❌ **Group call error**: {str(e)}"
            
            # 3. Check if bot has admin permissions
            try:
                chat_member = await app.get_chat_member(chat_id, app.me.id)
                if chat_member.privileges and chat_member.privileges.can_manage_video_chats:
                    admin_status = "✅ **Admin permissions**"
                else:
                    admin_status = "❌ **No admin permissions**\nManage Voice Chats permission လိုအပ်ပါသည်။"
            except Exception as e:
                admin_status = f"❌ **Admin check error**: {str(e)}"
            
            return f"""
🔍 **Voice Chat Debug Info**

🤖 **Available Assistants**: {', '.join(available_assistants) if available_assistants else 'None'}

📞 **Call Status**:
{call_status}

⚡ **Admin Status**:
{admin_status}

🆔 **Chat ID**: {chat_id}
            """
        
        except Exception as e:
            return f"❌ **Debug error**: {str(e)}"

    @capture_internal_err
    async def check_sessions(self):
        """Session strings များ စစ်ဆေးခြင်း"""
        sessions = []
        try:
            if self.one and await self.is_assistant_connected(self.one):
                sessions.append("Session 1: ✅ Connected")
            else:
                sessions.append("Session 1: ❌ Disconnected")
        except:
            sessions.append("Session 1: ❌ Failed")
        
        try:
            if self.two and await self.is_assistant_connected(self.two):
                sessions.append("Session 2: ✅ Connected") 
            else:
                sessions.append("Session 2: ❌ Disconnected")
        except:
            sessions.append("Session 2: ❌ Failed")
            
        try:
            if self.three and await self.is_assistant_connected(self.three):
                sessions.append("Session 3: ✅ Connected")
            else:
                sessions.append("Session 3: ❌ Disconnected")
        except:
            sessions.append("Session 3: ❌ Failed")
            
        try:
            if self.four and await self.is_assistant_connected(self.four):
                sessions.append("Session 4: ✅ Connected")
            else:
                sessions.append("Session 4: ❌ Disconnected")
        except:
            sessions.append("Session 4: ❌ Failed")
            
        try:
            if self.five and await self.is_assistant_connected(self.five):
                sessions.append("Session 5: ✅ Connected")
            else:
                sessions.append("Session 5: ❌ Disconnected")
        except:
            sessions.append("Session 5: ❌ Failed")
        
        return "\n".join(sessions)

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
        
        LOGGER(__name__).info(f"Joining call in chat {chat_id}")

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

    # Other methods remain the same (pause_stream, resume_stream, stop_stream, etc.)
    @capture_internal_err
    async def pause_stream(self, chat_id: int) -> None:
        assistant = await group_assistant(self, chat_id)
        await assistant.pause(chat_id)

    @capture_internal_err
    async def resume_stream(self, chat_id: int) -> None:
        assistant = await group_assistant(self, chat_id)
        await assistant.resume(chat_id)

    @capture_internal_err
    async def mute_stream(self, chat_id: int) -> None:
        assistant = await group_assistant(self, chat_id)
        await assistant.mute(chat_id)

    @capture_internal_err
    async def unmute_stream(self, chat_id: int) -> None:
        assistant = await group_assistant(self, chat_id)
        await assistant.unmute(chat_id)

    @capture_internal_err
    async def stop_stream(self, chat_id: int) -> None:
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
    async def skip_stream(self, chat_id: int, link: str, video: Union[bool, str] = None, image: Union[bool, str] = None) -> None:
        assistant = await group_assistant(self, chat_id)
        stream = dynamic_media_stream(path=link, video=bool(video))
        await assistant.play(chat_id, stream)

    async def start(self) -> None:
        LOGGER(__name__).info("Starting PyTgCalls Clients...")
        if config.STRING1 and self.one:
            await self.one.start()
        if config.STRING2 and self.two:
            await self.two.start()
        if config.STRING3 and self.three:
            await self.three.start()
        if config.STRING4 and self.four:
            await self.four.start()
        if config.STRING5 and self.five:
            await self.five.start()

    @capture_internal_err
    async def ping(self) -> str:
        pings = []
        if self.one:
            try:
                pings.append(await self.one.ping)
            except:
                pass
        if self.two:
            try:
                pings.append(await self.two.ping)
            except:
                pass
        if self.three:
            try:
                pings.append(await self.three.ping)
            except:
                pass
        if self.four:
            try:
                pings.append(await self.four.ping)
            except:
                pass
        if self.five:
            try:
                pings.append(await self.five.ping)
            except:
                pass
        return str(round(sum(pings) / len(pings), 3)) if pings else "0.0"

    @capture_internal_err
    async def decorators(self) -> None:
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
            if assistant:
                assistant.on_update()(unified_update_handler)

# Create instance
Hotty = Call()

# Debug commands
@app.on_message(filters.command("joincheck"))
async def join_check(_, message):
    chat_id = message.chat.id
    try:
        debug_info = await Hotty.debug_video_call(chat_id)
        await message.reply(f"🔍 **Voice Chat Status**\n\n{debug_info}")
    except Exception as e:
        await message.reply(f"❌ Check failed: {str(e)}")

@app.on_message(filters.command("sessions"))
async def check_sessions_cmd(_, message):
    try:
        session_status = await Hotty.check_sessions()
        await message.reply(f"🔧 **Session Status**\n\n{session_status}")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")
