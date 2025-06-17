package handlers

import (
	"github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func IsPin(update tgbotapi.Update) bool {
	if update.Message == nil {
		return false
	}
	return len(update.Message.Text) > 0 && (update.Message.Text[0:4] == "/pin" || update.Message.Text[0:6] == "/unpin")
}

func HandlePin(bot *tgbotapi.BotAPI, update tgbotapi.Update) {
	msg := tgbotapi.NewMessage(update.Message.Chat.ID, "Pin/unpin command executed.")
	bot.Send(msg)
}