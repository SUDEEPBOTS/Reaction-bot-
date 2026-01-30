import asyncio
import random
from pyrogram import Client, filters, enums, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN

# Import DB Functions
from database import (
    add_clone, get_all_clones, set_bot_emoji, 
    get_bot_emoji, set_random_mode, is_random_on,
    remove_clone # Added remove_clone here
)

# Initialize Manager Bot
app = Client("ManagerBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
CLONE_CLIENTS = {} 

# --- SMALL CAPS FUNCTION ---
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

# --- 1. CLONE HANDLERS (DM & START) ---

# Handler for /set command in Clone DM
async def clone_msg_handler(client, message: Message):
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
            await message.reply(f"{smcp('Usage')}: `/set 🔥`")

# Handler for /start command in Clone DM (Welcome + Button)
async def clone_start_handler(client, message: Message):
    bot_name = client.me.first_name
    bot_username = client.me.username
    
    txt = (
        f"👋 <b>{smcp('Hello')}! {smcp('I am')} {bot_name}</b>\n\n"
        f"🤖 {smcp('I am a Reaction Bot.')}\n"
        f"✨ {smcp('Add me to your group and I will react to messages!')}\n\n"
        f"⚙️ <b>{smcp('Settings')}:</b>\n"
        f"👉 `/set 🔥` ({smcp('Set my reaction')})"
    )
    
    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton(text=f"➕ {smcp('Add Me To Your Group')}", url=f"https://t.me/{bot_username}?startgroup=true")]
    ])
    
    await message.reply(txt, reply_markup=btn, parse_mode=enums.ParseMode.HTML)

# --- 2. START CLONE FUNCTION ---
async def start_clone(token):
    try:
        cl = Client(f"clone_{token[:10]}", api_id=API_ID, api_hash=API_HASH, bot_token=token, in_memory=True)
        
        # Add Handler: /set
        @cl.on_message(filters.private & filters.command("set"))
        async def internal_set_handler(c, m):
            await clone_msg_handler(c, m)

        # Add Handler: /start (Welcome Message)
        @cl.on_message(filters.private & filters.command("start"))
        async def internal_start_handler(c, m):
            await clone_start_handler(c, m)

        await cl.start()
        CLONE_CLIENTS[cl.me.id] = cl
        return cl.me
    except Exception as e:
        print(f"Error starting clone: {e}")
        return None

# --- 3. MANAGER COMMANDS ---

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply(f"👋 <b>{smcp('Manager Bot is Alive')}!</b>\n\n🆔 <b>ID:</b> <code>{message.from_user.id}</code>", parse_mode=enums.ParseMode.HTML)

@app.on_message(filters.command("clone"))
async def clone_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply(f"{smcp('Usage')}: `/clone [TOKEN]`")
        
    token = message.text.split(None, 1)[1].strip()
    msg = await message.reply(f"⚙️ <b>{smcp('Cloning Bot')}...</b>", parse_mode=enums.ParseMode.HTML)
    
    bot_info = await start_clone(token)
    
    if bot_info:
        await add_clone(token, bot_info.id, bot_info.first_name)
        txt = (
            f"✅ <b>{smcp('Bot Cloned Successfully')}!</b>\n\n"
            f"🤖 <b>{smcp('Name')}:</b> {bot_info.first_name}\n"
            f"🆔 <b>ID:</b> <code>{bot_info.id}</code>\n\n"
            f"{smcp('Go to the Bot DM and type')} `/set 🔥` {smcp('to set its reaction')}."
        )
        await msg.edit(txt, parse_mode=enums.ParseMode.HTML)
    else:
        await msg.edit(f"❌ <b>{smcp('Failed to clone. Invalid Token.')}</b>", parse_mode=enums.ParseMode.HTML)

# NEW: Remove Command
@app.on_message(filters.command("remove"))
async def remove_bot_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply(f"{smcp('Usage')}: `/remove [BOT_ID]`")
    
    try:
        bot_id = int(message.text.split(None, 1)[1].strip())
    except:
        return await message.reply(f"❌ <b>{smcp('Invalid Bot ID')}!</b>", parse_mode=enums.ParseMode.HTML)

    msg = await message.reply(f"🗑 <b>{smcp('Removing Bot')}...</b>", parse_mode=enums.ParseMode.HTML)

    # 1. Stop the client if running
    if bot_id in CLONE_CLIENTS:
        try:
            await CLONE_CLIENTS[bot_id].stop()
            del CLONE_CLIENTS[bot_id]
        except Exception as e:
            print(f"Error stopping client: {e}")

    # 2. Remove from DB
    await remove_clone(bot_id)
    
    await msg.edit(f"✅ <b>{smcp('Bot Removed Successfully')}!</b>", parse_mode=enums.ParseMode.HTML)

@app.on_message(filters.command("random") & filters.group)
async def toggle_random(client, message):
    if len(message.command) < 2:
        return await message.reply(f"{smcp('Usage')}: `/random on` {smcp('or')} `/random off`")
    
    choice = message.command[1].lower()
    if choice == "on":
        await set_random_mode(message.chat.id, True)
        await message.reply(f"🎲 <b>{smcp('Random Mode')}: ON</b>\n{smcp('All bots will use different emojis now.')}", parse_mode=enums.ParseMode.HTML)
    else:
        await set_random_mode(message.chat.id, False)
        await message.reply(f"🤖 <b>{smcp('Random Mode')}: OFF</b>\n{smcp('Bots will use their personal emojis.')}", parse_mode=enums.ParseMode.HTML)

# --- 4. AUTO REACTION ---
@app.on_message(filters.channel | filters.group)
async def auto_react(client, message):
    chat_id = message.chat.id
    random_enabled = await is_random_on(chat_id)

    for bot_id, clone in CLONE_CLIENTS.items():
        try:
            if random_enabled:
                emoji = random.choice(RANDOM_EMOJIS)
            else:
                emoji = await get_bot_emoji(bot_id)
            
            await clone.send_reaction(chat_id, message.id, emoji)
            await asyncio.sleep(0.3)
        except:
            pass

# --- BOOTUP LOGIC ---
async def boot():
    print("🔄 Loading Saved Clones...")
    clones = await get_all_clones()
    count = 0
    for c in clones:
        if await start_clone(c['token']):
            count += 1
    print(f"🚀 {count} Clones Live!")

# --- MAIN ASYNC LOOP ---
async def main():
    await app.start()
    await boot()
    print("🔥 Manager Bot Live!")
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
