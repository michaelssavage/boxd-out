package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/PuerkitoBio/goquery"
	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

type Movie struct {
	Title     string `json:"title"`
	Year      string `json:"year"`
	ImageURL  string `json:"imageUrl"`
	MovieURL  string `json:"movieUrl"`
	UpdatedAt time.Time `json:"updatedAt"`
}

type FavoriteMovies struct {
	ID      string  `json:"id"`
	Movies  []Movie `json:"movies"`
	LastUpdated time.Time `json:"lastUpdated"`
}

func handler(ctx context.Context, request events.APIGatewayProxyRequest) (*events.APIGatewayProxyResponse, error) {
	mongoURI := os.Getenv("MONGODB_URI")
	
	client, err := mongo.Connect(ctx, options.Client().ApplyURI(mongoURI))
	if err != nil {
		return &events.APIGatewayProxyResponse{
			StatusCode: 500,
			Body:       "Failed to connect to database",
		}, err
	}
	defer client.Disconnect(ctx)

	movies, err := scrapeFavorites()
	if err != nil {
		return &events.APIGatewayProxyResponse{
			StatusCode: 500,
			Body:       "Failed to scrape favorites",
		}, err
	}

	err = updateDatabase(ctx, client, movies)
	if err != nil {
		return &events.APIGatewayProxyResponse{
			StatusCode: 500,
			Body:       "Failed to update database",
		}, err
	}

	return &events.APIGatewayProxyResponse{
		StatusCode: 200,
		Body:       "Successfully updated favorites",
	}, nil
}

func scrapeFavorites() ([]Movie, error) {
	resp, err := http.Get("https://letterboxd.com/ottobio/")
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	doc, err := goquery.NewDocumentFromReader(resp.Body)
	if err != nil {
		return nil, err
	}

	var movies []Movie
	doc.Find("#favourites .poster-container").Each(func(i int, s *goquery.Selection) {
		poster := s.Find(".film-poster")
		
		movie := Movie{
			Title:     poster.AttrOr("data-film-name", ""),
			Year:      poster.AttrOr("data-film-release-year", ""),
			ImageURL:  poster.Find("img").AttrOr("src", ""),
			MovieURL:  "https://letterboxd.com" + poster.AttrOr("data-film-link", ""),
			UpdatedAt: time.Now(),
		}
		movies = append(movies, movie)
	})

	return movies, nil
}

func updateDatabase(ctx context.Context, client *mongo.Client, movies []Movie) error {
	collection := client.Database("letterboxd").Collection("favorites")
	
	favoriteMovies := FavoriteMovies{
		ID:          "latest", // Using a fixed ID to always update the same document
		Movies:      movies,
		LastUpdated: time.Now(),
	}

	opts := options.Replace().SetUpsert(true)
	filter := bson.D{{Key: "_id", Value: favoriteMovies.ID}}
	
	_, err := collection.ReplaceOne(ctx, filter, favoriteMovies, opts)
	return err
}

func main() {
	lambda.Start(handler)
}