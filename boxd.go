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
	Title    string    `json:"title"`
	Year     string    `json:"year"`
	ImageURL string    `json:"imageUrl"`
	MovieURL string    `json:"movieUrl"`
	UpdatedAt time.Time `json:"updatedAt"`
}

type FavoriteMovies struct {
	ID          string    `json:"id"`
	Movies      []Movie   `json:"movies"`
	LastUpdated time.Time `json:"lastUpdated"`
}

// Configuration struct to hold runtime settings
type Config struct {
	Local        bool
	Username     string
	MongoDBURI   string
	OutputFormat string // "json" or "text"
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
	// Scrape Letterboxd favorites
	movies, err := scrapeFavorites(config.Username)
	if err != nil {
		return &events.APIGatewayProxyResponse{
			StatusCode: 500,
			Body:       fmt.Sprintf("Failed to scrape favorites: %v", err),
		}, err
	}

	if config.Local {
		// For local execution, print results based on output format
		return handleLocalOutput(movies, config.OutputFormat)
	}

	// For serverless execution, update database
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

func handleLocalOutput(movies []Movie, format string) (*events.APIGatewayProxyResponse, error) {
	switch format {
	case "json":
		jsonData, err := json.MarshalIndent(movies, "", "  ")
		if err != nil {
			return nil, fmt.Errorf("failed to marshal JSON: %v", err)
		}
		return &events.APIGatewayProxyResponse{
			StatusCode: 200,
			Body:       string(jsonData),
		}, nil
	default: // text format
		var result string
		for _, movie := range movies {
			result += fmt.Sprintf("Title: %s (%s)\nURL: %s\nImage: %s\n\n", 
				movie.Title, movie.Year, movie.MovieURL, movie.ImageURL)
		}
		return &events.APIGatewayProxyResponse{
			StatusCode: 200,
			Body:       result,
		}, nil
	}
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
	// Check if running locally
	local := flag.Bool("local", false, "Run in local mode")
	username := flag.String("username", "", "Letterboxd username")
	mongoURI := flag.String("mongodb-uri", "", "MongoDB connection URI")
	outputFormat := flag.String("format", "json", "Output format: text or json")
	flag.Parse()

	if *local {
		if *username == "" {
			log.Fatal("Username is required in local mode")
		}

		config := Config{
			Local:        true,
			Username:     *username,
			MongoDBURI:   *mongoURI,
			OutputFormat: *outputFormat,
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