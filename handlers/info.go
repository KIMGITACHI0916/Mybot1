package handlers

import (
	"github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func IsInfo(update tgbotapi.Update) bool {
	if update.Message == nil {
		return false
	}
	return len(update.Message.Text) > 0 && (update.Message.Text == "/info" || update.Message.Text == "/info@YourBotUsername")
}

func HandleInfo(bot *tgbotapi.BotAPI, update tgbotapi.Update) {
	msg := tgbotapi.NewMessage(update.Message.Chat.ID, "This is a Telegram bot written in Go.")
	bot.Send(msg)
}