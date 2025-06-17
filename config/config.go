package config

import (
	"log"
	"os"
)

type Config struct {
	BotToken string
	MongoURI string
	Debug    bool
}

// Load reads environment variables and returns a Config struct.
// Exits if a required variable is missing.
func Load() *Config {
	botToken := os.Getenv("BOT_TOKEN")
	mongoURI := os.Getenv("MONGO_URI")
	debug := os.Getenv("BOT_DEBUG") == "true"

	if botToken == "" {
		log.Fatal("BOT_TOKEN environment variable is required")
	}
	if mongoURI == "" {
		log.Fatal("MONGO_URI environment variable is required")
	}

	return &Config{
		BotToken: botToken,
		MongoURI: mongoURI,
		Debug:    debug,
	}
}

// Dummy placeholders for Mongo connection, customize as needed.
var mongoClient interface{}

func SetupMongo(uri string) {
	// Initialize MongoDB connection here.
	// Example: mongoClient = mongo.Connect(...)
	// For now, just a placeholder.
}

func CloseMongo() {
	// Close MongoDB connection here, if needed.
}