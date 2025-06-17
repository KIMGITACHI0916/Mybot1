package handlers

import (
	"github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func IsPurge(update tgbotapi.Update) bool {
	if update.Message == nil {
		return false
	}
	return len(update.Message.Text) > 0 && update.Message.Text[0:6] == "/purge"
}

func HandlePurge(bot *tgbotapi.BotAPI, update tgbotapi.Update) {
	msg := tgbotapi.NewMessage(update.Message.Chat.ID, "Purge command executed.")
	bot.Send(msg)
}