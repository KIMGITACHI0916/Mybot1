package main

import (
	"log"
	"net/http"
	"os/exec"
)

func main() {
	// Run bot.py in background
	go func() {
		cmd := exec.Command("python3", "bot.py")
		cmd.Stdout = log.Writer()
		cmd.Stderr = log.Writer()
		if err := cmd.Run(); err != nil {
			log.Fatalf("Bot failed: %v", err)
		}
	}()

	// Railway healthcheck
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("Bot is running."))
	})

	log.Println("Starting Go server on port 8080...")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
