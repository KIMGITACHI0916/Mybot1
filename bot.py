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
approved_users = set()

# === /start ===
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply("Bot is online!")

# === /ban ===
@bot.on(events.NewMessage(pattern='/ban'))
async def ban(event):
    if event.is_reply:
        user = await event.get_reply_message().get_sender()
        await bot(functions.channels.EditBannedRequest(
            event.chat_id,
            user.id,
            types.ChatBannedRights(view_messages=True)
        ))
        await event.reply("User banned.")

# === /mute ===
@bot.on(events.NewMessage(pattern='/mute'))
async def mute(event):
    if event.is_reply:
        user = await event.get_reply_message().get_sender()
        await bot(functions.channels.EditBannedRequest(
            event.chat_id,
            user.id,
            types.ChatBannedRights(send_messages=True)
        ))
        await event.reply("User muted.")

# === /kick ===
@bot.on(events.NewMessage(pattern='/kick'))
async def kick(event):
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
            types.ChatBannedRights(view_messages=False)
        ))
        await event.reply("User kicked.")

# === /tmute command ===
@bot.on(events.NewMessage(pattern=r"/tmute (\d+)([smhd])"))
async def tmute(event):
    if event.is_reply:
        time_val = int(event.pattern_match.group(1))
        unit = event.pattern_match.group(2)
        units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        seconds = time_val * units[unit]
        user = await event.get_reply_message().get_sender()
        await bot(functions.channels.EditBannedRequest(
            event.chat_id,
            user.id,
            types.ChatBannedRights(until_date=time.time() + seconds, send_messages=True)
        ))
        await event.reply(f"Muted for {time_val}{unit}")

# === /tban command ===
@bot.on(events.NewMessage(pattern=r"/tban (\d+)([smhd])"))
async def tban(event):
    if event.is_reply:
        time_val = int(event.pattern_match.group(1))
        unit = event.pattern_match.group(2)
        units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        seconds = time_val * units[unit]
        user = await event.get_reply_message().get_sender()
        await bot(functions.channels.EditBannedRequest(
            event.chat_id,
            user.id,
            types.ChatBannedRights(until_date=time.time() + seconds, view_messages=True)
        ))
        await event.reply(f"Banned for {time_val}{unit}")

# === Anti-flood ===
@bot.on(events.NewMessage())
async def flood_control(event):
    if event.is_private:
        return
    user_id = event.sender_id
    now = time.time()
    history = flood_tracker.get(user_id, [])
    history = [msg for msg in history if now - msg < 10]  # last 10 seconds
    history.append(now)
    flood_tracker[user_id] = history
    if len(history) > 5:
        await event.respond("Stop spamming or you may be muted!")

# === /info command ===
@bot.on(events.NewMessage(pattern='/info'))
async def user_info(event):
    if event.is_reply:
        user = await event.get_reply_message().get_sender()
    else:
        user = await event.get_sender()
    name = user.first_name or "None"
    username = f"@{user.username}" if user.username else "None"
    link = f"tg://user?id={user.id}"
    approved = "Approved" if user.id in approved_users else "Not Approved"
    
    msg = f"User info:\nID: [{user.id}](tg://user?id={user.id})\nFirst Name: {name}\nUsername: {username}\nUser link: [Click here]({link})\nStatus: {approved}"
    await event.reply(msg, link_preview=False)

# === /pin ===
@bot.on(events.NewMessage(pattern='/pin'))
async def pin_msg(event):
    if event.is_reply:
        await bot.pin_message(event.chat_id, event.reply_to_msg_id)
        await event.reply("Message pinned.")

# === /purge ===
@bot.on(events.NewMessage(pattern='/purge'))
async def purge(event):
    if event.is_reply:
        start = event.reply_to_msg_id
        end = event.id
        for msg_id in range(start, end):
            try:
                await bot.delete_messages(event.chat_id, msg_id)
            except:
                pass
        await event.reply("Purged messages.")

print("Bot started")
bot.run_until_disconnected()
