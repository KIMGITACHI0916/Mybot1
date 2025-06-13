import os
import asyncio
import time
from datetime import datetime
from collections import defaultdict
from telethon import TelegramClient, events, functions, types

# === Load environment variables ===
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")

if not all([api_id, api_hash, bot_token]):
    print("[ERROR] Missing API_ID, API_HASH, or BOT_TOKEN environment variable.")
    exit(1)

api_id = int(api_id)

# === Start Telegram Bot ===
bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# === In-Memory Storage ===
flood_tracker = defaultdict(list)
temp_bans = {}
temp_mutes = {}
tagall_running = {}
antiflood_enabled = {}
flood_punishment = {}
AFK_USERS = defaultdict(dict)

# === Utility: Check Admin ===
async def is_admin(event):
    try:
        perms = await bot.get_permissions(event.chat_id, event.sender_id)
        return perms.is_admin
    except:
        return False

# === Admin Only Command Decorator ===
def admin_only(func):
    async def wrapper(event):
        if not await is_admin(event):
            return await event.reply("You need to be an admin to use this command.")
        return await func(event)
    return wrapper

# === /start ===
@bot.on(events.NewMessage(pattern=r"/start"))
async def start_cmd(event):
    await event.reply("Bot is online!")

# === /afk ===
@bot.on(events.NewMessage(pattern=r"/afk(?:\s+(.*))?"))
async def set_afk(event):
    user_id = event.sender_id
    reason = event.pattern_match.group(1) or ""
    AFK_USERS[user_id] = {
        "reason": reason,
        "since": datetime.now(),
        "is_afk": True
    }
    sender = await event.get_sender()
    name = sender.first_name or "User"
    await event.reply(f"{name} is now AFK: {reason}")

@bot.on(events.NewMessage(incoming=True))
async def check_afk(event):
    sender_id = event.sender_id
    if sender_id in AFK_USERS and AFK_USERS[sender_id].get("is_afk"):
        if not event.raw_text.strip().lower().startswith("/afk"):
            AFK_USERS[sender_id]["is_afk"] = False
            sender = await event.get_sender()
            name = sender.first_name or "User"
            await event.reply(f"Welcome back, {name}!")

    if event.is_reply:
        replied_msg = await event.get_reply_message()
        if replied_msg:
            replied_user = replied_msg.sender_id
            afk_data = AFK_USERS.get(replied_user, {})
            if afk_data.get("is_afk"):
                user = await replied_msg.get_sender()
                name = user.first_name or "User"
                reason = afk_data.get("reason", "AFK")
                await event.reply(f"{name} is AFK: {reason}")

    elif event.message.mentioned:
        for entity in event.message.entities or []:
            if hasattr(entity, 'user_id'):
                uid = entity.user_id
                afk_data = AFK_USERS.get(uid, {})
                if afk_data.get("is_afk"):
                    user = await bot.get_entity(uid)
                    name = user.first_name or "User"
                    reason = afk_data.get("reason", "AFK")
                    await event.reply(f"{name} is AFK: {reason}")

# === Moderation: ban, mute, kick, unban, unmute ===
async def ban_user(event, user_id, rights):
    await bot(functions.channels.EditBannedRequest(event.chat_id, user_id, rights))

@bot.on(events.NewMessage(pattern=r"/(ban|mute|kick|unban|unmute)"))
@admin_only
async def mod_cmd(event):
    if not event.is_reply:
        return await event.reply("Reply to a user to execute command.")

    cmd = event.pattern_match.group(1)
    user = await event.get_reply_message().get_sender()
    uid = user.id

    if cmd == "ban":
        rights = types.ChatBannedRights(view_messages=True)
    elif cmd == "mute":
        rights = types.ChatBannedRights(send_messages=True)
    elif cmd == "kick":
        rights = types.ChatBannedRights(view_messages=True)
        await ban_user(event, uid, rights)
        await asyncio.sleep(1)
        rights = types.ChatBannedRights()
    elif cmd in ["unban", "unmute"]:
        rights = types.ChatBannedRights()
    else:
        return

    await ban_user(event, uid, rights)
    await event.reply(f"User {cmd}ed.")

# === /tban and /tmute ===
@bot.on(events.NewMessage(pattern=r"/(tban|tmute) (\d+)([smhd])"))
@admin_only
async def temp_mod_cmd(event):
    if not event.is_reply:
        return await event.reply("Reply to a user to use temporary moderation.")

    cmd = event.pattern_match.group(1)
    time_val = int(event.pattern_match.group(2))
    unit = event.pattern_match.group(3)
    units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    seconds = time_val * units[unit]
    user_msg = await event.get_reply_message()
    user = await user_msg.get_sender()

    if cmd == "tban":
        rights = types.ChatBannedRights(until_date=int(time.time()) + seconds, view_messages=True)
    else:
        rights = types.ChatBannedRights(until_date=int(time.time()) + seconds, send_messages=True)

    await ban_user(event, user.id, rights)

    # Delete all messages from user in last 100 messages
    async for msg in bot.iter_messages(event.chat_id, limit=100):
        if msg.sender_id == user.id:
            try:
                await bot.delete_messages(event.chat_id, msg.id)
            except:
                pass

    await event.reply(f"User {cmd}d for {time_val}{unit} and messages deleted.")

