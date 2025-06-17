package handlers

import (
	"github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func IsHelp(update tgbotapi.Update) bool {
	if update.Message == nil {
		return false
	}
	return len(update.Message.Text) > 0 && (update.Message.Text == "/help" || update.Message.Text == "/help@YourBotUsername")
}

func HandleHelp(bot *tgbotapi.BotAPI, update tgbotapi.Update) {
	msg := tgbotapi.NewMessage(update.Message.Chat.ID, "Help: List of available commands...\n/admin\n/silent\n/temp\n/afk\n/tagall\n/purge\n/pin\n/unpin\n/help\n/info\n/start")
	bot.Send(msg)
}