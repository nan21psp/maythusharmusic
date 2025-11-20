def clone_private_panel(_, bot_username):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["Aᴅᴅ ᴍᴇ ʙᴀʙʏ"],
                url=f"https://t.me/{app_username}?startgroup=s&admin=delete_messages+manage_video_chats+pin_messages+invite_users+ban_users"
            )
        ],
        [
            InlineKeyboardButton("ᴏᴡɴᴇʀ", url="https://t.me/iwillgoforwardsalone"),
            InlineKeyboardButton("ꜱᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ", url="https://t.me/sasukemusicsupportchat"),
        ],
        [
            InlineKeyboardButton("ꜱᴜᴘᴘᴏʀᴛ ᴄʜᴀɴɴᴇʟ", url="https://t.me/everythingreset"),
        ],
    ]
    return buttons
