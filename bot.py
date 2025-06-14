import os
import asyncio
import time
from datetime import datetime
from collections import defaultdict
from telethon import TelegramClient, events, functions, types, errors

# === Load environment variables ===
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")

if not all([api_id, api_hash, bot_token]):
    print("[ERROR] Missing API_ID, API_HASH, or BOT_TOKEN environment variable.")
    exit(1)

bot = TelegramClient("bot", api_id, api_hash).start(bot_token=bot_token)

# === In-Memory Storage ===
flood_tracker = defaultdict(list)
antiflood_enabled = defaultdict(bool)
flood_punishment = defaultdict(lambda: "tmute")
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

# === /antiflood on/off ===
@bot.on(events.NewMessage(pattern=r"/antiflood (on|off)"))
@admin_only
async def toggle_antiflood(event):
    state = event.pattern_match.group(1)
    antiflood_enabled[event.chat_id] = (state == "on")
    await event.reply(f"Antiflood has been turned {state}.")

# === /setflood (mute|ban|tmute) ===
@bot.on(events.NewMessage(pattern=r"/setflood (mute|ban|tmute)"))
@admin_only
async def set_flood_punishment(event):
    method = event.pattern_match.group(1)
    flood_punishment[event.chat_id] = method
    await event.reply(f"Flood punishment set to {method}.")

# === Anti-flood Logic ===
@bot.on(events.NewMessage(incoming=True))
async def flood_control(event):
    if event.is_private or not antiflood_enabled.get(event.chat_id):
        return

    user_id = event.sender_id
    chat_id = event.chat_id
    now = time.time()
    history = flood_tracker[(chat_id, user_id)]
    history = [t for t in history if now - t < 10]
    history.append(now)
    flood_tracker[(chat_id, user_id)] = history

    if len(history) > 5:
        try:
            action = flood_punishment[chat_id]
            rights = None
            reason = ""

            if action == "mute":
                rights = types.ChatBannedRights(until_date=None, send_messages=True)
                reason = "muted"
            elif action == "ban":
                rights = types.ChatBannedRights(until_date=None, view_messages=True)
                reason = "banned"
            elif action == "tmute":
                until = int(time.time()) + 300  # 5 minutes
                rights = types.ChatBannedRights(until_date=until, send_messages=True)
                reason = "muted for 5 minutes"

            if rights:
                await bot(functions.channels.EditBannedRequest(chat_id, user_id, rights))

            async for msg in bot.iter_messages(chat_id, from_user=user_id, limit=100):
                try:
                    await msg.delete()
                except:
                    continue

            await event.respond(f"User [ID {user_id}](tg://user?id={user_id}) has been {reason} for flooding.", parse_mode='md')
            flood_tracker[(chat_id, user_id)] = []

        except errors.ChatAdminRequiredError:
            await event.respond("I don't have rights to mute or delete messages. Please make me admin with ban rights.")
        except errors.BotMethodInvalidError:
            await event.respond("Flood control failed: Method not allowed for bots. Please ensure the bot has full rights.")
        except Exception as e:
            await event.respond(f"Error during antiflood action: {str(e)}")

# === /all tag all members ===
@bot.on(events.NewMessage(pattern=r"/all"))
@admin_only
async def tag_all(event):
    mentions = []
    async for user in bot.iter_participants(event.chat_id):
        mentions.append(f"[{user.first_name}](tg://user?id={user.id})")
    batch = []
    while mentions:
        batch = mentions[:5]
        mentions = mentions[5:]
        await bot.send_message(event.chat_id, " ".join(batch), parse_mode="md")

# === /cancel clear tag ===
@bot.on(events.NewMessage(pattern=r"/cancel"))
@admin_only
async def cancel(event):
    await event.respond("Command canceled.")

# === /info command ===
@bot.on(events.NewMessage(pattern=r"/info"))
async def info(event):
    user = await event.get_sender()
    info_text = (
        f"**User Info:**\n"
        f"ID: `{user.id}`\n"
        f"Name: `{user.first_name}`\n"
        f"Username: @{user.username if user.username else 'None'}\n"
        f"Link: [Click Here](tg://user?id={user.id})"
    )
    await event.reply(info_text, parse_mode="md")

# === /purge command ===
@bot.on(events.NewMessage(pattern=r"/purge"))
async def purge(event):
    if not await is_admin(event):
        return
    reply = await event.get_reply_message()
    if not reply:
        return await event.reply("Reply to a message to start purging.")
    count = 0
    async for msg in bot.iter_messages(event.chat_id, min_id=reply.id):
        try:
            await msg.delete()
            count += 1
        except:
            continue
    await event.reply(f"Purged {count} messages.")

# === /pin and /unpin ===
@bot.on(events.NewMessage(pattern=r"/(pin|unpin)"))
@admin_only
async def pin_unpin(event):
    command = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    if not reply:
        return await event.reply("Reply to a message to pin/unpin.")
    try:
        if command == "pin":
            await bot.pin_message(event.chat_id, reply.id)
            await event.reply("Message pinned.")
        else:
            await bot.unpin_message(event.chat_id, reply.id)
            await event.reply("Message unpinned.")
    except Exception as e:
        await event.reply(f"Failed to {command} message: {str(e)}")

# === /afk ===
@bot.on(events.NewMessage(pattern=r"/afk(?: (.+))?"))
async def afk_command(event):
    reason = event.pattern_match.group(1) or "AFK"
    user = await event.get_sender()
    name = user.first_name
    AFK_USERS[user.id] = {
        "time": time.time(),
        "reason": reason.strip(),
        "name": name,
    }
    await event.reply(f"{name} is now AFK: {reason.strip()}")

# === Mention AFK Check ===
@bot.on(events.NewMessage())
async def mention_afk_checker(event):
    if event.is_private:
        return

    for entity in event.message.entities or []:
        if isinstance(entity, types.MessageEntityMention) or isinstance(entity, types.MessageEntityMentionName):
            user_id = None
            if isinstance(entity, types.MessageEntityMentionName):
                user_id = entity.user_id
            elif isinstance(entity, types.MessageEntityMention):
                username = event.raw_text[entity.offset:entity.offset + entity.length]
                if username.startswith("@"): username = username[1:]
                try:
                    user = await bot.get_entity(username)
                    user_id = user.id
                except:
                    continue

            if user_id and user_id in AFK_USERS:
                afk_data = AFK_USERS[user_id]
                name = afk_data.get("name")
                reason = afk_data.get("reason")
                since = time.time() - afk_data.get("time")
                duration = int(since)
                msg = f"{name} is AFK: {reason}\nAFK for {duration}s"
                await event.reply(msg)
                break

    if event.sender_id in AFK_USERS:
        afk_data = AFK_USERS[event.sender_id]
        name = afk_data.get("name")
        since = time.time() - afk_data.get("time")
        duration = int(since)
        del AFK_USERS[event.sender_id]
        await event.reply(f"Welcome back! {name}. You were away for {duration}s")
        
                    
                    
print("Bot is running...")
bot.run_until_disconnected()
