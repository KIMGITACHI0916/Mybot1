
package main

import (
  tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
  "time"
  "strings"
  "fmt"
)

func isAdmin(cmd string) bool {
  a := []string{"ban","unban","mute","unmute","kick","sban","smute","skick","spurge","purge","pin","unpin","tban","tmute"}
  for _, c := range a {
    if strings.HasPrefix(cmd, "/"+c) {
      return true
    }
  }
  return false
}

func handleAdmin(bot *tgbotapi.BotAPI, msg *tgbotapi.Message, cmd string, args []string) {
  chatID := msg.Chat.ID

  if !isUserAdmin(bot, chatID, msg.From.ID) {
    bot.Send(tgbotapi.NewMessage(chatID, "🚫 Only admins can use this."))
    return
  }

  var targetID int64
  if msg.ReplyToMessage != nil {
    targetID = int64(msg.ReplyToMessage.From.ID)
  }

  switch {
  case strings.HasPrefix(cmd, "/ban"):
    // Example ban logic
    bot.Send(tgbotapi.NewMessage(chatID, fmt.Sprintf("User %d banned", targetID)))
  case strings.HasPrefix(cmd, "/purge"):
    purgeMessages(bot, chatID, msg.MessageID, args)
  }
}
