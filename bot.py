import os
import asyncio
import time
import logging
from telethon import Button
from datetime import datetime
from collections import defaultdict
from telethon import TelegramClient, events, functions, types, errors
from telethon.tl.types import PeerChannel, PeerChat

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Load environment variables ===
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")

# Telethon client setup
bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

if not all([api_id, api_hash, bot_token]):
    print("[ERROR] Missing API_ID, API_HASH, or BOT_TOKEN environment variable.")
    exit(1)

bot = TelegramClient("bot", api_id, api_hash).start(bot_token=bot_token)

# === In-Memory Storage ===
flood_tracker = defaultdict(list)
antiflood_enabled = defaultdict(bool)
flood_punishment = defaultdict(lambda: "tmute")
AFK_USERS = defaultdict(dict)
OWNER_ID = int(os.getenv("OWNER_ID"))
started_users = set()
bot_groups = set()

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


# ==help==
@bot.on(events.NewMessage(pattern=r"/help"))
async def help_command(event):
    help_text = "**🤖 Bot Help Menu**\n\nSelect a category below to see available commands."

    buttons = [
        [Button.inline("📌 Basic Commands", data=b"help_basic")],
        [Button.inline("🛡 Admin Tools", data=b"help_admin")],
        [Button.inline("👤 User Tools", data=b"help_user")],
    ]

    await event.respond(help_text, buttons=buttons)


@bot.on(events.CallbackQuery(data=b"help_basic"))
async def show_basic(event):
    await event.edit(
        "**📌 Basic Commands**\n\n"
        "**/start** – Check if the bot is active.\n"
        "**/info** – Get user information.\n"
        "**/help** – Show this help message.\n"
        "**/all** – Mention/tag all group members.\n",
        buttons=[Button.inline("⬅️ Back", data=b"help_back")]
    )

@bot.on(events.CallbackQuery(data=b"help_admin"))
async def show_admin(event):
    await event.edit(
        "**🛡 Admin Tools**\n\n"
        "**/ban** – Ban a user from the group.\n"
        "**/unban** – Unban a previously banned user.\n"
        "**/mute** – Mute a user in the group.\n"
        "**/unmute** – Unmute a muted user.\n"
        "**/kick** – Kick a user from the group.\n"
        "**/tban** – Temporarily ban a user.\n"
        "**/tmute** – Temporarily mute a user.\n"
        "**/sban** – Silently ban (no message shown).\n"
        "**/smute** – Silently mute (no message shown).\n"
        "**/skick** – Silently kick (no message shown).\n",
        buttons=[Button.inline("⬅️ Back", data=b"help_back")]
    )

@bot.on(events.CallbackQuery(data=b"help_user"))
async def show_user(event):
    await event.edit(
        "**👤 User Tools**\n\n"
        "**/afk** – Set AFK status with optional reason.\n"
        "**/cancel** – Cancel ongoing tagall.\n"
        "**/purge** – Delete messages in bulk.\n"
        "**/pin** – Pin a message.\n"
        "**/unpin** – Unpin a message.\n",
        buttons=[Button.inline("⬅️ Back", data=b"help_back")]
    )

@bot.on(events.CallbackQuery(data=b"help_back"))
async def show_main_help(event):
    await help_command(event)

    
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
    
# === /purge ===
@bot.on(events.NewMessage(pattern=r"/purge"))
async def purge(event):
    if not await is_admin(event):
        return await event.reply("❗ You need to be an admin to use this command.")

    reply = await event.get_reply_message()
    if not reply:
        return await event.reply("❗ Reply to a message to start purging.")

    deleted = 0
    try:
        async for msg in bot.iter_messages(event.chat_id, offset_id=event.id):
            if msg.id <= reply.id:
                break
            try:
                await msg.delete()
                deleted += 1
            except:
                continue
        await reply.delete()
        await event.delete()
        confirm = await bot.send_message(event.chat_id, f"✅ Purged {deleted + 2} messages.")
        await asyncio.sleep(3)
        await confirm.delete()
    except Exception as e:
        await event.reply(f"⚠️ Error during purge: {e}")

# === /spurge (silent purge) ===
@bot.on(events.NewMessage(pattern=r"/spurge"))
async def spurge(event):
    if not await is_admin(event):
        return

    reply = await event.get_reply_message()
    if not reply:
        return await event.reply("❗ Reply to a message to start purging.")

    try:
        async for msg in bot.iter_messages(event.chat_id, offset_id=event.id):
            if msg.id <= reply.id:
                break
            try:
                await msg.delete()
            except:
                continue
        await reply.delete()
        await event.delete()
    except:
        pass

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

#afk
@bot.on(events.NewMessage(pattern=r"/afk(?: (.+))?"))
async def afk_command(event):
    reason = event.pattern_match.group(1) or ""
    user = await event.get_sender()
    name = user.first_name
    AFK_USERS[user.id] = {
        "time": time.time(),
        "reason": reason.strip(),
        "name": name,
    }
    await event.reply(f"{name} is now AFK: {reason.strip()}")

