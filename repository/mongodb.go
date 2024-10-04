package repository

import (
	"boxd/models"
	"context"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

func UpdateDatabase(ctx context.Context, client *mongo.Client, movies []models.Movie) error {
	collection := client.Database("letterboxd").Collection("favorites")
	
	favoriteMovies := models.FavoriteMovies{
		ID:          "latest",
		Movies:      movies,
		LastUpdated: time.Now(),
	}

	opts := options.Replace().SetUpsert(true)
	filter := bson.D{{Key: "_id", Value: favoriteMovies.ID}}
	
	_, err := collection.ReplaceOne(ctx, filter, favoriteMovies, opts)
	return err
}