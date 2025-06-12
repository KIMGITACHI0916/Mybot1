from telethon import TelegramClient, events, functions, types
import asyncio
import time
import os

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")

bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# === In-Memory Storage ===
flood_tracker = {}
temp_bans = {}
temp_mutes = {}
tagall_running = {}

# === Utility: Check Admin ===
async def is_admin(event):
    try:
        perms = await bot.get_permissions(event.chat_id, event.sender_id)
        return perms.is_admin
    except:
        return False

# === /start ===
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply("Bot is online!")

# === /ban ===
@bot.on(events.NewMessage(pattern='/ban'))
async def ban(event):
    if not await is_admin(event):
        return await event.reply("You need to be an admin to use this command.")
    if not (await event.client.get_permissions(event.chat_id, 'me')).is_admin:
        return await event.reply("I don't have admin rights to perform this action.")
    if event.is_reply:
        user = await event.get_reply_message().get_sender()
        await bot(functions.channels.EditBannedRequest(
            event.chat_id,
            user.id,
            types.ChatBannedRights(view_messages=True)
        ))
        await event.reply("User banned.")

# === /unban ===
@bot.on(events.NewMessage(pattern='/unban'))
async def unban(event):
    if not await is_admin(event):
        return await event.reply("You need to be an admin to use this command.")
    if not (await event.client.get_permissions(event.chat_id, 'me')).is_admin:
        return await event.reply("I don't have admin rights to perform this action.")
    if event.is_reply:
        user = await event.get_reply_message().get_sender()
        await bot(functions.channels.EditBannedRequest(
            event.chat_id,
            user.id,
            types.ChatBannedRights()
        ))
        await event.reply("User unbanned.")

# === /untban (alias for unban) ===
@bot.on(events.NewMessage(pattern='/untban'))
async def untban(event):
    await unban(event)

# === /mute ===
@bot.on(events.NewMessage(pattern='/mute'))
async def mute(event):
    if not await is_admin(event):
        return await event.reply("You need to be an admin to use this command.")
    if not (await event.client.get_permissions(event.chat_id, 'me')).is_admin:
        return await event.reply("I don't have admin rights to perform this action.")
    if event.is_reply:
        user = await event.get_reply_message().get_sender()
        await bot(functions.channels.EditBannedRequest(
            event.chat_id,
            user.id,
            types.ChatBannedRights(send_messages=True)
        ))
        await event.reply("User muted.")

# === /unmute ===
@bot.on(events.NewMessage(pattern='/unmute'))
async def unmute(event):
    if not await is_admin(event):
        return await event.reply("You need to be an admin to use this command.")
    if not (await event.client.get_permissions(event.chat_id, 'me')).is_admin:
        return await event.reply("I don't have admin rights to perform this action.")
    if event.is_reply:
        user = await event.get_reply_message().get_sender()
        await bot(functions.channels.EditBannedRequest(
            event.chat_id,
            user.id,
            types.ChatBannedRights()
        ))
        await event.reply("User unmuted.")

# === /untmute (alias for unmute) ===
@bot.on(events.NewMessage(pattern='/untmute'))
async def untmute(event):
    await unmute(event)

# === /kick ===
@bot.on(events.NewMessage(pattern='/kick'))
async def kick(event):
    if not await is_admin(event):
        return await event.reply("You need to be an admin to use this command.")
    if not (await event.client.get_permissions(event.chat_id, 'me')).is_admin:
        return await event.reply("I don't have admin rights to perform this action.")
    if event.is_reply:
        user = await event.get_reply_message().get_sender()
        await bot(functions.channels.EditBannedRequest(
            event.chat_id,
            user.id,
            types.ChatBannedRights(view_messages=True)
        ))
        await asyncio.sleep(1)
        await bot(functions.channels.EditBannedRequest(
            event.chat_id,
            user.id,
            types.ChatBannedRights()
        ))
        await event.reply("User kicked.")

