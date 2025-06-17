package handlers

import (
	"github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func IsAfk(update tgbotapi.Update) bool {
	if update.Message == nil {
		return false
	}
	return len(update.Message.Text) > 0 && update.Message.Text[0:4] == "/afk"
}

func HandleAfk(bot *tgbotapi.BotAPI, update tgbotapi.Update) {
	msg := tgbotapi.NewMessage(update.Message.Chat.ID, "You are now AFK.")
	bot.Send(msg)
}