@bot.on(events.NewMessage())
async def mention_afk_checker(event):
    if event.is_private:
        return

    if event.raw_text.startswith("/afk"):
        return

    def format_duration(seconds):
        h, rem = divmod(int(seconds), 3600)
        m, s = divmod(rem, 60)
        parts = []
        if h: parts.append(f"{h}h")
        if m: parts.append(f"{m}m")
        if s or not parts: parts.append(f"{s}s")
        return ' '.join(parts)

    # Check AFK in mentions
    for entity in event.message.entities or []:
        if isinstance(entity, (types.MessageEntityMention, types.MessageEntityMentionName)):
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

            if user_id and "time" in AFK_USERS[user_id]:
                afk_data = AFK_USERS[user_id]
                name = afk_data.get("name")
                reason = afk_data.get("reason")
                since = time.time() - afk_data.get("time")
                duration = format_duration(since)
                msg = f"{name} is AFK: {reason}\nAFK for {duration}"
                await event.reply(msg)
                break

    # Check if reply target is AFK
    if event.is_reply:
        reply_msg = await event.get_reply_message()
        if "time" in AFK_USERS[reply_msg.sender_id]:
            afk_data = AFK_USERS[reply_msg.sender_id]
            name = afk_data.get("name")
            reason = afk_data.get("reason")
            since = time.time() - afk_data.get("time")
            duration = format_duration(since)
            msg = f"{name} is AFK: {reason}\nAFK for {duration}"
            await event.reply(msg)

    # Remove AFK if sender was AFK
    if "time" in AFK_USERS[event.sender_id]:
        afk_data = AFK_USERS[event.sender_id]
        name = afk_data.get("name")
        since = time.time() - afk_data.get("time")
        duration = format_duration(since)
        del AFK_USERS[event.sender_id]
        await event.reply(f"Welcome back, {name}! You were away for {duration}.")


# /all or utag handler
@bot.on(events.NewMessage(pattern=r'(/all|utag)(\s+.*)?'))
async def tag_all_handler(event):
    chat = await event.get_chat()
    if not isinstance(chat, (PeerChannel, PeerChat)) and not getattr(chat, 'megagroup', False):
        await event.respond("This command can only be used in groups!")
        return

    if event.sender_id not in started_users:
        await event.respond("Please start the bot by sending /start in private chat first!")
        return

    command = event.pattern_match.group(1)
    extra_text = event.pattern_match.group(2)
    extra_text = extra_text.strip() if extra_text else ""

    try:
        participants = await bot.get_participants(chat)
    except Exception as e:
        logger.error(f"Error getting participants: {e}")
        await event.respond("Failed to get group members. Make sure I have the right permissions!")
        return

    valid_participants = [user for user in participants if not user.bot and user.id != event.sender_id]
    chunk_size = 5
    user_chunks = [valid_participants[i:i + chunk_size] for i in range(0, len(valid_participants), chunk_size)]

    reply_to_msg_id = None
    if event.reply_to:
        replied_msg = await event.get_reply_message()
        reply_to_msg_id = replied_msg.id

    if extra_text and user_chunks:
        msg = await bot.send_message(chat.id, extra_text, reply_to=reply_to_msg_id)
        reply_to_msg_id = msg.id

    for chunk in user_chunks:
        tag_text = ""
        for user in chunk:
            first_name = user.first_name or "User"
            mention = f"[{first_name}](tg://user?id={user.id})"
            tag_text += f"🔹{mention}\n"
        await bot.send_message(chat.id, tag_text, reply_to=reply_to_msg_id, parse_mode='markdown')
        await asyncio.sleep(2)

    if chat.id not in bot_groups:
        bot_groups.add(chat.id)

# /broadcast handler
@bot.on(events.NewMessage(pattern=r'/broadcast(\s+.+)?'))
async def broadcast_handler(event):
    sender = await event.get_sender()
    if sender.id not in admin_users:
        await event.respond("You don't have permission to use this command!")
        return

    broadcast_text = event.pattern_match.group(1)
    if not broadcast_text:
        await event.respond("Please provide a message to broadcast!\nUsage: /broadcast [message]")
        return
    broadcast_text = broadcast_text.strip()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    footer = f"\n\n🔄 Broadcast by Admin on {timestamp}"
    full_message = f"{broadcast_text}{footer}"
    sent_count = 0
    total_targets = len(started_users) + len(bot_groups)
    status_msg = await event.respond(f"🔄 Broadcasting message to {total_targets} targets...")

    for user_id in started_users:
        try:
            await bot.send_message(user_id, full_message)
            sent_count += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Failed to send to user {user_id}: {e}")

    for group_id in bot_groups:
        try:
            await bot.send_message(group_id, full_message)
            sent_count += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Failed to send to group {group_id}: {e}")

    await bot.edit_message(status_msg.chat_id, status_msg.id,
                           f"✅ Broadcast completed! Message sent to {sent_count}/{total_targets} targets.")

# Bot added to group handler
@bot.on(events.ChatAction)
async def chat_action_handler(event):
    if event.user_added and bot.uid in event.user_ids:
        chat = await event.get_chat()
        bot_groups.add(chat.id)
        await event.respond("👋 Hello everyone! I'm User Tagger Bot.\n\n"
                            "To use me, first send me a /start command in private chat.\n"
                            "Then you can use /all or utag commands to tag all users in this group!")

# Main function
async def main():
    bot_info = await bot.get_me()
    bot.uid = bot_info.id
    print(f"Bot @{bot_info.username} started successfully!")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
    
print("Bot is running...")
bot.run_until_disconnected()
