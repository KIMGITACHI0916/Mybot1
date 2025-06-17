package handlers

import (
	"github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func IsStart(update tgbotapi.Update) bool {
	if update.Message == nil {
		return false
	}
	return len(update.Message.Text) > 0 && (update.Message.Text == "/start" || update.Message.Text == "/start@YourBotUsername")
}

func HandleStart(bot *tgbotapi.BotAPI, update tgbotapi.Update) {
	msg := tgbotapi.NewMessage(update.Message.Chat.ID, "Welcome! Use /help to see available commands.")
	bot.Send(msg)
}