# === Anti-flood ===
@bot.on(events.NewMessage(pattern=r"/antiflood (on|off)"))
@admin_only
async def toggle_antiflood(event):
    state = event.pattern_match.group(1)
    antiflood_enabled[event.chat_id] = (state == "on")
    await event.reply(f"Antiflood has been turned {state}.")

@bot.on(events.NewMessage(pattern=r"/setflood (mute|ban)"))
@admin_only
async def set_flood_punishment(event):
    method = event.pattern_match.group(1)
    flood_punishment[event.chat_id] = method
    await event.reply(f"Flood punishment set to {method}.")

@bot.on(events.NewMessage(incoming=True))
async def flood_control(event):
    if event.is_private or not antiflood_enabled.get(event.chat_id):
        return
    user_id = event.sender_id
    now = time.time()
    chat_user_key = (event.chat_id, user_id)
    history = flood_tracker[chat_user_key]
    history = [t for t in history if now - t < 10]
    history.append(now)
    flood_tracker[chat_user_key] = history

    if len(history) > 5:
        # Always apply tmute 5m
        mute_rights = types.ChatBannedRights(until_date=int(time.time()) + 300, send_messages=True)
        try:
            await ban_user(event, user_id, mute_rights)
            async for msg in bot.iter_messages(event.chat_id, limit=100):
                if msg.sender_id == user_id:
                    try:
                        await bot.delete_messages(event.chat_id, msg.id)
                    except:
                        pass
            await event.respond(f"User [{user_id}](tg://user?id={user_id}) has been muted for 5m for flooding.", parse_mode='md')
            flood_tracker[chat_user_key] = []
        except:
            await event.respond("I don't have enough rights to mute for flood.")

# === /info ===
@bot.on(events.NewMessage(pattern=r"/info"))
async def info_cmd(event):
    replied_user = (await event.get_reply_message()).sender if event.is_reply else event.sender
    user_link = f"tg://user?id={replied_user.id}"
    msg = (
        f"<b>User info:</b>\n"
        f"<b>ID:</b> <code>{replied_user.id}</code>\n"
        f"<b>First Name:</b> {replied_user.first_name}\n"
        f"<b>Username:</b> @{replied_user.username if replied_user.username else 'N/A'}\n"
        f"<b>User link:</b> <a href=\"{user_link}\">link</a>"
    )
    await event.reply(msg, parse_mode='html')

# === /purge ===
@bot.on(events.NewMessage(pattern=r"/purge"))
@admin_only
async def purge_cmd(event):
    if not event.is_reply:
        return await event.reply("Reply to a message to start purging from there.")
    start_msg = await event.get_reply_message()
    end_msg_id = event.id
    for msg_id in range(start_msg.id, end_msg_id):
        try:
            await bot.delete_messages(event.chat_id, msg_id)
        except:
            continue
    await event.reply("Messages purged.")

# === /pin ===
@bot.on(events.NewMessage(pattern=r"/pin"))
@admin_only
async def pin_cmd(event):
    if event.is_reply:
        await bot.pin_message(event.chat_id, event.reply_to_msg_id)
        await event.reply("Message pinned.")

# === /unpin ===
@bot.on(events.NewMessage(pattern=r"/unpin"))
@admin_only
async def unpin_cmd(event):
    await bot.unpin_message(event.chat_id)
    await event.reply("Message unpinned.")

# === /cancel ===
@bot.on(events.NewMessage(pattern=r"/cancel"))
@admin_only
async def cancel_cmd(event):
    tagall_running[event.chat_id] = False
    await event.reply("Tagging cancelled.")

# === /all ===
@bot.on(events.NewMessage(pattern=r"/all"))
@admin_only
async def tag_all_cmd(event):
    if not (await bot.get_permissions(event.chat_id, 'me')).is_admin:
        return await event.reply("I don't have permission to tag everyone.")
    tagall_running[event.chat_id] = True
    async for user in bot.iter_participants(event.chat_id):
        if not tagall_running.get(event.chat_id):
            break
        if user.bot or user.deleted:
            continue
        try:
            await event.respond(f"[{user.first_name}](tg://user?id={user.id})", link_preview=False)
            await asyncio.sleep(1)
        except:
            continue
    await event.reply("Tagging finished.")

print("Bot started")
bot.run_until_disconnected()
    
