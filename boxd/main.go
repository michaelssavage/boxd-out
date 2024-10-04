package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
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
	Title     string    `json:"title"`
	Year      string    `json:"year"`
	ImageURL  string    `json:"imageUrl"`
	MovieURL  string    `json:"movieUrl"`
	UpdatedAt time.Time `json:"updatedAt"`
}

type FavoriteMovies struct {
	ID          string    `json:"id"`
	Movies      []Movie   `json:"movies"`
	LastUpdated time.Time `json:"lastUpdated"`
}

// Configuration struct to hold runtime settings
type Config struct {
	Local      bool
	Username   string
	MongoDBURI string
}

func handler(ctx context.Context, request events.APIGatewayProxyRequest) (*events.APIGatewayProxyResponse, error) {
	config := Config{
		Local:      false,
		MongoDBURI: os.Getenv("MONGODB_URI"),
		Username:   os.Getenv("LETTERBOXD_USERNAME"),
	}
	
	return handleRequest(ctx, config)
}

func handleRequest(ctx context.Context, config Config) (*events.APIGatewayProxyResponse, error) {
	movies, err := scrapeFavorites(config.Username)
	if err != nil {
		return &events.APIGatewayProxyResponse{
			StatusCode: 500,
			Body:       fmt.Sprintf("Failed to scrape favorites: %v", err),
		}, err
	}

	if config.Local {
		jsonData, err := json.MarshalIndent(movies, "", "  ")
		if err != nil {
			return &events.APIGatewayProxyResponse{
				StatusCode: 500,
				Body:       fmt.Sprintf("Failed to marshal JSON: %v", err),
			}, err
		}
		return &events.APIGatewayProxyResponse{
			StatusCode: 200,
			Body:       string(jsonData),
		}, nil
	}

	client, err := mongo.Connect(ctx, options.Client().ApplyURI(config.MongoDBURI))
	if err != nil {
		return &events.APIGatewayProxyResponse{
			StatusCode: 500,
			Body:       "Failed to connect to database",
		}, err
	}
	defer client.Disconnect(ctx)

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

func scrapeFavorites(username string) ([]Movie, error) {
	url := fmt.Sprintf("https://letterboxd.com/%s/", username)
	resp, err := http.Get(url)
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
		ID:          "latest",
		Movies:      movies,
		LastUpdated: time.Now(),
	}

	opts := options.Replace().SetUpsert(true)
	filter := bson.D{{Key: "_id", Value: favoriteMovies.ID}}
	
	_, err := collection.ReplaceOne(ctx, filter, favoriteMovies, opts)
	return err
}

func main() {
	// Define flags but use environment variables as defaults
	local := flag.Bool("local", false, "Run in local mode")
	username := flag.String("username", os.Getenv("LETTERBOXD_USERNAME"), "Letterboxd username")
	mongoURI := flag.String("mongodb-uri", os.Getenv("MONGODB_URI"), "MongoDB connection URI")
	flag.Parse()

	if *local {
		if *username == "" {
			log.Fatal("Letterboxd username is required. Set LETTERBOXD_USERNAME environment variable or use -username flag")
		}

		if !*local && *mongoURI == "" {
			log.Fatal("MongoDB URI is required when not in local mode. Set MONGODB_URI environment variable or use -mongodb-uri flag")
		}

		config := Config{
			Local:      true,
			Username:   *username,
			MongoDBURI: *mongoURI,
		}

		response, err := handleRequest(context.Background(), config)
		if err != nil {
			log.Fatalf("Error: %v", err)
		}
		fmt.Println(response.Body)
	} else {
		lambda.Start(handler)
	}
}