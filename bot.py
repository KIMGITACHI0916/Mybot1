from telethon import TelegramClient, events, functions
from telethon.tl.types import ChatAdminRights
import asyncio
import time
import os

API_ID = 22661093
API_HASH = "344d2a8926320e2cf9211f0ffda9c03a"
BOT_TOKEN = os.getenv("7786341898:AAHdPjculC44KfjYmVyjvbloEgkfaCmkGwE")
OWNER_ID = 5064542413

client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

user_status = {}  # For anti-flood
approved_users = set([OWNER_ID])

# Anti-flood limits
FLOOD_LIMIT = 5
FLOOD_TIME = 10  # seconds

@client.on(events.NewMessage(pattern='/tagall'))
async def tag_all(event):
    if event.sender_id != OWNER_ID:
        return
    mentions = []
    async for user in client.iter_participants(event.chat_id):
        if not user.bot:
            mention = f"<a href='tg://user?id={user.id}'>\u200B</a>"
            mentions.append(mention)
    await event.respond(''.join(mentions), parse_mode='html')

@client.on(events.NewMessage(pattern='/info'))
async def info(event):
    user = await event.get_reply_message()
    if not user:
        user = event.sender
    else:
        user = await user.get_sender()

    status = "Approved" if user.id in approved_users else "Not Approved"
    text = (f"<b>User Info:</b>\n"
            f"🆔 ID: <code>{user.id}</code>\n"
            f"📛 First Name: {user.first_name}\n"
            f"🔗 Username: @{user.username if user.username else 'None'}\n"
            f"🔗 User Link: <a href='tg://user?id={user.id}'>Click here</a>\n"
            f"✅ Status: {status}")

    await event.reply(text, parse_mode='html')

@client.on(events.NewMessage(pattern=r'/purge'))
async def purge(event):
    if not event.is_reply:
        return await event.reply("Reply to a message to start purging.")
    msg = await event.get_reply_message()
    count = 0
    async for message in client.iter_messages(event.chat_id, min_id=msg.id):
        await message.delete()
        count += 1
    await event.respond(f"Purged {count} messages.")

@client.on(events.NewMessage(pattern=r'/pin'))
async def pin(event):
    if event.is_reply:
        msg = await event.get_reply_message()
        await client.pin_message(event.chat_id, msg.id)
        await event.respond("Message pinned.")

async def temp_moderate(event, action, seconds):
    if not event.is_reply:
        return await event.reply("Reply to a user.")
    user = await event.get_reply_message()
    user_id = user.sender_id
    rights = ChatAdminRights()
    if action == "mute":
        await client.edit_permissions(event.chat_id, user_id, send_messages=False)
    elif action == "ban":
        await client.edit_permissions(event.chat_id, user_id, view_messages=False)
    await event.reply(f"User temporarily {action}d for {seconds} seconds.")
    await asyncio.sleep(seconds)
    await client.edit_permissions(event.chat_id, user_id, send_messages=True, view_messages=True)
    await event.respond(f"User {action} lifted.")

@client.on(events.NewMessage(pattern=r'/tban (\d+)'))
async def tban(event):
    seconds = int(event.pattern_match.group(1))
    await temp_moderate(event, "ban", seconds)

@client.on(events.NewMessage(pattern=r'/tmute (\d+)'))
async def tmute(event):
    seconds = int(event.pattern_match.group(1))
    await temp_moderate(event, "mute", seconds)

@client.on(events.NewMessage(pattern=r'/(ban|mute|kick)'))
async def normal_mod(event):
    if not event.is_reply:
        return await event.reply("Reply to a user.")
    user = await event.get_reply_message()
    user_id = user.sender_id
    action = event.pattern_match.group(1)
    if action == "ban":
        await client.edit_permissions(event.chat_id, user_id, view_messages=False)
    elif action == "mute":
        await client.edit_permissions(event.chat_id, user_id, send_messages=False)
    elif action == "kick":
        await client.kick_participant(event.chat_id, user_id)
    await event.reply(f"User {action}ed.")

@client.on(events.NewMessage())
async def anti_flood(event):
    user_id = event.sender_id
    now = time.time()
    if user_id not in user_status:
        user_status[user_id] = []
    user_status[user_id].append(now)
    user_status[user_id] = [t for t in user_status[user_id] if now - t < FLOOD_TIME]
    if len(user_status[user_id]) > FLOOD_LIMIT:
        await client.edit_permissions(event.chat_id, user_id, send_messages=False)
        await event.respond(f"User {user_id} muted for flooding.")

print("Bot is running with moderation features.")
client.run_until_disconnected()
