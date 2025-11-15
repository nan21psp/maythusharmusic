import asyncio
from pyrogram import Client, filters
from pyrogram.handlers import VoiceChatMembersUpdatedHandler
from pyrogram.types import VoiceChatMembersUpdated

# Voice chat ကို လူ ဝင်/ထွက် တာကို စောင့်ကြည့်မယ့် Handler
@app.on_voice_chat_members_updated()
async def voice_chat_handler(client: Client, update: VoiceChatMembersUpdated):
    
    chat_id = update.chat.id
    
    # --- 1. Voice Chat ကို Join လာတဲ့ User တွေ ---
    if update.join_members:
        for member in update.join_members:
            try:
                # User ရဲ့ mention text ကို တည်ဆောက်မယ်
                mention_text = member.user.mention
                
                # Group ထဲကို message ပို့မယ်
                await client.send_message(
                    chat_id=chat_id,
                    text=f"👋 **Joined:** {mention_text} has joined the voice chat!"
                )
            except Exception as e:
                print(f"Error sending join message: {e}")

    # --- 2. Voice Chat ကနေ Leave သွားတဲ့ User တွေ ---
    if update.left_members:
        for member in update.left_members:
            try:
                # User ရဲ့ mention text ကို တည်ဆောက်မယ်
                mention_text = member.user.mention

                # Group ထဲကို message ပို့မယ်
                await client.send_message(
                    chat_id=chat_id,
                    text=f"💨 **Left:** {mention_text} has left the voice chat."
                )
            except Exception as e:
                print(f"Error sending left message: {e}")
