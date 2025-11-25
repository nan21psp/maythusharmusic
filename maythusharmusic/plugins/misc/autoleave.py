import asyncio
from datetime import datetime
from pyrogram.enums import ChatType

from pyrogram import Client, filters
import config
from maythusharmusic import app
from maythusharmusic.core.call import Hotty, autoend
from maythusharmusic.utils.database import (
    get_client,
    is_active_chat,
    is_autoend,
    get_autoleave,
    set_autoleave,
)

# --------------------- AUTO LEAVE SYSTEM ---------------------

async def auto_leave():
    while True:
        await asyncio.sleep(25200)  # 7 hours

        # database ထဲက autoleave status check
        status = await get_autoleave()
        if not status:
            continue

        from maythusharmusic.core.userbot import assistants

        for num in assistants:
            client = await get_client(num)
            left = 0

            try:
                async for i in client.get_dialogs():
                    if i.chat.type in [
                        ChatType.SUPERGROUP,
                        ChatType.GROUP,
                        ChatType.CHANNEL,
                    ]:
                        if i.chat.id not in [
                            config.LOGGER_ID,
                            -1002459775779,
                            -1002356385851,
                        ]:
                            if left == 150:
                                continue

                            if not await is_active_chat(i.chat.id):
                                try:
                                    await client.leave_chat(i.chat.id)
                                    left += 1
                                except:
                                    continue
            except:
                pass


asyncio.create_task(auto_leave())

# --------------------- AUTO END STREAM ---------------------

async def auto_end():
    while True:
        await asyncio.sleep(5)

        ender = await is_autoend()
        if not ender:
            continue

        for chat_id in autoend:
            timer = autoend.get(chat_id)
            if not timer:
                continue
            if datetime.now() > timer:
                if not await is_active_chat(chat_id):
                    autoend[chat_id] = {}
                    continue
                autoend[chat_id] = {}
                try:
                    await Hotty.stop_stream(chat_id)
                except:
                    continue
                try:
                    await app.send_message(
                        chat_id,
                        ">ʙᴏᴛ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ʟᴇғᴛ ᴠɪᴅᴇᴏᴄʜᴀᴛ ʙᴇᴄᴀᴜsᴇ ɴᴏ ᴏɴᴇ ᴡᴀs ʟɪsᴛᴇɴɪɴɢ ᴏɴ ᴠɪᴅᴇᴏᴄʜᴀᴛ.",
                    )
                except:
                    continue


asyncio.create_task(auto_end())

# --------------------- TELEGRAM COMMAND ---------------------

@app.on_message(filters.command(["autoleave"]) & ~BANNED_USERS)
async def autoleave_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply(
            "**Usage:** `/autoleave enable` or `/autoleave disable`"
        )

    query = message.command[1].lower()

    if query == "enable":
        await set_autoleave(True)
        return await message.reply("✅ **Auto Leave Enabled.**")

    elif query == "disable":
        await set_autoleave(False)
        return await message.reply("❌ **Auto Leave Disabled.**")

    else:
        return await message.reply("Invalid option. Use: enable / disable")
