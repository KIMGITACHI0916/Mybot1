from telethon import TelegramClient, events
import os

api_id = int(os.getenv("22661093"))
api_hash = os.getenv("344d2a8926320e2cf9211f0ffda9c03a")
bot_token = os.getenv("7786341898:AAHdPjculC44KfjYmVyjvbloEgkfaCmkGwE")

bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
	await event.reply("Bot is online!")

print("Telethon bot started")
bot.run_until_disconnected()
