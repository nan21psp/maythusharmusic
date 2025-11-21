import socket
import time
import requests
from pyrogram import filters

import config
from maythusharmusic.core.mongo import mongodb

from .logging import LOGGER

SUDOERS = filters.user()

_boot_ = time.time()


def is_render():
    return "render" in socket.getfqdn() or "onrender.com" in socket.getfqdn()


XCB = [
    "/",
    "@",
    ".",
    "com",
    ":",
    "git",
    "push",
    "https",
    "HEAD",
    "master",
]


def dbb():
    global db
    db = {}
    LOGGER(__name__).info(f" Database loaded..")


async def sudo():
    global SUDOERS
    SUDOERS.add(config.OWNER_ID)
    sudoersdb = mongodb.sudoers
    sudoers = await sudoersdb.find_one({"sudo": "sudo"})
    sudoers = [] if not sudoers else sudoers["sudoers"]
    if config.OWNER_ID not in sudoers:
        sudoers.append(config.OWNER_ID)
        await sudoersdb.update_one(
            {"sudo": "sudo"},
            {"$set": {"sudoers": sudoers}},
            upsert=True,
        )
    if sudoers:
        for user_id in sudoers:
            SUDOERS.add(user_id)
    LOGGER(__name__).info(f"Sudo users loaded...")


def render_app():
    """Render.com app configuration"""
    if is_render():
        try:
            # Render-specific configurations
            LOGGER(__name__).info(f"Render App Configured")
            
            # Render မှာ automatic deployment ရှိလို့ restart logic မလိုတော့ဘူး
            # Environment variables ကို Render dashboard ကနေ directly manage လုပ်နိုင်တယ်
            
        except BaseException as e:
            LOGGER(__name__).warning(
                f"Render configuration check: {e}"
            )


def restart():
    """Render doesn't need manual restart like Heroku"""
    if is_render():
        LOGGER(__name__).info("Render: Changes will deploy automatically on git push")
        return True
    else:
        # Local development restart logic here
        pass


# Initialize Render app
render_app()
