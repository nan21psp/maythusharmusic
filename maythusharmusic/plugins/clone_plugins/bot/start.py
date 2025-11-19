import time
from time import time
import asyncio
from pyrogram.errors import UserAlreadyParticipant
import random
from pyrogram.errors import UserNotParticipant
from pyrogram import filters, Client
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from youtubesearchpython.__future__ import VideosSearch
import config
from maythusharmusic.utils import bot_up_time
from maythusharmusic.utils.database import (
    add_served_chat_clone,
    add_served_user_clone,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    get_assistant,
)
from maythusharmusic.utils.decorators.language import LanguageStart
from strings import get_string
from maythusharmusic import app

# Spam Protection Variables
user_last_message_time = {}
user_command_count = {}
SPAM_THRESHOLD = 2
SPAM_WINDOW_SECONDS = 5

YUMI_PICS = [
    "https://files.catbox.moe/2uahrk.jpg",
    "https://files.catbox.moe/2uahrk.jpg",
    "https://files.catbox.moe/2uahrk.jpg",
]

# --- (၁) CLONE BOT အတွက် သီးသန့် BUTTON FUNCTION ---
def clone_start_pm(_, bot_username):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_3"], # "အုပ်စုသို့ထည့်ရန်"
                url=f"https://t.me/{bot_username}?startgroup=s&admin=delete_messages+manage_video_chats+pin_messages+invite_users+ban_users",
            )
        ],
        [
            InlineKeyboardButton(text=_["S_B_5"], user_id=config.OWNER_ID), # "ပိုင်ရှင်"
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_CHAT), # "အကူအညီ"
        ],
        [
            InlineKeyboardButton(text=_["S_B_6"], url=config.SUPPORT_CHANNEL), # "ချန်နယ်"
        ],
    ]
    return buttons
# -------------------------------------------------

