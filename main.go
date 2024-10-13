package main

import (
	"context"
	"flag"
	"log"
	"os"

	"boxd/controller"
	"boxd/middleware"
	"boxd/utils"

	"github.com/gin-gonic/gin"
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

	router := gin.Default()

	router.GET("/", controller.CheckHealth)

	authorized := router.Group("/")
	authorized.Use(middleware.Authenticate(config))
	{
		authorized.GET("/scrape", controller.ScrapeFavourites(config))
    authorized.GET("/favourites", controller.GetFavourites(config, client))
    authorized.POST("/favourites", controller.SaveFavourites(config, client))
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("Starting HTTP server on :%s", port)
	return router.Run(":" + port)
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