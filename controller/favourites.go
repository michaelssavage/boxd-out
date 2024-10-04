package controller

import (
	"encoding/json"
	"fmt"
	"net/http"

	"boxd/repository"
	"boxd/service"
	"boxd/utils"

	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

func GetFavorites(w http.ResponseWriter, r *http.Request, config utils.Config) {
	movies, err := service.ScrapeFavourites(config.Username)
	if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
	}
	json.NewEncoder(w).Encode(movies)
}

func SaveFavorites(w http.ResponseWriter, r *http.Request, config utils.Config) {
	if config.MongoDBURI == "" {
		http.Error(w, "MongoDB URI not configured", http.StatusInternalServerError)
		return
	}

	movies, err := service.ScrapeFavourites(config.Username)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to scrape favorites: %v", err), http.StatusInternalServerError)
		return
	}

	client, err := mongo.Connect(r.Context(), options.Client().ApplyURI(config.MongoDBURI))
		if err != nil {
			http.Error(w, "Failed to connect to database", http.StatusInternalServerError)
			return
		}
		defer client.Disconnect(r.Context())

	err = repository.UpdateDatabase(r.Context(), client, movies)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.WriteHeader(http.StatusCreated)
		json.NewEncoder(w).Encode(map[string]string{
			"message": "Successfully saved favorites to database",
			"count":   fmt.Sprintf("%d", len(movies)),
		})
}