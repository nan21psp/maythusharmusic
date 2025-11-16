import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import (
    ApiIdInvalid, ApiIdPublishedFlood, FloodWait,
    PhoneNumberInvalid, PhoneCodeInvalid,
    PasswordHashInvalid, PasswordRequired, UserNotParticipant
)

# Bot ရဲ့ main app ကို import လုပ်ပါ
from maythusharmusic.core.bot import app
# SUDOERS တွေကိုပဲ ခွင့်ပြုဖို့ import လုပ်ပါ
from maythusharmusic.misc import SUDOERS

# Bot Owner (SUDOERS) တွေက Bot ရဲ့ Private Chat (DM) မှာပဲ သုံးလို့ရအောင် filter လုပ်ထားပါ
@app.on_message(filters.command(["string", "session", "genstring"]) & SUDOERS & filters.private)
async def string_gen(client: Client, message: Message):
    user_id = message.from_user.id
    ask_msg = None
    session_string = None
    
    async def get_response(text: str) -> Message:
        """Helper function to ask a question and get a response"""
        nonlocal ask_msg
        ask_msg = await message.reply_text(text, quote=True)
        try:
            # စက္ကန့် 300 (5 မိနစ်) အတွင်း reply ပြန်ဖို့ စောင့်ပါ
            response = await client.wait_for_message(
                chat_id=user_id,
                timeout=300
            )
            if response:
                await response.delete() # User ရဲ့ reply ကို ဖျက်ပါ
            if ask_msg:
                await ask_msg.delete() # Bot ရဲ့ မေးခွန်းကို ဖျက်ပါ
            return response
        except asyncio.TimeoutError:
            if ask_msg:
                await ask_msg.delete()
            await message.reply_text("Time limit reached (5 minutes). Please try again.")
            raise

    try:
        # 1. API_ID တောင်းပါ
        api_id_msg = await get_response("Please send your **API_ID**.\n\n(my.telegram.org က ရတဲ့ နံပါတ်ပါ။)")
        if not api_id_msg.text or not api_id_msg.text.isdigit():
            return await message.reply_text("API_ID must be a number. Please try again.")
        api_id = int(api_id_msg.text)

        # 2. API_HASH တောင်းပါ
        api_hash_msg = await get_response("Please send your **API_HASH**.\n\n(my.telegram.org က ရတဲ့ စာတန်းပါ။)")
        if not api_hash_msg.text:
             return await message.reply_text("API_HASH is invalid. Please try again.")
        api_hash = api_hash_msg.text

        # 3. Phone Number တောင်းပါ
        phone_msg = await get_response("Please send your **Phone Number** (with country code, e.g., +95...).")
        if not phone_msg.text:
             return await message.reply_text("Phone number is invalid. Please try again.")
        phone_number = phone_msg.text

        # --- Memory ထဲမှာ Client အသစ်တစ်ခု တည်ဆောက်ပါ ---
        await message.reply_text("Sending OTP to your phone...")
        temp_client = Client(":memory:", api_id=api_id, api_hash=api_hash)
        
        await temp_client.connect()
        sent_code = await temp_client.send_code(phone_number)
        
        # 4. OTP တောင်းပါ
        otp_msg = await get_response("Please send the **OTP** you received (e.g., 12345).\n\n(Code က Telegram account ထဲကို ရောက်ပါမယ်။)")
        if not otp_msg.text:
             return await message.reply_text("OTP is invalid. Please try again.")
        otp = otp_msg.text

        try:
            await temp_client.sign_in(phone_number, sent_code.phone_code_hash, otp)
        
        # 5. 2FA Password တောင်းပါ
        except PasswordRequired:
            password_msg = await get_response("Please send your **2FA Password** (Cloud Password).")
            if not password_msg.text:
                 return await message.reply_text("Password invalid. Please try again.")
            password = password_msg.text
            try:
                await temp_client.check_password(password)
            except PasswordHashInvalid:
                return await message.reply_text("Wrong 2FA Password. Please try again.")

        # 6. Session String ကို ထုတ်ယူပါ
        session_string = await temp_client.export_session_string()
        await temp_client.disconnect()
        
        await message.reply_text(
            f"**Success!**\n\nYour session string is:\n`{session_string}`\n\n"
            "ဒါကို copy ယူပြီး သင့် Bot ရဲ့ `config.py` (ဒါမှမဟုတ် `.env`) file ထဲမှာ `STRING1` အဖြစ် ထည့်ပေးပါ။"
        )

    except ApiIdInvalid:
        return await message.reply_text("API_ID or API_HASH is invalid. Please try again.")
    except ApiIdPublishedFlood:
         return await message.reply_text("Your API_ID is banned. Please use another one.")
    except PhoneNumberInvalid:
        return await message.reply_text("Phone number is invalid. Please try again (e.g., +95...).")
    except PhoneCodeInvalid:
        return await message.reply_text("The OTP you sent is invalid. Please try again.")
    except FloodWait as e:
        return await message.reply_text(f"You are being rate-limited. Please wait {e.value} seconds and try again.")
    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")
    finally:
        # မတော်တဆ မေးခွန်း message ကျန်ခဲ့ရင် ဖျက်ပါ
        if ask_msg and not getattr(ask_msg, 'is_deleted', True):
            try:
                await ask_msg.delete()
            except:
                pass
