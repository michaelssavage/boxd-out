package main

import (
	"context"
	"flag"
	"log"
	"net/http"
	"os"

	"boxd/controller"
	"boxd/middleware"
	"boxd/utils"

	"github.com/joho/godotenv"

	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

func startServer(config utils.Config) error {
	client, err := mongo.Connect(context.Background(), options.Client().ApplyURI(config.MongoDBURI))
    if err != nil {
        return err
    }
    defer client.Disconnect(context.Background())

	mux := http.NewServeMux()

	mux.HandleFunc("/", 
		controller.CheckHealth,
	)
	
	mux.HandleFunc("/scrape",
        middleware.Authenticate(func(w http.ResponseWriter, r *http.Request) {
            controller.ScrapeFavourites(w, r, config)
        }, config),
    )

		mux.HandleFunc("/favourites",
		middleware.Authenticate(func(w http.ResponseWriter, r *http.Request) {
				switch r.Method {
				case http.MethodGet:
						controller.GetFavourites(w, r, config, client)
				case http.MethodPost:
						controller.SaveFavourites(w, r, config, client)
				default:
						http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
				}
		}, config),
)
	
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	
	log.Printf("Starting HTTP server on :%s", port)
	return http.ListenAndServe(":"+port, mux)
}

func main() {
	godotenv.Load()

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