import asyncio
import config  # <-- 1. config file ကို import လုပ်ပါ
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import (
    ApiIdInvalid, ApiIdPublishedFlood, FloodWait,
    PhoneNumberInvalid, PhoneCodeInvalid,
    PasswordHashInvalid, PasswordRequired, UserNotParticipant
)

# Bot ရဲ့ main app (Hotty) ကို import လုပ်ပြီး 'app' လို့ နာမည်ပြောင်း သုံးပါ
from maythusharmusic.core.bot import Hotty as app
# SUDOERS import ကို မသုံးတော့ပါ (သို့မဟုတ် တခြားနေရာမှာ သုံးရင် ထားခဲ့နိုင်)
# from maythusharmusic.misc import SUDOERS 

# --- 2. Filter ကို SUDOERS အစား config.OWNER_ID ဖြင့် ပြောင်းပါ ---
@app.on_message(filters.command(["string", "session", "genstring"]) & filters.user(config.OWNER_ID) & filters.private)
async def string_gen(client: Client, message: Message):
    user_id = message.from_user.id
    ask_msg = None
    session_string = None
    phone_number = None # Phone number ကို မှတ်ထားဖို့
    api_id = None # API ID ကို မှတ်ထားဖို့
    
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
        api_id = int(api_id_msg.text) # <-- api_id ကို မှတ်ထားပါ

        # 2. API_HASH တောင်းပါ
        api_hash_msg = await get_response("Please send your **API_HASH**.\n\n(my.telegram.org က ရတဲ့ စာတန်းပါ။)")
        if not api_hash_msg.text:
             return await message.reply_text("API_HASH is invalid. Please try again.")
        api_hash = api_hash_msg.text

        # 3. Phone Number တောင်းပါ
        phone_msg = await get_response("Please send your **Phone Number** (with country code, e.g., +95...).")
        if not phone_msg.text:
             return await message.reply_text("Phone number is invalid. Please try again.")
        phone_number = phone_msg.text # <-- phone_number ကို မှတ်ထားပါ

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
        
        # --- START: (Saved Messages သို့ ပို့ရန် ပြင်ဆင်ထားသည်) ---
        
        # 7. User ရဲ့ Saved Messages ကို အရင်ပို့ပါ
        try:
            await temp_client.send_message(
                "me", # "me" (Saved Messages) ကို ပို့ပါ
                f"**Success!**\n\nYour session string for `{api_id}` is:\n\n`{session_string}`\n\n"
                "**Please keep this secret and NEVER share it with anyone!**\n"
                "You can now use this in your bot's configuration."
            )
        except Exception as e:
            # Saved Messages ကို ပို့တာ မအောင်မြင်ခဲ့ရင် (Fallback)
            await message.reply_text(
                f"**Success!**\n\n"
                f"I couldn't send the string to your Saved Messages (Error: {e}).\n"
                f"Here is your session string:\n`{session_string}`"
            )
            await temp_client.disconnect()
            return

        # 8. Client ကို disconnect လုပ်ပါ
        await temp_client.disconnect()
        
        # 9. User ကို Bot DM ကနေ အကြောင်းကြားပါ
        await message.reply_text(
            f"**Success!**\n\n"
            f"I have sent the session string to your **Saved Messages** (from the account {phone_number}).\n\n"
            "Please check your Saved Messages and copy it from there."
        )
        
        # --- END: (Saved Messages သို့ ပို့ရန် ပြင်ဆင်ထားသည်) ---

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