# === /tmute ===
@bot.on(events.NewMessage(pattern=r"/tmute (\d+)([smhd])"))
async def tmute(event):
    if not await is_admin(event):
        return await event.reply("You need to be an admin to use this command.")
    if not (await event.client.get_permissions(event.chat_id, 'me')).is_admin:
        return await event.reply("I don't have admin rights to perform this action.")
    if event.is_reply:
        time_val = int(event.pattern_match.group(1))
        unit = event.pattern_match.group(2)
        units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        seconds = time_val * units[unit]
        user = await event.get_reply_message().get_sender()
        temp_mutes[user.id] = time.time() + seconds
        await bot(functions.channels.EditBannedRequest(
            event.chat_id,
            user.id,
            types.ChatBannedRights(until_date=time.time() + seconds, send_messages=True)
        ))
        await event.reply(f"Muted for {time_val}{unit}")

# === /tban ===
@bot.on(events.NewMessage(pattern=r"/tban (\d+)([smhd])"))
async def tban(event):
    if not await is_admin(event):
        return await event.reply("You need to be an admin to use this command.")
    if not (await event.client.get_permissions(event.chat_id, 'me')).is_admin:
        return await event.reply("I don't have admin rights to perform this action.")
    if event.is_reply:
        time_val = int(event.pattern_match.group(1))
        unit = event.pattern_match.group(2)
        units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        seconds = time_val * units[unit]
        user = await event.get_reply_message().get_sender()
        temp_bans[user.id] = time.time() + seconds
        await bot(functions.channels.EditBannedRequest(
            event.chat_id,
            user.id,
            types.ChatBannedRights(until_date=time.time() + seconds, view_messages=True)
        ))
        await event.reply(f"Banned for {time_val}{unit}")

# === /cancel ===
@bot.on(events.NewMessage(pattern='/cancel'))
async def cancel(event):
    if not await is_admin(event):
        return await event.reply("You need to be an admin to use this command.")
    tagall_running[event.chat_id] = False
    await event.reply("Tagging cancelled.")

# === Anti-flood ===
@bot.on(events.NewMessage())
async def flood_control(event):
    if event.is_private:
        return
    user_id = event.sender_id
    now = time.time()
    history = flood_tracker.get(user_id, [])
    history = [msg for msg in history if now - msg < 10]
    history.append(now)
    flood_tracker[user_id] = history
    if len(history) > 5:
        await event.respond("Stop spamming or you may be muted!")

# === /info ===
@bot.on(events.NewMessage(pattern='/info'))
async def user_info(event):
    if event.is_reply:
        user = await event.get_reply_message().get_sender()
    else:
        user = await event.get_sender()
    name = user.first_name or "None"
    username = f"@{user.username}" if user.username else "None"
    link = f"tg://user?id={user.id}"
    msg = f"User info:\nID: [{user.id}](tg://user?id={user.id})\nFirst Name: {name}\nUsername: {username}\nUser link: [Click here]({link})"
    await event.reply(msg, link_preview=False)

# === /pin ===
@bot.on(events.NewMessage(pattern='/pin'))
async def pin_msg(event):
    if not await is_admin(event):
        return await event.reply("You need to be an admin to use this command.")
    if not (await event.client.get_permissions(event.chat_id, 'me')).is_admin:
        return await event.reply("I don't have admin rights to pin messages.")
    if event.is_reply:
        await bot.pin_message(event.chat_id, event.reply_to_msg_id)
        await event.reply("Message pinned.")

# === /unpin ===
@bot.on(events.NewMessage(pattern='/unpin'))
async def unpin_msg(event):
    if not await is_admin(event):
        return await event.reply("You need to be an admin to use this command.")
    if not (await event.client.get_permissions(event.chat_id, 'me')).is_admin:
        return await event.reply("I don't have admin rights to unpin messages.")
    await bot.unpin_message(event.chat_id)
    await event.reply("Message unpinned.")

# === /purge ===
@bot.on(events.NewMessage(pattern='/purge'))
async def purge(event):
    if not await is_admin(event):
        return await event.reply("You need to be an admin to use this command.")
    if event.is_reply:
        start = event.reply_to_msg_id
        end = event.id
        for msg_id in range(start, end):
            try:
                await bot.delete_messages(event.chat_id, msg_id)
            except:
                pass
        await event.reply("Purged messages.")

# === /all ===
@bot.on(events.NewMessage(pattern='/all'))
async def tag_all(event):
    if not await is_admin(event):
        return await event.reply("You need to be an admin to use this command.")
    if not (await event.client.get_permissions(event.chat_id, 'me')).is_admin:
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
                          
