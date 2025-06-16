
package main

import (
  "log"
  "os"
  "time"

  "github.com/joho/godotenv"
  tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func main() {
  godotenv.Load()
  botToken := os.Getenv("BOT_TOKEN")
  if botToken == "" { log.Fatal("BOT_TOKEN required") }

  bot, err := tgbotapi.NewBotAPI(botToken)
  if err != nil { log.Fatal(err) }

  u := tgbotapi.NewUpdate(0)
  u.Timeout = 60
  updates := bot.GetUpdatesChan(u)

  flood := NewFloodGuard()

  for update := range updates {
    if update.Message != nil {
      flood.Process(update.Message.Chat.ID, update.Message.From.ID)
      handleUpdate(bot, update, flood)
    }
    if update.EditedMessage != nil {
      onEdit(bot, update.EditedMessage)
    }
  }
}
