import asyncio
import random
import logging
import time
from pyrogram import Client, filters, enums, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN

# Import DB Functions
from database import (
    add_clone, get_all_clones, remove_clone
)

# --- ULTRA DEBUGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s"
)
logger = logging.getLogger("ReactionBot")

# Initialize Manager Bot
app = Client("ManagerBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
CLONE_CLIENTS = {} 

# GLOBAL CACHE
USED_EMOJIS_CACHE = {}
RANDOM_EMOJIS = [
    "👍", "❤️", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱", "🎉", 
    "🤩", "⚡️", "🍓", "🚀", "🏆", "👻", "👀", "🍌", "🌚", "💔",
    "💯", "💩", "🤮", "🍾", "🐳", "🎃", "👺", "🤡", "😇", "🤝"
]

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

# --- CACHE CLEANUP ---
async def cache_cleanup():
    while True:
        await asyncio.sleep(300) # 5 Mins
        USED_EMOJIS_CACHE.clear()
        # logger.info("🧹 Cache Cleared")

# --- CORE REACTION LOGIC (DEBUGGED) ---
async def react_everywhere(client, message):
    try:
        # 1. Log Incoming
        chat_id = message.chat.id
        msg_id = message.id
        bot_name = client.me.first_name
        
        # logger.info(f"📥 {bot_name} saw msg in {chat_id}")

        # 2. Unique Key & Logic
        unique_key = f"{chat_id}:{msg_id}"
        if unique_key not in USED_EMOJIS_CACHE:
            USED_EMOJIS_CACHE[unique_key] = set()

        # 3. Pick Unique Emoji
        available = [e for e in RANDOM_EMOJIS if e not in USED_EMOJIS_CACHE[unique_key]]
        if not available:
            emoji = random.choice(RANDOM_EMOJIS)
        else:
            emoji = random.choice(available)
        
        # Lock Emoji
        USED_EMOJIS_CACHE[unique_key].add(emoji)

        # 4. Small Delay (To prevent race conditions)
        await asyncio.sleep(random.uniform(0.1, 0.5))

        # 5. EXECUTE REACTION
        await client.send_reaction(chat_id, msg_id, emoji)
        logger.info(f"✅ SUCCESS: {bot_name} -> {emoji} in {chat_id}")

    except Exception as e:
        # ERROR LOGGING
        err = str(e)
        if "PEER_ID_INVALID" in err:
            logger.error(f"❌ {bot_name}: Bot not in chat or kicked.")
        elif "CHAT_ADMIN_REQUIRED" in err:
            logger.error(f"❌ {bot_name}: Need Admin Rights (Add as Admin).")
        elif "REACTION_INVALID" in err:
            logger.error(f"❌ {bot_name}: Invalid Emoji (Telegram rejected it).")
        else:
            logger.error(f"❌ {bot_name} Error: {err}")

# --- STARTUP HANDLER ---
async def start_handler(client, message: Message):
    # React first!
    await react_everywhere(client, message)
    
    # Then reply
    bot_name = client.me.first_name
    bot_username = client.me.username
    txt = (
        f"👋 <b>{smcp('Hello')}! {smcp('I am')} {bot_name}</b>\n\n"
        f"✨ {smcp('I will react to EVERYTHING!')}\n"
        f"➡️ {smcp('Just add me to Groups/Channels.')}"
    )
    btn = InlineKeyboardMarkup([[InlineKeyboardButton(text=f"➕ {smcp('Add Me')}", url=f"https://t.me/{bot_username}?startgroup=true")]])
    await message.reply(txt, reply_markup=btn, parse_mode=enums.ParseMode.HTML)

# --- CLONE BOOTER ---
async def start_clone(token):
    try:
        cl = Client(f"clone_{token[:10]}", api_id=API_ID, api_hash=API_HASH, bot_token=token, in_memory=True)
        
        # 1. /start Handler (DM)
        @cl.on_message(filters.private & filters.command("start"))
        async def _start(c, m): await start_handler(c, m)

        # 2. UNIVERSAL REACTION WATCHER (Reacts to EVERYTHING: DMs, Groups, Channels)
        # filters.incoming ensures we don't react to our own sent messages
        @cl.on_message(filters.incoming & ~filters.service) 
        async def _react(c, m): await react_everywhere(c, m)

        await cl.start()
        CLONE_CLIENTS[cl.me.id] = cl
        logger.info(f"🤖 Clone Online: {cl.me.first_name}")
        return cl.me
    except Exception as e:
        logger.error(f"⚠️ Clone Boot Failed: {e}")
        return None

# --- MANAGER COMMANDS ---

# Manager Reaction Watcher
@app.on_message(filters.incoming & ~filters.service & ~filters.command(["clone", "remove", "clean"]))
async def manager_react_watcher(client, message):
    await react_everywhere(client, message)

@app.on_message(filters.command("clone"))
async def clone_cmd(client, message):
    if len(message.command) < 2: return await message.reply("Usage: `/clone [TOKEN]`")
    token = message.text.split(None, 1)[1].strip()
    msg = await message.reply("⚙️ <b>Processing...</b>")
    bot_info = await start_clone(token)
    if bot_info:
        await add_clone(token, bot_info.id, bot_info.first_name)
        await msg.edit(f"✅ <b>{bot_info.first_name} Cloned!</b>")
    else:
        await msg.edit("❌ <b>Invalid Token</b>")

@app.on_message(filters.command("remove"))
async def remove_cmd(client, message):
    try:
        bot_id = int(message.text.split(None, 1)[1].strip())
        if bot_id in CLONE_CLIENTS:
            await CLONE_CLIENTS[bot_id].stop()
            del CLONE_CLIENTS[bot_id]
        await remove_clone(bot_id)
        await message.reply("✅ <b>Removed!</b>")
    except:
        await message.reply("Usage: `/remove [BOT_ID]`")

# --- MAIN ---
async def boot():
    logger.info("---------- STARTING MANAGER ----------")
    clones = await get_all_clones()
    for c in clones:
        if c.get('token'): await start_clone(c['token'])
    asyncio.create_task(cache_cleanup())

async def main():
    await app.start()
    await boot()
    logger.info("🔥 SYSTEM READY - WAITING FOR MESSAGES")
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
