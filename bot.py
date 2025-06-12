from telethon import TelegramClient, events
from telethon.tl.functions.users import GetFullUser
from telethon.tl.types import PeerUser
import os

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH"))
bot_token = os.getenv("BOT_TOKEN")

bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# Example: /info command
@bot.on(events.NewMessage(pattern='/info'))
async def info_handler(event):
    reply = await event.get_reply_message()
    user = reply.sender if reply else event.sender
    full = await bot(GetFullUser(PeerUser(user.id)))

    status = "Approved ✅" if user.bot else "Not Approved ❌"

    info_text = f"<b>User Info:</b>\n"
    info_text += f"<b>ID:</b> <code>{user.id}</code>\n"
    info_text += f"<b>First Name:</b> {user.first_name}\n"
    info_text += f"<b>Username:</b> @{user.username if user.username else 'None'}\n"
    info_text += f"<b>User Link:</b> <a href='tg://user?id={user.id}'>Click Here</a>\n"
    info_text += f"<b>Status:</b> {status}"

    await event.reply(info_text, parse_mode='html')

# Other Commands (placeholders for now)
@bot.on(events.NewMessage(pattern='/ban'))
async def ban(event):
    pass

@bot.on(events.NewMessage(pattern='/mute'))
async def mute(event):
    pass

@bot.on(events.NewMessage(pattern='/kick'))
async def kick(event):
    pass

@bot.on(events.NewMessage(pattern='/tmute'))
async def tmute(event):
    pass

@bot.on(events.NewMessage(pattern='/tban'))
async def tban(event):
    pass

# Add purge, antiflood, pin commands similarly

print("Telethon bot started")
bot.run_until_disconnected()
