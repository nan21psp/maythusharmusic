from strings import get_string
from maythusharmusic.misc import SUDOERS
from maythusharmusic.utils.database import (get_lang, is_maintenance)


def language(mystic):
    async def wrapper(_, message, **kwargs):
        if await is_maintenance() is False:
            if message.from_user.id not in SUDOERS:
                return await message.reply_text(
                    text=f"{app.mention} ɪs ᴜɴᴅᴇʀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ, ᴠɪsɪᴛ <a href={SUPPORT_CHAT}>sᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ</a> ғᴏʀ ᴋɴᴏᴡɪɴɢ ᴛʜᴇ ʀᴇᴀsᴏɴ.",
                    disable_web_page_preview=True,
                )
        try:
            await message.delete()
        except:
            pass

        try:
            language_code = await get_lang(message.chat.id)
            # Language code မှန်မမှန်စစ်ဆေးပါ
            if not language_code or not isinstance(language_code, str):
                language_code = "en"
            
            language_strings = get_string(language_code)
            
            # Language strings ရလာတာမှန်မမှန်စစ်ဆေးပါ
            if not language_strings or not isinstance(language_strings, dict):
                print(f"Invalid language strings for code: {language_code}")
                language_strings = get_string("en")
                
        except Exception as e:
            print(f"Language error: {e}")
            language_strings = get_string("en")
            
        return await mystic(_, message, language_strings)

    return wrapper


def languageCB(mystic):
    async def wrapper(_, CallbackQuery, **kwargs):
        if await is_maintenance() is False:
            if CallbackQuery.from_user.id not in SUDOERS:
                return await CallbackQuery.answer(
                    f"{app.mention} ɪs ᴜɴᴅᴇʀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ, ᴠɪsɪᴛ sᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ ғᴏʀ ᴋɴᴏᴡɪɴɢ ᴛʜᴇ ʀᴇᴀsᴏɴ.",
                    show_alert=True,
                )
        try:
            language_code = await get_lang(CallbackQuery.message.chat.id)
            # Language code မှန်မမှန်စစ်ဆေးပါ
            if not language_code or not isinstance(language_code, str):
                language_code = "en"
            
            language_strings = get_string(language_code)
            
            # Language strings ရလာတာမှန်မမှန်စစ်ဆေးပါ
            if not language_strings or not isinstance(language_strings, dict):
                print(f"Invalid language strings for code: {language_code}")
                language_strings = get_string("en")
                
        except Exception as e:
            print(f"Language error: {e}")
            language_strings = get_string("en")
            
        return await mystic(_, CallbackQuery, language_strings)

    return wrapper


def LanguageStart(mystic):
    async def wrapper(_, message, **kwargs):
        try:
            language_code = await get_lang(message.chat.id)
            # Language code မှန်မမှန်စစ်ဆေးပါ
            if not language_code or not isinstance(language_code, str):
                language_code = "en"
            
            language_strings = get_string(language_code)
            
            # Language strings ရလာတာမှန်မမှန်စစ်ဆေးပါ
            if not language_strings or not isinstance(language_strings, dict):
                print(f"Invalid language strings for code: {language_code}")
                language_strings = get_string("en")
                
        except Exception as e:
            print(f"Language error: {e}")
            language_strings = get_string("en")
            
        return await mystic(_, message, language_strings)

    return wrapper
