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
    is_banned_user,
    get_assistant,
)

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

# --- (၁) ခလုတ်များကို တိုက်ရိုက်ရေးသားခြင်း ---
def clone_start_pm(bot_username):
    buttons = [
        [
            InlineKeyboardButton(
                text="အုပ်စုသို့ထည့်ရန်", # S_B_3 အစား တိုက်ရိုက်ရေးလိုက်ပါ
                url=f"https://t.me/{app_username}?startgroup=s&admin=delete_messages+manage_video_chats+pin_messages+invite_users+ban_users",
            )
        ],
        [
            InlineKeyboardButton(text="ပိုင်ရှင်", user_id=config.OWNER_ID), # S_B_5
            InlineKeyboardButton(text="အကူအညီ", url=config.SUPPORT_CHAT), # S_B_2
        ],
        [
            InlineKeyboardButton(text="ချန်နယ်", url=config.SUPPORT_CHANNEL), # S_B_6
        ],
    ]
    return buttons
# ----------------------------------------

@Client.on_message(filters.command(["start"]) & filters.private & ~filters.banned)
async def start_pm(client: Client, message: Message):
    try:
        a = await client.get_me()
        bot_username = a.username
        
        # Spam Protection
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

        await add_served_user_clone(message.from_user.id)

        # Normal Start
        # --- (၂) Function ခေါ်ရာတွင် _ (language) ထည့်စရာမလိုတော့ပါ ---
        keyboard = clone_start_pm(bot_username)
        
        await message.reply_photo(
            photo=config.START_IMG_URL,
            caption=f"မင်္ဂလာပါ {message.from_user.mention} ဗျာ။\n\nကျွန်တော်ကတော့ {a.mention} (Music Bot) ဖြစ်ပါတယ်။\n\nကျွန်တော့်ကို Group ထဲထည့်ပြီး Admin ပေးထားရင် သီချင်းဖွင့်ပေးပါမယ်။",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    except Exception as e:
        print(f"Start PM Error: {traceback.format_exc()}")


@Client.on_message(filters.command(["start"]) & filters.group & ~filters.banned)
async def start_gp(client: Client, message: Message):
    try:
        a = await client.get_me()
        
        # Button for Group
        out = clone_start_pm(a.username)
        
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
        except:
            try:
                invitelink = await client.export_chat_invite_link(message.chat.id)
                if "+" in invitelink:
                    link_hash = invitelink.split("+")[1]
                    await userbot.join_chat(f"https://t.me/joinchat/{link_hash}")
                else:
                    await userbot.join_chat(invitelink)
                await message.reply_text(f"✅ Assistant (@{userbot.username}) joined successfully.")
            except Exception as e:
                pass 

    except Exception as e:
        print(f"Start Group Error: {traceback.format_exc()}")

@Client.on_message(filters.new_chat_members, group=-1)
async def welcome(client, message: Message):
    a = await client.get_me()
    for member in message.new_chat_members:
        try:
            if await is_banned_user(member.id):
                try:
                    await message.chat.ban_member(member.id)
                except:
                    pass
            if member.id == a.id:
                if message.chat.type != ChatType.SUPERGROUP:
                    await message.reply_text("Please make this group a Supergroup.")
                    await client.leave_chat(message.chat.id)
                    return
                if message.chat.id in await blacklisted_chats():
                    await client.leave_chat(message.chat.id)
                    return

                out = clone_start_pm(a.username)
                
                # Assistant Auto Join Logic
                try:
                    userbot = await get_assistant(message.chat.id)
                    if message.chat.username:
                        await userbot.join_chat(f"{message.chat.username}")
                    else:
                        invitelink = await client.export_chat_invite_link(message.chat.id)
                        await userbot.join_chat(invitelink)
                except:
                    pass

                await message.reply_photo(
                    random.choice(YUMI_PICS),
                    caption=f"Thanks for adding me to {message.chat.title}!\nI am {a.mention}.",
                    reply_markup=InlineKeyboardMarkup(out),
                )
                await add_served_chat_clone(message.chat.id)
        except Exception as ex:
            print(ex)
