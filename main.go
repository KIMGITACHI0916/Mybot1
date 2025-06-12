package main

import (
	"fmt"
	"net/http"
)

func main() {
	port := "8080"
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "Bot is running!")
	})
	fmt.Println("Starting server on port", port)
	http.ListenAndServe(":"+port, nil)
}
