import asyncio
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter
from pyrogram.errors import (
    ChatAdminRequired,
    InviteRequestSent,
    UserAlreadyParticipant,
    UserNotParticipant,
    PeerIdInvalid,
)
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from maythusharmusic import YouTube, app
from maythusharmusic.misc import SUDOERS
from maythusharmusic.utils.database import (
    get_assistant,
    get_cmode,
    get_lang,
    get_playmode,
    get_playtype,
    is_active_chat,
    is_maintenance,
    get_clones, # Clone စာရင်းရယူရန်
)
from maythusharmusic.utils.inline import botplaylist_markup
from config import PLAYLIST_IMG_URL, SUPPORT_CHAT, adminlist
from strings import get_string

links = {}
clinks = {}


def PlayWrapper(command):
    async def wrapper(client, message):
        # --- (၁) SILENT MODE CHECK (Main Bot အတွက်) ---
        # လက်ရှိ Run နေတာ Main Bot ဖြစ်ပါက
        if client.me.id == app.me.id:
            try:
                # Database မှ Clone Bot စာရင်းကို ရယူခြင်း
                clones_data = await get_clones()
                # Clone Username များကို List အဖြစ် ပြောင်းခြင်း
                clone_usernames = [c.get("bot_username", "").lower() for c in clones_data if c.get("bot_username")]
                
                # လက်ရှိ Group ထဲရှိ Bot များကို စစ်ဆေးခြင်း
                is_clone_here = False
                async for bot_member in app.get_chat_members(message.chat.id, filter=ChatMembersFilter.BOTS):
                    if bot_member.user.username and bot_member.user.username.lower() in clone_usernames:
                        is_clone_here = True
                        break
                
                # Clone Bot ရှိနေရင် Main Bot က ဘာမှမလုပ်ဘဲ ရပ်မည် (Silent)
                if is_clone_here:
                    return 
            except Exception as e:
                print(f"Silent Check Error: {e}")
        # --------------------------------------------------

        # --- (၂) MAIN BOT REQUIREMENT CHECK (ADMIN COMMANDS) ---
        # Clone Bot ဖြစ်နေပြီး Main Bot မရှိရင် တားမည်
        if client.me.id != app.me.id:
            try:
                await client.get_chat_member(message.chat.id, app.me.id)
            except UserNotParticipant:
                main_bot_username = app.me.username
                return await message.reply_text(
                    f"⚠️ <b>Main Bot Missing!</b>\n\n"
                    f"ဒီ Command ကို အသုံးပြုရန်အတွက် Main Bot (@{main_bot_username}) သည် ဤ Group ထဲတွင် ရှိနေရပါမည်။\n"
                    f"ကျေးဇူးပြု၍ Main Bot ကို ထည့်သွင်းပါ။",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("➕ Add Main Bot", url=f"https://t.me/{main_bot_username}?startgroup=true")]
                    ])
                )
            except Exception:
                pass
        # --------------------------------------------------

        language = await get_lang(message.chat.id)
        _ = get_string(language)
        
        if message.sender_chat:
            upl = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="ʜᴏᴡ ᴛᴏ ғɪx ?",
                            callback_data="AnonymousAdmin",
                        ),
                    ]
                ]
            )
            return await message.reply_text(_["general_3"], reply_markup=upl)

        if await is_maintenance() is False:
            if message.from_user.id not in SUDOERS:
                return await message.reply_text(
                    text=f"{client.me.mention} ɪs ᴜɴᴅᴇʀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ.(ပြင်ဆင်မှုများပြုလုပ်နေပါသည်) , ᴠɪsɪᴛ <a href={SUPPORT_CHAT}>sᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ</a> ғᴏʀ ᴋɴᴏᴡɪɴɢ ᴛʜᴇ ʀᴇᴀsᴏɴ.",
                    disable_web_page_preview=True,
                )

        try:
            await message.delete()
        except:
            pass

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
        url = await YouTube.url(message)
        if audio_telegram is None and video_telegram is None and url is None:
            if len(message.command) < 2:
                if "stream" in message.command:
                    return await message.reply_text(_["str_1"])
                buttons = botplaylist_markup(_)
                return await message.reply_photo(
                    photo=PLAYLIST_IMG_URL,
                    caption=_["playlist_1"],
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
        if message.command[0][0] == "c":
            chat_id = await get_cmode(message.chat.id)
            if chat_id is None:
                return await message.reply_text(_["setting_12"])
            try:
                chat = await client.get_chat(chat_id)
            except:
                return await message.reply_text(_["cplay_4"])
            channel = chat.title
        else:
            chat_id = message.chat.id
            channel = None
        playmode = await get_playmode(message.chat.id)
        playty = await get_playtype(message.chat.id)
        if playty != "Everyone":
            if message.from_user.id not in SUDOERS:
                admins = adminlist.get(message.chat.id)
                if not admins:
                    return await message.reply_text(_["admin_18"])
                else:
                    if message.from_user.id not in admins:
                        return await message.reply_text(_["play_4"])
        if message.command[0][0] == "v":
            video = True
        else:
            if "-v" in message.text:
                video = True
            else:
                video = True if message.command[0][1] == "v" else None
        if message.command[0][-1] == "e":
            if not await is_active_chat(chat_id):
                return await message.reply_text(_["play_18"])
            fplay = True
        else:
            fplay = None

        if not await is_active_chat(chat_id):
            userbot = await get_assistant(chat_id)
            try:
                try:
                    get = await client.get_chat_member(chat_id, userbot.id)
                except ChatAdminRequired:
                    return await message.reply_text(_["call_1"])
                if (
                    get.status == ChatMemberStatus.BANNED
                    or get.status == ChatMemberStatus.RESTRICTED
                ):
                    return await message.reply_text(
                        _["call_2"].format(
                            client.me.mention, userbot.id, userbot.name, userbot.username
                        )
                    )
            except (UserNotParticipant, PeerIdInvalid):
                if chat_id in links:
                    invitelink = links[chat_id]
                else:
                    if message.chat.username:
                        invitelink = message.chat.username
                        try:
                            await userbot.resolve_peer(invitelink)
                        except:
                            pass
                    else:
                        try:
                            invitelink = await client.export_chat_invite_link(chat_id)
                        except ChatAdminRequired:
                            return await message.reply_text(_["call_1"])
                        except Exception as e:
                            return await message.reply_text(
                                _["call_3"].format(client.me.mention, type(e).__name__)
                            )

                if invitelink.startswith("https://t.me/+"):
                    invitelink = invitelink.replace(
                        "https://t.me/+", "https://t.me/joinchat/"
                    )
                #myu = await message.reply_text(_["call_4"].format(client.me.mention))
                try:
                    await asyncio.sleep(1)
                    await userbot.join_chat(invitelink)
                except InviteRequestSent:
                    try:
                        await client.approve_chat_join_request(chat_id, userbot.id)
                    except Exception as e:
                        return await message.reply_text(
                            _["call_3"].format(client.me.mention, type(e).__name__)
                        )
                    await asyncio.sleep(1)
                    await myu.edit(_["call_5"].format(client.me.mention))
                except UserAlreadyParticipant:
                    pass
                except Exception as e:
                    return await message.reply_text(
                        _["call_3"].format(client.me.mention, type(e).__name__)
                    )

                links[chat_id] = invitelink

                try:
                    await userbot.resolve_peer(chat_id)
                except:
                    pass

        return await command(
            client,
            message,
            _,
            chat_id,
            video,
            channel,
            playmode,
            url,
            fplay,
        )

    return wrapper


def CPlayWrapper(command):
    async def wrapper(client, message):
        # --- MAIN BOT REQUIREMENT CHECK (CPlay အတွက်လည်း) ---
        # Clone Bot ဖြစ်နေပြီး Main Bot မရှိရင် တားမည်
        if client.me.id != app.me.id:
            try:
                await client.get_chat_member(message.chat.id, app.me.id)
            except UserNotParticipant:
                main_bot_username = app.me.username
                return await message.reply_text(
                    f"⚠️ <b>Main Bot Missing!</b>\n\n"
                    f"ဒီ Command ကို အသုံးပြုရန်အတွက် Main Bot (@{main_bot_username}) သည် ဤ Group ထဲတွင် ရှိနေရပါမည်။\n"
                    f"ကျေးဇူးပြု၍ Main Bot ကို ထည့်သွင်းပါ။",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("➕ Add Main Bot", url=f"https://t.me/{main_bot_username}?startgroup=true")]
                    ])
                )
            except Exception:
                pass
        # --------------------------------------------------

        language = await get_lang(message.chat.id)
        _ = get_string(language)
        if message.sender_chat:
            upl = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="ʜᴏᴡ ᴛᴏ ғɪx ?",
                            callback_data="AnonymousAdmin",
                        ),
                    ]
                ]
            )
            return await message.reply_text(_["general_3"], reply_markup=upl)

        if await is_maintenance() is False:
            if message.from_user.id not in SUDOERS:
                return await message.reply_text(
                    text=f"{client.me.mention} ɪs ᴜɴᴅᴇʀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ.(ပြင်ဆင်မှုများပြုလုပ်နေပါသည်) , ᴠɪsɪᴛ <a href={SUPPORT_CHAT}>sᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ</a> ғᴏʀ ᴋɴᴏᴡɪɴɢ ᴛʜᴇ ʀᴇᴀsᴏɴ.",
                    disable_web_page_preview=True,
                )
        
        return await command(
            client,
            message,
            _,
            message.chat.id,
            None,
            None,
            None,
            None,
            None,
        )

    return wrapper
