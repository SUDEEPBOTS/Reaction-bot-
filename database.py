from pymongo import MongoClient
from config import MONGO_DB_URI

cluster = MongoClient(MONGO_DB_URI)
db = cluster["ReactionBotDB"]
clones_collection = db["clones"]
settings_collection = db["settings"]

# --- CLONE & BOT EMOJI ---

async def add_clone(token, bot_id, name):
    # await hataya kyunki pymongo sync hai
    clones_collection.update_one(
        {"bot_id": bot_id},
        {"$set": {"token": token, "name": name}},
        upsert=True
    )

async def set_bot_emoji(bot_id, emoji):
    clones_collection.update_one(
        {"bot_id": bot_id},
        {"$set": {"personal_emoji": emoji}},
        upsert=True
    )

async def get_bot_emoji(bot_id):
    doc = clones_collection.find_one({"bot_id": bot_id})
    return doc.get("personal_emoji", "🔥") if doc else "🔥"

async def get_all_clones():
    cursor = clones_collection.find({})
    return [doc for doc in cursor]

async def remove_clone(bot_id):
    clones_collection.delete_one({"bot_id": bot_id})

# --- CHANNEL SETTINGS (RANDOM MODE) ---

async def set_random_mode(chat_id, status: bool):
    settings_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"random_mode": status}},
        upsert=True
    )

async def is_random_on(chat_id):
    doc = settings_collection.find_one({"chat_id": chat_id})
    return doc.get("random_mode", False) if doc else False
