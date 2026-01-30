import asyncio
import random
import logging # Naya: Logging Import
from pyrogram import Client, filters, enums, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN

# Import DB Functions
from database import (
    add_clone, get_all_clones, set_bot_emoji, 
    get_bot_emoji, set_random_mode, is_random_on,
    remove_clone
)

# --- DEBUGGING SETUP (Ye Error Dikhayega) ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ReactionBot")

# Initialize Manager Bot
app = Client("ManagerBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
CLONE_CLIENTS = {} 

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

RANDOM_EMOJIS = ["👍", "❤️", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱", "🎉", "🤩", "⚡️", "🍓", "🚀", "🏆"]

# --- UNIVERSAL REACTION ENGINE (DEBUG VERSION) ---
async def universal_reaction_logic(client, message):
    try:
        chat_id = message.chat.id
        msg_id = message.id
        bot_id = client.me.id
        
        # Log 1: Message Detection
        # logger.info(f"Bot {bot_id} saw message {msg_id} in Chat {chat_id}")

        # Check Random Mode
        if await is_random_on(chat_id):
            emoji = random.choice(RANDOM_EMOJIS)
        else:
            emoji = await get_bot_emoji(bot_id)
            
        # Log 2: Attempting Reaction
        # logger.info(f"Bot {bot_id} attempting reaction {emoji} on msg {msg_id}")

        await client.send_reaction(chat_id, msg_id, emoji)
        
        # Log 3: Success
        logger.info(f"✅ Success: Bot {client.me.first_name} reacted {emoji} in {message.chat.title}")

    except Exception as e:
        # Log 4: ERROR REVEALED
        logger.error(f"❌ REACTION FAILED for Bot {client.me.first_name}: {e}")

# --- HANDLERS ---

async def set_emoji_handler(client, message: Message):
    if message.text and message.text.startswith("/set"):
        try:
            if " " in message.text:
                emoji = message.text.split(None, 1)[1].strip()
            else:
                emoji = message.text.replace("/set", "").strip()
            
            if not emoji:
                await message.reply(f"{smcp('Usage')}: `/set 🔥`")
                return

            await set_bot_emoji(client.me.id, emoji)
            await message.reply(f"✅ <b>{smcp('Personal Emoji Updated')}:</b> {emoji}", parse_mode=enums.ParseMode.HTML)
        except Exception as e:
            logger.error(f"Set Emoji Error: {e}")
            await message.reply(f"{smcp('Usage')}: `/set 🔥`")

async def start_handler(client, message: Message):
    bot_name = client.me.first_name
    bot_username = client.me.username
    txt = (
        f"👋 <b>{smcp('Hello')}! {smcp('I am')} {bot_name}</b>\n\n"
        f"🤖 {smcp('I am a Reaction Bot.')}\n"
        f"✨ {smcp('Add me to your group/channel as Admin!')}\n\n"
        f"⚙️ <b>{smcp('Settings')}:</b>\n"
        f"👉 `/set 🔥` ({smcp('Set my reaction')})"
    )
    btn = InlineKeyboardMarkup([[InlineKeyboardButton(text=f"➕ {smcp('Add Me To Your Group')}", url=f"https://t.me/{bot_username}?startgroup=true")]])
    await message.reply(txt, reply_markup=btn, parse_mode=enums.ParseMode.HTML)

# --- START CLONE FUNCTION ---
async def start_clone(token):
    try:
        cl = Client(f"clone_{token[:10]}", api_id=API_ID, api_hash=API_HASH, bot_token=token, in_memory=True)
        
        @cl.on_message(filters.private & filters.command("set"))
        async def _set(c, m): await set_emoji_handler(c, m)

        @cl.on_message(filters.private & filters.command("start"))
        async def _start(c, m): await start_handler(c, m)

        # Clone Watcher
        @cl.on_message(filters.channel | filters.group)
        async def _react(c, m): await universal_reaction_logic(c, m)

        await cl.start()
        CLONE_CLIENTS[cl.me.id] = cl
        logger.info(f"Clone Started: {cl.me.first_name}")
        return cl.me
    except Exception as e:
        logger.error(f"Clone Start Error: {e}")
        return None

# --- MANAGER COMMANDS ---

@app.on_message(filters.private & filters.command("start"))
async def manager_start(client, message): await start_handler(client, message)

@app.on_message(filters.private & filters.command("set"))
async def manager_set(client, message): await set_emoji_handler(client, message)

@app.on_message(filters.command("clone"))
async def clone_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply(f"{smcp('Usage')}: `/clone [TOKEN]`")
    token = message.text.split(None, 1)[1].strip()
    msg = await message.reply(f"⚙️ <b>{smcp('Cloning Bot')}...</b>", parse_mode=enums.ParseMode.HTML)
    
    bot_info = await start_clone(token)
    
    if bot_info:
        await add_clone(token, bot_info.id, bot_info.first_name)
        txt = (f"✅ <b>{smcp('Bot Cloned Successfully')}!</b>\n\n🤖 <b>{smcp('Name')}:</b> {bot_info.first_name}\n🆔 <b>ID:</b> <code>{bot_info.id}</code>\n\n{smcp('Go to the Bot DM and type')} `/set 🔥`.")
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

@app.on_message(filters.command("random") & filters.group)
async def toggle_random(client, message):
    choice = message.command[1].lower() if len(message.command) > 1 else ""
    if choice == "on":
        await set_random_mode(message.chat.id, True)
        await message.reply(f"🎲 <b>{smcp('Random Mode')}: ON</b>", parse_mode=enums.ParseMode.HTML)
    else:
        await set_random_mode(message.chat.id, False)
        await message.reply(f"🤖 <b>{smcp('Random Mode')}: OFF</b>", parse_mode=enums.ParseMode.HTML)

# --- MANAGER WATCHER ---
@app.on_message(filters.channel | filters.group)
async def manager_auto_react(client, message):
    await universal_reaction_logic(client, message)

# --- MAIN ---
async def boot():
    logger.info("🔄 Loading Saved Clones...")
    clones = await get_all_clones()
    count = 0
    for c in clones:
        if await start_clone(c['token']):
            count += 1
    logger.info(f"🚀 {count} Clones Live!")

async def main():
    await app.start()
    await boot()
    logger.info("🔥 Manager Bot Live!")
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
