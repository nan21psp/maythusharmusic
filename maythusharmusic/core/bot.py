import asyncio
from pyrogram import Client, errors
from pyrogram.enums import ChatMemberStatus, ParseMode

import config
from ..logging import LOGGER

class Hotty(Client):
    def __init__(self):
        LOGGER(__name__).info(f"Starting Bot...")
        super().__init__(
            name="maythusharmusic",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            in_memory=True,
            max_concurrent_transmissions=7,
        )

    async def start(self):
        await super().start()
        self.id = self.me.id
        self.name = self.me.first_name + " " + (self.me.last_name or "")
        self.username = self.me.username
        self.mention = self.me.mention

        try:
            await self.send_message(
                chat_id=config.LOGGER_ID,
                text=f"<u><b>» {self.mention} ʙᴏᴛ sᴛᴀʀᴛᴇᴅ :</b><u>\n\nɪᴅ : <code>{self.id}</code>\nɴᴀᴍᴇ : {self.name}\nᴜsᴇʀɴᴀᴍᴇ : @{self.username}",
            )
        except (errors.ChannelInvalid, errors.PeerIdInvalid):
            LOGGER(__name__).error(
                "Bot has failed to access the log group/channel. Make sure that you have added your bot to your log group/channel."
            )

        except Exception as ex:
            LOGGER(__name__).error(
                f"Bot has failed to access the log group/channel.\n  Reason : {type(ex).__name__}."
            )

        try:
            a = await self.get_chat_member(config.LOGGER_ID, self.id)
            if a.status != ChatMemberStatus.ADMINISTRATOR:
                LOGGER(__name__).error(
                    "Please promote your bot as an admin in your log group/channel."
                )
        except:
            pass

        LOGGER(__name__).info(f"Music Bot Started as {self.name}")

    async def stop(self):
        await super().stop()

    # --- (၁) စာပို့တိုင်း Clean Mode ထဲ အလိုအလျောက်ထည့်မည့် Function ---
    async def add_to_clean(self, chat_id, message_id):
        try:
            # Log Group မဟုတ်မှသာ ဖျက်မည်
            if chat_id != config.LOGGER_ID:
                # Database function ကို ဒီမှာမှ Import လုပ်ပါ (Circular Import ရှောင်ရန်)
                from maythusharmusic.utils.database import add_clean_message
                await add_clean_message(chat_id, message_id)
        except:
            pass

    # --- (၂) send_message ကို ကြားဖြတ်ပြီး Clean Mode ထည့်ခြင်း ---
    async def send_message(self, chat_id, text, *args, **kwargs):
        message = await super().send_message(chat_id, text, *args, **kwargs)
        # ပို့ပြီးတာနဲ့ Clean List ထဲထည့်မည်
        await self.add_to_clean(chat_id, message.id)
        return message

    # --- (၃) send_photo ကို ကြားဖြတ်ပြီး Clean Mode ထည့်ခြင်း ---
    async def send_photo(self, chat_id, photo, *args, **kwargs):
        message = await super().send_photo(chat_id, photo, *args, **kwargs)
        await self.add_to_clean(chat_id, message.id)
        return message

    # --- (၄) send_video ကို ကြားဖြတ်ပြီး Clean Mode ထည့်ခြင်း ---
    async def send_video(self, chat_id, video, *args, **kwargs):
        message = await super().send_video(chat_id, video, *args, **kwargs)
        await self.add_to_clean(chat_id, message.id)
        return message
