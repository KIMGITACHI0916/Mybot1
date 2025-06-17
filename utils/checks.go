package utils

import (
	"strings"

	"github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

// IsCommand checks if the message starts with a /
func IsCommand(msg *tgbotapi.Message) bool {
	return msg != nil && strings.HasPrefix(msg.Text, "/")
}

// IsAdmin checks if the user is an admin (dummy, always false, replace with real logic)
func IsAdmin(userID int, chatID int64) bool {
	// TODO: Implement with actual Telegram getChatAdministrators API
	return false
}