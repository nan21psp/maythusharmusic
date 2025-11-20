import time
import asyncio
import random
import traceback
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
import config
from maythusharmusic import app
from maythusharmusic.utils.database import (
    add_served_chat_clone,
    add_served_user_clone,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    get_assistant,
)
from maythusharmusic.utils.decorators.language import LanguageStart
from maythusharmusic.utils.inline import private_panel
from strings import get_string

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

private_panel = clone_start_pm

# --- CLONE BOT BUTTON FUNCTION ---
def clone_start_pm(_, bot_username):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_3"], # အုပ်စုသို့ထည့်ရန်
                url=f"https://t.me/{app_username}?startgroup=s&admin=delete_messages+manage_video_chats+pin_messages+invite_users+ban_users",
            )
        ],
        [
            InlineKeyboardButton(text=_["S_B_5"], user_id=config.OWNER_ID), # ပိုင်ရှင်
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_CHAT), # အကူအညီ
        ],
        [
            InlineKeyboardButton(text=_["S_B_6"], url=config.SUPPORT_CHANNEL), # ချန်နယ်
        ],
    ]
    return buttons
# ---------------------------------

@Client.on_message(filters.command(["start"]) & filters.private & ~filters.banned)
@LanguageStart
async def start_pm(client: Client, message: Message, _):
    try:
        # 1. Get Bot Info
        a = await client.get_me()
        bot_username = a.username
        bot_name = a.first_name
        
        # 2. Spam Protection
        user_id = message.from_user.id
        current_time = time.time()
        last_message_time = user_last_message_time.get(user_id, 0)

        if current_time - last_message_time < SPAM_WINDOW_SECONDS:
            user_last_message_time[user_id] = current_time
            user_command_count[user_id] = user_command_count.get(user_id, 0) + 1
            if user_command_count[user_id] > SPAM_THRESHOLD:
                hu = await message.reply_text(f"**{message.from_user.mention} Please don't spam!**")
                await asyncio.sleep(3)
                await hu.delete()
                return
        else:
            user_command_count[user_id] = 1
            user_last_message_time[user_id] = current_time

        # 3. Add User to Database
        await add_served_user_clone(message.from_user.id)

        # 4. Send Start Message
        if len(message.text.split()) > 1:
            name = message.text.split(None, 1)[1]
            if name[0:4] == "help":
                # Help command အတွက် Logic (လိုအပ်ရင် ထပ်ဖြည့်ပါ)
                await message.reply_text("Help Menu is coming soon!")
                return

        # Normal Start
        keyboard = clone_start_pm(_, bot_username)
        await message.reply_photo(
            photo=config.START_IMG_URL,
            caption=_["start_2"].format(message.from_user.mention, a.mention),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    except Exception as e:
        print(f"Start PM Error: {traceback.format_exc()}")


@Client.on_message(filters.command(["start"]) & filters.group & ~filters.banned)
@LanguageStart
async def start_gp(client: Client, message: Message, _):
    try:
        a = await client.get_me()
        user_id = message.from_user.id
        
        # Button for Group
        out = clone_start_pm(_, a.username)
        
        await message.reply_photo(
            photo=config.START_IMG_URL,
            caption=f"Hello! I am {a.mention}.\nThanks for adding me in {message.chat.title}.",
            reply_markup=InlineKeyboardMarkup(out),
        )
        await add_served_chat_clone(message.chat.id)

        # Assistant Checking Logic
        userbot = await get_assistant(message.chat.id)
        try:
            await client.get_chat_member(message.chat.id, userbot.id)
            # Assistant is already in group
            # (Do nothing or send confirm message)
        except:
            # Assistant not in group, try to invite
            try:
                invitelink = await client.export_chat_invite_link(message.chat.id)
                if "+" in invitelink:
                    link_hash = invitelink.split("+")[1]
                    await userbot.join_chat(f"https://t.me/joinchat/{link_hash}")
                else:
                    await userbot.join_chat(invitelink)
                await message.reply_text(f"✅ Assistant (@{userbot.username}) joined successfully.")
            except Exception as e:
                # Invite failed (Need Admin)
                pass 

    except Exception as e:
        print(f"Start Group Error: {traceback.format_exc()}")
