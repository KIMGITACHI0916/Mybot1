
package main

import (
  tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
  "strings"
)

func handleUpdate(bot *tgbotapi.BotAPI, upd tgbotapi.Update, flood *FloodGuard) {
  msg := upd.Message
  chatID := msg.Chat.ID

  if flood.IsFlood(chatID, msg.From.ID) {
    bot.Send(tgbotapi.NewDeleteMessage(chatID, msg.MessageID))
    return
  }

  text := msg.Text
  if text == "" { return }
  parts := strings.Split(text, " ")
  cmd := strings.ToLower(parts[0])

  switch {
  case cmd == "/start":
    bot.Send(tgbotapi.NewMessage(chatID, "Welcome! Use /help to see commands."))
  case cmd == "/help":
    bot.Send(tgbotapi.NewMessage(chatID, "**Commands:**\n/info – get user info\nAdmin: ban, tban, sban, unban, mute, ... tagall, purge, pin, etc."))
  case cmd == "/info":
    sendInfo(bot, msg)
  case cmd == "/al", cmd == "@all", cmd == "/tagall", cmd == "/all":
    tagAll(bot, bot, msg)
  default:
    if isAdmin(cmd) {
      handleAdmin(bot, msg, cmd, parts[1:])
    }
  }
}
