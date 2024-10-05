package controller

import (
	"encoding/json"
	"fmt"
	"net/http"

	"boxd/models"
	"boxd/repository"
	"boxd/service"
	"boxd/utils"

	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

func ScrapeFavourites(w http.ResponseWriter, r *http.Request, config utils.Config) {
	movies, err := service.ScrapeFavourites(config.Username)
	if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
	}
	json.NewEncoder(w).Encode(movies)
}

func GetFavourites(w http.ResponseWriter, r *http.Request, config utils.Config) ([]models.Movie, error) {
	if config.MongoDBURI == "" {
		return nil, fmt.Errorf("MongoDB URI not configured")
	}

	client, err := mongo.Connect(r.Context(), options.Client().ApplyURI(config.MongoDBURI))
	if err != nil {
			return nil, fmt.Errorf("failed to connect to database: %v", err)
	}
	defer client.Disconnect(r.Context())

	movies, err := repository.GetFavourites(r.Context(), client)
    if err != nil {
        if err == mongo.ErrNoDocuments {
            return []models.Movie{}, fmt.Errorf("failed to get documents")
        }
        return []models.Movie{}, fmt.Errorf("failed to get favorites")
    }

    if err := json.NewEncoder(w).Encode(movies); err != nil {
        return []models.Movie{}, fmt.Errorf("failed to encode response")
    }

	return movies, err
}

func SaveFavourites(w http.ResponseWriter, r *http.Request, config utils.Config) {
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

	err = repository.SaveFavourites(r.Context(), client, movies)
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