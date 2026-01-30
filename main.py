import asyncio
import random
import logging
import time
from pyrogram import Client, filters, enums, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN

# Import DB Functions (Removed set/get emoji functions)
from database import (
    add_clone, get_all_clones, remove_clone
)

# --- DEBUGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ReactionBot")

# Initialize Manager Bot
app = Client("ManagerBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
CLONE_CLIENTS = {} 

# GLOBAL CACHE TO PREVENT DUPLICATE REACTIONS
# Format: { "chat_id:msg_id": {"🔥", "❤️"} }
USED_EMOJIS_CACHE = {}

def smcp(text):
    mapping = {
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ',
        'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ',
        's': 's', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ғ', 'G': 'ɢ', 'H': 'ʜ', 'I': 'ɪ',
        'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ', 'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ',
        'S': 's', 'T': 'ᴛ', 'U': 'ᴜ', 'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ',
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉'
    }
    return "".join(mapping.get(c, c) for c in text)

# Expanded Emoji List for variety
RANDOM_EMOJIS = [
    "👍", "❤️", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱", "🎉", 
    "🤩", "⚡️", "🍓", "🚀", "🏆", "👻", "👀", "🍌", "🌚", "💔",
    "💯", "💩", "🤮", "🍾", "🐳", "🎃", "👺", "🤡", "😇", "🤝"
]

# --- CLEANUP TASK ---
# Ye function purane messages ka cache clear karega taaki RAM na bhare
async def cache_cleanup():
    while True:
        try:
            current_time = time.time()
            # Keys are "chat_id:msg_id:timestamp"
            # We need a complex structure or just clear everything every 10 mins
            # Simple approach: Clear all cache every 5 minutes (old msgs dont need unique checks)
            USED_EMOJIS_CACHE.clear()
            # logger.info("🧹 Cache Cleared")
            await asyncio.sleep(300) # 5 Minutes
        except:
            await asyncio.sleep(60)

# --- UNIQUE REACTION LOGIC ---
async def unique_reaction_logic(client, message):
    try:
        chat_id = message.chat.id
        msg_id = message.id
        unique_key = f"{chat_id}:{msg_id}"

        # Initialize cache set for this message if not exists
        if unique_key not in USED_EMOJIS_CACHE:
            USED_EMOJIS_CACHE[unique_key] = set()

        # Find emojis that are NOT used yet
        available_emojis = [e for e in RANDOM_EMOJIS if e not in USED_EMOJIS_CACHE[unique_key]]

        if not available_emojis:
            # If all emojis used, pick random (fallback)
            emoji = random.choice(RANDOM_EMOJIS)
        else:
            # Pick a unique one
            emoji = random.choice(available_emojis)
        
        # Mark this emoji as used IMMEDIATELY
        USED_EMOJIS_CACHE[unique_key].add(emoji)
            
        await client.send_reaction(chat_id, msg_id, emoji)
        logger.info(f"✅ {client.me.first_name} -> {emoji}")

    except Exception as e:
        # logger.error(f"❌ Reaction Failed: {e}")
        pass

# --- HANDLERS ---

async def start_handler(client, message: Message):
    bot_name = client.me.first_name
    bot_username = client.me.username
    txt = (
        f"👋 <b>{smcp('Hello')}! {smcp('I am')} {bot_name}</b>\n\n"
        f"🤖 {smcp('I am a Smart Reaction Bot.')}\n"
        f"✨ {smcp('Add me to your group, and I will give UNIQUE reactions!')}\n"
    )
    btn = InlineKeyboardMarkup([[InlineKeyboardButton(text=f"➕ {smcp('Add Me To Your Group')}", url=f"https://t.me/{bot_username}?startgroup=true")]])
    await message.reply(txt, reply_markup=btn, parse_mode=enums.ParseMode.HTML)

# --- START CLONE FUNCTION ---
async def start_clone(token):
    try:
        cl = Client(f"clone_{token[:10]}", api_id=API_ID, api_hash=API_HASH, bot_token=token, in_memory=True)
        
        # Start Handler
        @cl.on_message(filters.private & filters.command("start"))
        async def _start(c, m): await start_handler(c, m)

        # Unique Reaction Watcher
        @cl.on_message(filters.channel | filters.group)
        async def _react(c, m): await unique_reaction_logic(c, m)

        await cl.start()
        CLONE_CLIENTS[cl.me.id] = cl
        return cl.me
    except Exception as e:
        logger.error(f"Clone Start Error: {e}")
        return None

# --- MANAGER COMMANDS ---

@app.on_message(filters.private & filters.command("start"))
async def manager_start(client, message): await start_handler(client, message)

@app.on_message(filters.command("clone"))
async def clone_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply(f"{smcp('Usage')}: `/clone [TOKEN]`")
    token = message.text.split(None, 1)[1].strip()
    msg = await message.reply(f"⚙️ <b>{smcp('Cloning Bot')}...</b>", parse_mode=enums.ParseMode.HTML)
    
    bot_info = await start_clone(token)
    
    if bot_info:
        await add_clone(token, bot_info.id, bot_info.first_name)
        txt = (f"✅ <b>{smcp('Bot Cloned Successfully')}!</b>\n\n🤖 <b>{smcp('Name')}:</b> {bot_info.first_name}\n🆔 <b>ID:</b> <code>{bot_info.id}</code>")
        await msg.edit(txt, parse_mode=enums.ParseMode.HTML)
    else:
        await msg.edit(f"❌ <b>{smcp('Failed to clone.')}</b>", parse_mode=enums.ParseMode.HTML)

@app.on_message(filters.command("remove"))
async def remove_bot_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply(f"{smcp('Usage')}: `/remove [BOT_ID]`")
    try:
        bot_id = int(message.text.split(None, 1)[1].strip())
    except:
        return await message.reply(f"❌ <b>{smcp('Invalid Bot ID')}!</b>", parse_mode=enums.ParseMode.HTML)
    
    msg = await message.reply(f"🗑 <b>{smcp('Removing Bot')}...</b>", parse_mode=enums.ParseMode.HTML)
    if bot_id in CLONE_CLIENTS:
        try:
            await CLONE_CLIENTS[bot_id].stop()
            del CLONE_CLIENTS[bot_id]
        except Exception as e:
            logger.error(f"Stop Error: {e}")
    await remove_clone(bot_id)
    await msg.edit(f"✅ <b>{smcp('Bot Removed Successfully')}!</b>", parse_mode=enums.ParseMode.HTML)

# --- MANAGER WATCHER ---
@app.on_message(filters.channel | filters.group)
async def manager_auto_react(client, message):
    await unique_reaction_logic(client, message)

# --- BOOT ---
async def boot():
    logger.info("🔄 Loading Saved Clones...")
    clones = await get_all_clones()
    count = 0
    for c in clones:
        token = c.get('token')
        if not token: continue
        if await start_clone(token): count += 1
    logger.info(f"🚀 {count} Clones Live!")
    
    # Start Cache Cleanup Task
    asyncio.create_task(cache_cleanup())

async def main():
    await app.start()
    await boot()
    logger.info("🔥 Manager Bot Live!")
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
