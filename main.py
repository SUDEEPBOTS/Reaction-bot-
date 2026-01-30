import asyncio
import random
import logging
from pyrogram import Client, filters, enums, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s"
)
logger = logging.getLogger("ReactionBot")

app = Client("ManagerBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
CLONE_CLIENTS = {} 
USED_EMOJIS_CACHE = {}

# --- UNIVERSAL SAFE EMOJIS ---
# Ye 6 emojis har Telegram channel/group mein default enabled hote hain
SAFE_EMOJIS = ["👍", "❤️", "🔥", "🥰", "👏", "🤩"]

def smcp(text):
    mapping = {'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ', 'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ғ', 'G': 'ɢ', 'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ', 'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 's', 'T': 'ᴛ', 'U': 'ᴜ', 'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ', '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉'}
    return "".join(mapping.get(c, c) for c in text)

async def react_logic(client, message):
    try:
        # 🚫 PRIVATE CHATS IGNORE (Error 400 BOT_METHOD_INVALID isi se aata hai)
        if message.chat.type == enums.ChatType.PRIVATE:
            return

        chat_id = message.chat.id
        msg_id = message.id
        
        # Unique Emoji Selection
        unique_key = f"{chat_id}:{msg_id}"
        if unique_key not in USED_EMOJIS_CACHE:
            USED_EMOJIS_CACHE[unique_key] = set()

        available = [e for e in SAFE_EMOJIS if e not in USED_EMOJIS_CACHE[unique_key]]
        emoji = random.choice(available) if available else random.choice(SAFE_EMOJIS)
        
        USED_EMOJIS_CACHE[unique_key].add(emoji)
        
        # 🔥 SEND REACTION
        await client.send_reaction(chat_id, msg_id, emoji)
        logger.info(f"✅ {client.me.first_name} reacted {emoji} in {chat_id}")

    except Exception as e:
        err = str(e)
        if "BOT_METHOD_INVALID" in err:
            # Ye tab aata hai jab bot DM mein react karne ki koshish kare
            pass 
        elif "CHAT_ADMIN_REQUIRED" in err:
            logger.error(f"❌ {client.me.first_name}: Admin Rights required (Check 'Post Messages' in Channels).")
        else:
            logger.error(f"❌ Reaction Error ({client.me.first_name}): {err}")

# --- HANDLERS ---

async def start_handler(client, message: Message):
    bot_username = client.me.username
    txt = f"👋 <b>{smcp('Hello')}!</b>\n\n✨ {smcp('I react to messages in Groups and Channels.')}"
    btn = InlineKeyboardMarkup([[InlineKeyboardButton(text=f"➕ {smcp('Add Me')}", url=f"https://t.me/{bot_username}?startgroup=true")]])
    await message.reply(txt, reply_markup=btn, parse_mode=enums.ParseMode.HTML)

async def start_clone(token):
    try:
        cl = Client(f"clone_{token[:10]}", api_id=API_ID, api_hash=API_HASH, bot_token=token, in_memory=True)
        
        @cl.on_message(filters.command("start") & filters.private)
        async def _start(c, m): await start_handler(c, m)

        # Reacts to ALL messages in Groups and Channels
        @cl.on_message((filters.group | filters.channel) & ~filters.service) 
        async def _react(c, m): await react_logic(c, m)

        await cl.start()
        CLONE_CLIENTS[cl.me.id] = cl
        return cl.me
    except Exception as e:
        logger.error(f"⚠️ Clone Boot Failed: {e}")
        return None

# --- MANAGER COMMANDS ---

@app.on_message((filters.group | filters.channel) & ~filters.service)
async def manager_react_watcher(client, message):
    await react_logic(client, message)

@app.on_message(filters.private & filters.command("start"))
async def manager_start(client, message):
    await start_handler(client, message)

@app.on_message(filters.command("clone"))
async def clone_cmd(client, message):
    if len(message.command) < 2: return await message.reply("Usage: `/clone [TOKEN]`")
    token = message.text.split(None, 1)[1].strip()
    msg = await message.reply("⚙️ <b>Processing...</b>")
    bot_info = await start_clone(token)
    if bot_info:
        from database import add_clone
        await add_clone(token, bot_info.id, bot_info.first_name)
        await msg.edit(f"✅ <b>{bot_info.first_name} Cloned!</b>")
    else:
        await msg.edit("❌ <b>Invalid Token</b>")

async def main():
    await app.start()
    from database import get_all_clones
    clones = await get_all_clones()
    for c in clones:
        if c.get('token'): await start_clone(c['token'])
    logger.info("🔥 SYSTEM READY")
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
