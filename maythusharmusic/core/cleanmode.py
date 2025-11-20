# maythusharmusic/core/cleanmode.py

import asyncio
from maythusharmusic import app
from maythusharmusic.utils.database import get_expired_messages, remove_clean_message

async def clean_mode_task():
    """နောက်ကွယ်မှ အလုပ်လုပ်မည့် Clean Mode စနစ်"""
    while True:
        try:
            # 10 စက္ကန့်တစ်ခါ စစ်ဆေးမည်
            await asyncio.sleep(10)
            
            # အချိန်ပြည့်သွားသော စာများကို ရှာမည်
            expired_msgs = await get_expired_messages()
            
            for msg in expired_msgs:
                chat_id = msg["chat_id"]
                message_id = msg["message_id"]
                
                try:
                    # စာကို ဖျက်မည်
                    await app.delete_messages(chat_id, message_id)
                except Exception:
                    # ဖျက်မရရင် (ဥပမာ Bot Admin မဟုတ်တော့ရင်) ကျော်သွားမယ်
                    pass
                
                # Database ထဲကနေ စာရင်းဖျက်မည်
                await remove_clean_message(chat_id, message_id)
                
        except Exception as e:
            print(f"Clean Mode Error: {e}")
