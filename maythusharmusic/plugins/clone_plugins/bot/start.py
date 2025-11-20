import time
import asyncio
import random
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardMarkup, Message
import config
from maythusharmusic import app
from maythusharmusic.utils.database import (
    add_served_chat_clone,
    add_served_user_clone,
    blacklisted_chats,
    is_banned_user,
    get_assistant,
    get_lang,
)
from strings import get_string

# --- (၁) clone_private_panel ကို Import လုပ်ခြင်း ---
from maythusharmusic.utils.inline import clone_private_panel
# ------------------------------------------------

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

@Client.on_message(filters.command(["start"]) & filters.private & ~filters.banned)
async def start_pm(client: Client, message: Message):
    try:
        await add_served_user_clone(message.from_user.id)
        
        # 1. Language String ရယူခြင်း
        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)
        except:
            _ = get_string("en")

        # 2. Spam Protection
        user_id = message.from_user.id
        current_time = time.time()
        last_message_time = user_last_message_time.get(user_id, 0)

        if current_time - last_message_time < SPAM_WINDOW_SECONDS:
            user_last_message_time[user_id] = current_time
            user_command_count[user_id] = user_command_count.get(user_id, 0) + 1
            if user_command_count[user_id] > SPAM_THRESHOLD:
                hu = await message.reply_text(f"**{message.from_user.mention} Please don't spam! Wait 5s.**")
                await asyncio.sleep(3)
                await hu.delete()
                return
        else:
            user_command_count[user_id] = 1
            user_last_message_time[user_id] = current_time

        # 3. Bot Info & Buttons
        a = await client.get_me()
        
        # --- (၃) clone_private_panel ခေါ်သုံးခြင်း ---
        # (utils/inline/start.py တွင် clone_private_panel ရှိရမည်)
        buttons = clone_private_panel(_, a.username)
        # ----------------------------------------

        await message.reply_photo(
            photo=config.START_IMG_URL,
            caption=_["start_2"].format(message.from_user.mention, a.mention),
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    except Exception as e:
        print(f"Start PM Error: {e}")


@Client.on_message(filters.command(["start"]) & filters.group & ~filters.banned)
async def start_gp(client: Client, message: Message):
    try:
        a = await client.get_me()
        await add_served_chat_clone(message.chat.id)

        # Language
        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)
        except:
            _ = get_string("en")

        # Buttons (Group အတွက်လည်း Panel သုံးလို့ရပါတယ်)
        buttons = clone_private_panel(_, a.username)

        await message.reply_photo(
            photo=config.START_IMG_URL,
            caption=_["start_1"].format(a.mention, "Alive"),
            reply_markup=InlineKeyboardMarkup(buttons),
        )

        # Assistant Checking Logic
        try:
            userbot = await get_assistant(message.chat.id)
            try:
                await client.get_chat_member(message.chat.id, userbot.id)
            except:
                try:
                    invitelink = await client.export_chat_invite_link(message.chat.id)
                    if "+" in invitelink:
                        link_hash = invitelink.split("+")[1]
                        await userbot.join_chat(f"https://t.me/joinchat/{link_hash}")
                    else:
                        await userbot.join_chat(invitelink)
                    await message.reply_text(f"✅ Assistant (@{userbot.username}) joined successfully.")
                except Exception:
                    pass # Admin မဟုတ်လို့ Invite မရရင် ကျော်သွားမယ်
        except Exception:
            pass

    except Exception as e:
        print(f"Start Group Error: {e}")


@Client.on_message(filters.new_chat_members, group=-1)
async def welcome(client, message: Message):
    a = await client.get_me()
    for member in message.new_chat_members:
        try:
            if member.id == a.id:
                # Language
                try:
                    language = await get_lang(message.chat.id)
                    _ = get_string(language)
                except:
                    _ = get_string("en")

                if message.chat.type != ChatType.SUPERGROUP:
                    await message.reply_text(_["start_4"])
                    await client.leave_chat(message.chat.id)
                    return
                
                # Blacklist Check (Optional)
                if message.chat.id in await blacklisted_chats():
                    await client.leave_chat(message.chat.id)
                    return

                buttons = clone_private_panel(_, a.username)

                await message.reply_photo(
                    random.choice(YUMI_PICS),
                    caption=_["start_3"].format(
                        message.from_user.first_name,
                        a.mention,
                        message.chat.title,
                        a.mention,
                    ),
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
                await add_served_chat_clone(message.chat.id)
                
                # Auto Join Assistant on Welcome
                try:
                    userbot = await get_assistant(message.chat.id)
                    invitelink = await client.export_chat_invite_link(message.chat.id)
                    if "+" in invitelink:
                        link_hash = invitelink.split("+")[1]
                        await userbot.join_chat(f"https://t.me/joinchat/{link_hash}")
                    else:
                        await userbot.join_chat(invitelink)
                except:
                    pass

        except Exception as ex:
            print(ex)
