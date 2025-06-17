package handlers

import (
	"github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func IsTagAll(update tgbotapi.Update) bool {
	if update.Message == nil {
		return false
	}
	return len(update.Message.Text) > 0 && update.Message.Text[0:7] == "/tagall"
}

func HandleTagAll(bot *tgbotapi.BotAPI, update tgbotapi.Update) {
	msg := tgbotapi.NewMessage(update.Message.Chat.ID, "Tagging all members (not implemented).")
	bot.Send(msg)
}