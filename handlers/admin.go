package handlers

import (
	"github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func IsAdmin(update tgbotapi.Update) bool {
	// Implement your logic to detect admin commands
	if update.Message == nil {
		return false
	}
	// Example: check if message text starts with "/admin"
	return len(update.Message.Text) > 0 && update.Message.Text[0:6] == "/admin"
}

func HandleAdmin(bot *tgbotapi.BotAPI, update tgbotapi.Update) {
	msg := tgbotapi.NewMessage(update.Message.Chat.ID, "Admin command executed.")
	bot.Send(msg)
}