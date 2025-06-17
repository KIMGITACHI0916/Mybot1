package middlewares

import (
	"sync"
	"time"

	"github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

var (
	userLastMessage = make(map[int]int64)
	mu              sync.Mutex
	floodInterval   = int64(3) // seconds
)

// AntiFlood checks if a user is sending messages too quickly.
func AntiFlood(update tgbotapi.Update) bool {
	if update.Message == nil {
		return false
	}
	userID := update.Message.From.ID
	now := time.Now().Unix()
	mu.Lock()
	defer mu.Unlock()
	if last, ok := userLastMessage[userID]; ok && now-last < floodInterval {
		return true // flooding
	}
	userLastMessage[userID] = now
	return false
}