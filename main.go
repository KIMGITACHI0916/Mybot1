package main

import (
	"log"
	"os"
	"os/signal"
	"syscall"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"

	"telegram-go-bot/config"
	"telegram-go-bot/handlers"
	"telegram-go-bot/middlewares"
)

func main() {
	// Load config (BOT_TOKEN, MONGO_URI, etc.)
	cfg := config.Load()

	bot, err := tgbotapi.NewBotAPI(cfg.BotToken)
	if err != nil {
		log.Fatalf("Failed to create bot: %v", err)
	}
	bot.Debug = cfg.Debug

	log.Printf("Bot authorized on account %s", bot.Self.UserName)

	u := tgbotapi.NewUpdate(0)
	u.Timeout = 60

	updates := bot.GetUpdatesChan(u)

	// Graceful shutdown support
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)

	// Mongo connect, load persistent stuff if needed
	config.SetupMongo(cfg.MongoURI)
	defer config.CloseMongo()

	// Main update loop
	go func() {
		for update := range updates {
			// Apply anti-flood and anti-edit middlewares
			if middlewares.AntiFlood(update) {
				continue
			}
			if !middlewares.CheckEdit(update) {
				continue
			}

			// Only messages and commands supported
			if update.Message != nil {
				switch {
				// Admin commands
				case handlers.IsAdmin(update):
					handlers.HandleAdmin(bot, update)
				// Silent commands
				case handlers.IsSilent(update):
					handlers.HandleSilent(bot, update)
				// Temp commands
				case handlers.IsTemp(update):
					handlers.HandleTemp(bot, update)
				// AFK command
				case handlers.IsAfk(update):
					handlers.HandleAfk(bot, update)
				// Tagall command
				case handlers.IsTagAll(update):
					handlers.HandleTagAll(bot, update)
				// Purge command
				case handlers.IsPurge(update):
					handlers.HandlePurge(bot, update)
				// Pin/unpin command
				case handlers.IsPin(update):
					handlers.HandlePin(bot, update)
				// Help/start/info
				case handlers.IsHelp(update):
					handlers.HandleHelp(bot, update)
				case handlers.IsInfo(update):
					handlers.HandleInfo(bot, update)
				case handlers.IsStart(update):
					handlers.HandleStart(bot, update)
				}
			}
		}
	}()

	log.Println("Bot is running... Press Ctrl+C to exit.")
	<-stop
	log.Println("Shutting down...")
}
