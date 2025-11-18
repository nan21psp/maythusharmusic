from maythusharmusic.core.mongo import mongodb, pymongodb
from typing import Dict, List, Union

cloneownerdb = mongodb.cloneownerdb
clonebotdb = pymongodb.clonebotdb
clonebotnamedb = mongodb.clonebotnamedb


# clone bot owner
async def save_clonebot_owner(bot_id, user_id):
    await cloneownerdb.insert_one({"bot_id": bot_id, "user_id": user_id})


async def get_clonebot_owner(bot_id):
    result = await cloneownerdb.find_one({"bot_id": bot_id})
    if result:
        return result.get("user_id")
    else:
        return False


async def save_clonebot_username(bot_id, user_name):
    await clonebotnamedb.insert_one({"bot_id": bot_id, "user_name": user_name})


async def get_clonebot_username(bot_id):
    result = await clonebotnamedb.find_one({"bot_id": bot_id})
    if result:
        return result.get("user_name")
    else:
        return False

from typing import Union
from maythusharmusic.core.mongo import mongodb, pymongodb

# Token တွေကို သီးသန့် collection တစ်ခုမှာ သိမ်းပါမယ်
clonetokendb = mongodb.clonetokens

async def save_clone_token(bot_id: int, bot_token: str):
    """Clone bot ရဲ့ token ကို database မှာ သိမ်းဆည်းပါ"""
    await clonetokendb.update_one(
        {"bot_id": bot_id},
        {"$set": {"bot_token": bot_token}},
        upsert=True
    )

async def get_clone_token(bot_id: int) -> Union[str, None]:
    """Clone bot ရဲ့ token ကို database ကနေ ပြန်ရှာပါ"""
    doc = await clonetokendb.find_one({"bot_id": bot_id})
    return doc.get("bot_token") if doc else None

async def get_all_clones() -> list:
    """Clone လုပ်ထားတဲ့ bot အားလုံးရဲ့ list ကို ပြန်ယူပါ (bot instance တွေ run ဖို့)"""
    clones = []
    # (သင့် file ထဲမှာ cloneownerdb ရှိပြီးသားမို့ အဲ့ဒါကိုပဲ သုံးပါတယ်)
    async for clone in cloneownerdb.find({"bot_id": {"$exists": True}}):
        clones.append(clone)
    return clones
