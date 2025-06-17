package middlewares

import (
	"time"

	"github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

// AntiEdit blocks rapid message edits (example logic).
var lastEditTimestamp int64

func AntiEdit(update tgbotapi.Update) bool {
	if update.EditedMessage == nil {
		return false
	}
	now := time.Now().Unix()
	if lastEditTimestamp > 0 && now-lastEditTimestamp < 5 {
		return true // edited too soon after last edit
	}
	lastEditTimestamp = now
	return false
}