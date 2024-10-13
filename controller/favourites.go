package controller

import (
	"fmt"
	"net/http"

	"boxd/repository"
	"boxd/service"
	"boxd/utils"

	"github.com/gin-gonic/gin"
	"go.mongodb.org/mongo-driver/mongo"
)

func ScrapeFavourites(config utils.Config) gin.HandlerFunc {
	return func(c *gin.Context) {
		movies, err := service.ScrapeFavourites(config.Username)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		c.JSON(http.StatusOK, movies)
	}
}

func GetFavourites(config utils.Config, client *mongo.Client) gin.HandlerFunc {
	return func(c *gin.Context) {
		if config.MongoDBURI == "" {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "MongoDB URI not configured"})
			return
		}

		movies, err := repository.GetFavourites(c.Request.Context(), client)
		if err != nil {
			if err == mongo.ErrNoDocuments {
				c.JSON(http.StatusNotFound, gin.H{"error": "No favorites found"})
				return
			}
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get favorites"})
			return
		}

		c.JSON(http.StatusOK, movies)
	}
}

func SaveFavourites(config utils.Config, client *mongo.Client) gin.HandlerFunc {
	return func(c *gin.Context) {
		if config.MongoDBURI == "" {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "MongoDB URI not configured"})
			return
		}

		imageService := service.NewImageService(2000, 3000)
		movies, err := service.ScrapeFavourites(config.Username)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to scrape favorites: %v", err)})
			return
		}

		// Update image URLs before saving
		movies = imageService.UpdateMovieImageURLs(movies)
		err = repository.SaveFavourites(c.Request.Context(), client, movies)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		c.Header("Access-Control-Allow-Origin", "*")
		c.JSON(http.StatusCreated, gin.H{
			"message": "Successfully saved favorites to database",
			"count":   len(movies),
		})
	}
}