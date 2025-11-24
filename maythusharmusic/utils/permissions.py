import logging
from functools import wraps
from traceback import format_exc as err

from pyrogram import Client
from pyrogram.errors.exceptions.forbidden_403 import ChatWriteForbidden
from pyrogram.types import Message

from maythusharmusic import app
from maythusharmusic.misc import SUDOERS


# (၁) Client ကို Parameter အနေနဲ့ လက်ခံအောင် ပြင်ဆင်ခြင်း
async def member_permissions(chat_id: int, user_id: int, client: Client = app):
    perms = []
    try:
        # app အစား client ကို သုံးပါ
        member = (await client.get_chat_member(chat_id, user_id)).privileges
    except Exception:
        return []
        
    if not member:
        return []
    if member.can_post_messages:
        perms.append("can_post_messages")
    if member.can_edit_messages:
        perms.append("can_edit_messages")
    if member.can_delete_messages:
        perms.append("can_delete_messages")
    if member.can_restrict_members:
        perms.append("can_restrict_members")
    if member.can_promote_members:
        perms.append("can_promote_members")
    if member.can_change_info:
        perms.append("can_change_info")
    if member.can_invite_users:
        perms.append("can_invite_users")
    if member.can_pin_messages:
        perms.append("can_pin_messages")
    if member.can_manage_video_chats:
        perms.append("can_manage_video_chats")
    return perms


async def authorised(func, subFunc2, client, message, *args, **kwargs):
    chatID = message.chat.id
    try:
        await func(client, message, *args, **kwargs)
    except ChatWriteForbidden:
        # app အစား client ကို သုံးပါ
        await client.leave_chat(chatID)
    except Exception as e:
        logging.exception(e)
        try:
            await message.reply_text(str(e.MESSAGE))
        except AttributeError:
            await message.reply_text(str(e))
        e = err()
        print(str(e))
    return subFunc2


async def unauthorised(
    message: Message, permission, subFunc2, bot_lacking_permission=False
):
    chatID = message.chat.id
    if bot_lacking_permission:
        text = (
            "I don't have the required permission to perform this action."
            + f"\n**Permission:** __{permission}__"
        )
    else:
        text = (
            "You don't have the required permission to perform this action."
            + f"\n**Permission:** __{permission}__"
        )
    try:
        await message.reply_text(text)
    except ChatWriteForbidden:
        # Client ကို message ကနေ ယူပါ
        client = getattr(message, "_client", app)
        await client.leave_chat(chatID)
    return subFunc2


# (၂) Client ကို Parameter အနေနဲ့ လက်ခံအောင် ပြင်ဆင်ခြင်း
async def bot_permissions(chat_id: int, client: Client = app):
    perms = []
    bot_id = (await client.get_me()).id
    return await member_permissions(chat_id, bot_id, client)


def adminsOnly(permission):
    def subFunc(func):
        @wraps(func)
        async def subFunc2(client, message: Message, *args, **kwargs):
            chatID = message.chat.id

            # (၃) Bot Permission စစ်ဆေးရာတွင် client ကို ထည့်ပေးပါ
            bot_perms = await bot_permissions(chatID, client)
            if permission not in bot_perms:
                return await unauthorised(
                    message, permission, subFunc2, bot_lacking_permission=True
                )

            if not message.from_user:
                # For anonymous admins
                if message.sender_chat and message.sender_chat.id == message.chat.id:
                    return await authorised(
                        func,
                        subFunc2,
                        client,
                        message,
                        *args,
                        **kwargs,
                    )
                return await unauthorised(message, permission, subFunc2)

            # For admins and sudo users
            userID = message.from_user.id
            
            # (၄) Member Permission စစ်ဆေးရာတွင် client ကို ထည့်ပေးပါ
            permissions = await member_permissions(chatID, userID, client)
            if userID not in SUDOERS and permission not in permissions:
                return await unauthorised(message, permission, subFunc2)
            return await authorised(func, subFunc2, client, message, *args, **kwargs)

        return subFunc2

    return subFunc
