package main

import (
	"flag"
	"log"
	"net/http"
	"os"

	"boxd/controller"
	"boxd/utils"

	"github.com/joho/godotenv"
)

func startServer(config utils.Config) error {
	mux := http.NewServeMux()

	mux.HandleFunc("/", controller.CheckHealth)

	mux.HandleFunc("/favourites", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			controller.GetFavorites(w, r, config)
		case http.MethodPost:
			controller.SaveFavorites(w, r, config)
		default:
			http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
		}
	})
	
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	
	log.Printf("Starting HTTP server on :%s", port)
	return http.ListenAndServe(":"+port, mux)
}

func main() {
	err := godotenv.Load()
    if err != nil {
        log.Fatal("Error loading .env file")
    }
	username := flag.String("username", os.Getenv("LETTERBOXD_USERNAME"), "Letterboxd username")
	mongoURI := flag.String("mongodb-uri", os.Getenv("MONGODB_URI"), "MongoDB connection URI")
	flag.Parse()

	if *username == "" {
		log.Fatal("Letterboxd username is required. Set LETTERBOXD_USERNAME environment variable or use -username flag")
	}

	config := utils.Config{
		Username:   *username,
		MongoDBURI: *mongoURI,
	}

	log.Fatal(startServer(config))
}