@Client.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client: Client, message: Message, _):
    a = await client.get_me()
    user_id = message.from_user.id
    current_time = time()

    # Update the last message timestamp for the user
    last_message_time = user_last_message_time.get(user_id, 0)

    if current_time - last_message_time < SPAM_WINDOW_SECONDS:
        user_last_message_time[user_id] = current_time
        user_command_count[user_id] = user_command_count.get(user_id, 0) + 1
        if user_command_count[user_id] > SPAM_THRESHOLD:
            hu = await message.reply_text(
                f"**{message.from_user.mention} ᴘʟᴇᴀsᴇ ᴅᴏɴᴛ ᴅᴏ sᴘᴀᴍ, ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ ᴀғᴛᴇʀ 5 sᴇᴄ**"
            )
            await asyncio.sleep(3)
            await hu.delete()
            return
    else:
        user_command_count[user_id] = 1
        user_last_message_time[user_id] = current_time

    await add_served_user_clone(message.from_user.id)
    
    # --- (၂) CLONE START BUTTONS ကို ခေါ်သုံးခြင်း ---
    keyboard = clone_start_pm(_, a.username)
    # --------------------------------------------

    await message.reply_photo(
        photo=config.START_IMG_URL,
        caption=_["start_2"].format(message.from_user.mention, a.mention),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


@Client.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    a = await client.get_me()
    user_id = message.from_user.id
    current_time = time()

    last_message_time = user_last_message_time.get(user_id, 0)

    if current_time - last_message_time < SPAM_WINDOW_SECONDS:
        user_last_message_time[user_id] = current_time
        user_command_count[user_id] = user_command_count.get(user_id, 0) + 1
        if user_command_count[user_id] > SPAM_THRESHOLD:
            hu = await message.reply_text(
                f"**{message.from_user.mention} ᴘʟᴇᴀsᴇ ᴅᴏɴᴛ ᴅᴏ sᴘᴀᴍ, ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ ᴀғᴛᴇʀ 5 sᴇᴄ**"
            )
            await asyncio.sleep(3)
            await hu.delete()
            return
    else:
        user_command_count[user_id] = 1
        user_last_message_time[user_id] = current_time

    # Group တွင်လည်း Clone Buttons သုံးရန်
    out = clone_start_pm(_, a.username)
    
    BOT_UP = await bot_up_time()
    await message.reply_photo(
        photo=config.START_IMG_URL,
        caption=_["start_1"].format(a.mention, BOT_UP),
        reply_markup=InlineKeyboardMarkup(out),
    )
    await add_served_chat_clone(message.chat.id)

    # Check if Userbot is already in the group
    try:
        userbot = await get_assistant(message.chat.id)
        message = await message.reply_text(
            f"**ᴄʜᴇᴄᴋɪɴɢ [ᴀssɪsᴛᴀɴᴛ](tg://openmessage?user_id={userbot.id}) ᴀᴠᴀɪʟᴀʙɪʟɪᴛʏ ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ...**"
        )
        is_userbot = await client.get_chat_member(message.chat.id, userbot.id)
        if is_userbot:
            await message.edit_text(
                f"**[ᴀssɪsᴛᴀɴᴛ](tg://openmessage?user_id={userbot.id}) ᴀʟsᴏ ᴀᴄᴛɪᴠᴇ ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ, ʏᴏᴜ ᴄᴀɴ ᴘʟᴀʏ sᴏɴɢs.**"
            )
    except Exception as e:
        # Userbot is not in the group, invite it
        try:
            await message.edit_text(
                f"**[ᴀssɪsᴛᴀɴᴛ](tg://openmessage?user_id={userbot.id}) ɪs ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ, ɪɴᴠɪᴛɪɴɢ...**"
            )
            invitelink = await client.export_chat_invite_link(message.chat.id)
            await asyncio.sleep(1)
            await userbot.join_chat(invitelink)
            await message.edit_text(
                f"**[ᴀssɪsᴛᴀɴᴛ](tg://openmessage?user_id={userbot.id}) ɪs ɴᴏᴡ ᴀᴄᴛɪᴠᴇ ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ, ʏᴏᴜ ᴄᴀɴ ᴘʟᴀʏ sᴏɴɢs.**"
            )
        except Exception as e:
            await message.edit_text(
                f"**ᴜɴᴀʙʟᴇ ᴛᴏ ɪɴᴠɪᴛᴇ ᴍʏ [ᴀssɪsᴛᴀɴᴛ](tg://openmessage?user_id={userbot.id}). ᴘʟᴇᴀsᴇ ᴍᴀᴋᴇ ᴍᴇ ᴀᴅᴍɪɴ ᴡɪᴛʜ ɪɴᴠɪᴛᴇ ᴜsᴇʀ ᴀᴅᴍɪɴ ᴘᴏᴡᴇʀ ᴛᴏ ɪɴᴠɪᴛᴇ ᴍʏ [ᴀssɪsᴛᴀɴᴛ](tg://openmessage?user_id={userbot.id}) ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ.**"
            )


@Client.on_message(filters.new_chat_members, group=-1)
async def welcome(client, message: Message):
    a = await client.get_me()
    for member in message.new_chat_members:
        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)
            if await is_banned_user(member.id):
                try:
                    await message.chat.ban_member(member.id)
                except Exception as e:
                    print(e)
            if member.id == a.id:
                if message.chat.type != ChatType.SUPERGROUP:
                    await message.reply_text(_["start_4"])
                    await client.leave_chat(message.chat.id)
                    return
                if message.chat.id in await blacklisted_chats():
                    await message.reply_text(
                        _["start_5"].format(
                            a.mention,
                            f"https://t.me/{a.username}?start=sudolist",
                            config.SUPPORT_CHAT,
                        ),
                        disable_web_page_preview=True,
                    )
                    await client.leave_chat(message.chat.id)
                    return

                # Group Welcome Message အတွက် Button
                out = clone_start_pm(_, a.username)
                
                chid = message.chat.id

                try:
                    userbot = await get_assistant(message.chat.id)
                    chid = message.chat.id

                    if message.chat.username:
                        await userbot.join_chat(f"{message.chat.username}")
                        await message.reply_text(
                            f"**My [Assistant](tg://openmessage?user_id={userbot.id}) also entered the chat using the group's username.**"
                        )
                    else:
                        invitelink = await client.export_chat_invite_link(chid)
                        await asyncio.sleep(1)
                        messages = await message.reply_text(
                            f"**Joining my [Assistant](tg://openmessage?user_id={userbot.id}) using the invite link...**"
                        )
                        await userbot.join_chat(invitelink)
                        await messages.delete()
                        await message.reply_text(
                            f"**My [Assistant](tg://openmessage?user_id={userbot.id}) also entered the chat using the invite link.**"
                        )
                except Exception as e:
                    await message.edit_text(
                        f"**Please make me admin to invite my [Assistant](tg://openmessage?user_id={userbot.id}) in this chat.**"
                    )

                await message.reply_photo(
                    random.choice(YUMI_PICS),
                    caption=_["start_3"].format(
                        message.from_user.first_name,
                        a.mention,
                        message.chat.title,
                        a.mention,
                    ),
                    reply_markup=InlineKeyboardMarkup(out),
                )
                await add_served_chat_clone(message.chat.id)
                await message.stop_propagation()
        except Exception as ex:
            print(ex)
