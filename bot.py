import os
import asyncio
import time
from telethon import Button
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
OWNER_ID = int(os.getenv("OWNER_ID"))
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

# === /all tag all members ===

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Handle the /start command"""
    user_id = event.sender_id
    started_users.add(user_id)
    
    await event.respond("👋 Welcome to the User Tagger Bot!\n\n"
                       "📌 Commands:\n"
                       "• /all [text] - Tag all users in the group\n"
                       "• utag [text] - Tag all users in the group\n"
                       "• /broadcast [message] - Send message to all users and groups (admin only)\n\n"
                       "Reply to a message with /all or utag to tag users while referencing that message.")

@bot.on(events.NewMessage(pattern=r'(/all|utag)(\s+.*)?'))
async def tag_all_handler(event):
    """Handle the /all or utag command to tag all users"""
    chat = await event.get_chat()
    
    # Check if this is a group
    if not isinstance(chat, (PeerChannel, PeerChat)) and not hasattr(chat, 'megagroup') and not getattr(chat, 'broadcast', False):
        await event.respond("This command can only be used in groups!")
        return
    
    # Check if user has started the bot
    if event.sender_id not in started_users:
        await event.respond("Please start the bot by sending /start in private chat first!")
        return
    
    # Get optional text after the command
    command = event.pattern_match.group(1)
    extra_text = event.pattern_match.group(2)
    
    if extra_text:
        extra_text = extra_text.strip()
    else:
        extra_text = ""
    
    # Get all participants in the chat
    try:
        participants = await bot.get_participants(chat)
    except Exception as e:
        logger.error(f"Error getting participants: {e}")
        await event.respond("Failed to get group members. Make sure I have the right permissions!")
        return
    
    # Filter out bots and the sender
    valid_participants = [user for user in participants if not user.bot and user.id != event.sender_id]
    
    # Create chunks of users to tag (5 users per message)
    chunk_size = 5
    user_chunks = [valid_participants[i:i + chunk_size] for i in range(0, len(valid_participants), chunk_size)]
    
    # Handle reply to a message
    if event.reply_to:
        replied_msg = await event.get_reply_message()
        reply_to_msg_id = replied_msg.id
    else:
        reply_to_msg_id = None
    
    # Send the extra text if provided
    if extra_text and user_chunks:
        await bot.send_message(
            entity=chat.id,
            message=extra_text,
            reply_to=reply_to_msg_id
        )
        # For subsequent tag messages, we'll reply to our own message
        if reply_to_msg_id:
            last_msg = await bot.get_messages(chat.id, ids=1)
            if last_msg:
                reply_to_msg_id = last_msg[0].id
    
    # Send tags in chunks with the specified format
    for chunk in user_chunks:
        tag_text = ""
        for user in chunk:
            first_name = user.first_name or "User"  # Fallback if first_name is None
            mention = f"[{first_name}](tg://user?id={user.id})"
            tag_text += f"🔹{mention}\n"
        
        if tag_text:
            await bot.send_message(
                entity=chat.id,
                message=tag_text,
                reply_to=reply_to_msg_id,
                parse_mode='markdown'
            )
            await asyncio.sleep(2)  # Avoid flood limits
    
    # Add group to known groups
    if chat.id not in bot_groups:
        bot_groups.add(chat.id)

@bot.on(events.NewMessage(pattern=r'/broadcast(\s+.+)?'))
async def broadcast_handler(event):
    """Handle the /broadcast command to send a message to all users and groups"""
    sender = await event.get_sender()
    
    # Check if the user is an admin
    if sender.id not in admin_users:
        await event.respond("You don't have permission to use this command!")
        return
    
    # Get the message to broadcast
    broadcast_text = event.pattern_match.group(1)
    if not broadcast_text:
        await event.respond("Please provide a message to broadcast!\nUsage: /broadcast [message]")
        return
    
    broadcast_text = broadcast_text.strip()
    
    # Add a timestamp and sender info to the broadcast
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    footer = f"\n\n🔄 Broadcast by Admin on {timestamp}"
    full_message = f"{broadcast_text}{footer}"
    
    # Counter for successful sends
    sent_count = 0
    total_targets = len(started_users) + len(bot_groups)
    
    status_msg = await event.respond(f"🔄 Broadcasting message to {total_targets} targets...")
    
    # Send to all users who started the bot
    for user_id in started_users:
        try:
            await bot.send_message(user_id, full_message)
            sent_count += 1
            await asyncio.sleep(0.5)  # Avoid flood limits
        except Exception as e:
            logger.error(f"Failed to send broadcast to user {user_id}: {e}")
    
    # Send to all groups
    for group_id in bot_groups:
        try:
            await bot.send_message(group_id, full_message)
            sent_count += 1
            await asyncio.sleep(0.5)  # Avoid flood limits
        except Exception as e:
            logger.error(f"Failed to send broadcast to group {group_id}: {e}")
    
    await bot.edit_message(entity=status_msg.chat_id, message=status_msg.id, 
                         text=f"✅ Broadcast completed! Message sent to {sent_count}/{total_targets} targets.")

@bot.on(events.ChatAction)
async def chat_action_handler(event):
    """Track when the bot is added to groups"""
    if event.user_added and bot.uid in event.user_ids:
        # Bot was added to a group
        chat = await event.get_chat()
        bot_groups.add(chat.id)
        
        await event.respond("👋 Hello everyone! I'm User Tagger Bot.\n\n"
                           "To use me, first send me a /start command in private chat.\n"
                           "Then you can use /all or utag commands to tag all users in this group!")

async def main():
    # Start the bot
    await bot.start(bot_token=BOT_TOKEN)
    
    # Get the bot entity to find its ID
    bot_info = await bot.get_me()
    bot.uid = bot_info.id
    
    print(f"Bot @{bot_info.username} started successfully!")
    
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


print("Bot is running...")
bot.run_until_disconnected()
