
package main

import (
  tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
  "fmt"
)

func tagAll(bot *tgbotapi.BotAPI, api *tgbotapi.BotAPI, msg *tgbotapi.Message) {
  members, _ := api.GetChatAdministrators(tgbotapi.ChatConfig{ChatID: msg.Chat.ID})
  text := "(Wanna inform)\n"
  for _, m := range members {
    text += fmt.Sprintf("[%s](tg://user?id=%d)\n", m.User.FirstName, m.User.ID)
  }
  cfg := tgbotapi.NewMessage(msg.Chat.ID, text)
  cfg.ParseMode = "Markdown"
  if msg.ReplyToMessage != nil {
    cfg.ReplyToMessageID = msg.ReplyToMessage.MessageID
  }
  api.Send(cfg)
}
