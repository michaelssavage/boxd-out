package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/PuerkitoBio/goquery"
	"github.com/chromedp/chromedp"
	"github.com/joho/godotenv"
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
	Username   string
	MongoDBURI string
}

func startServer(config Config) error {
	handler := createHandler(config)
	
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	
	log.Printf("Starting HTTP server on :%s", port)
	return http.ListenAndServe(":"+port, handler)
}

func createHandler(config Config) http.Handler {
	mux := http.NewServeMux()

	// GET / - returns a simple status message
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/plain")
		w.Write([]byte("boxd is running"))
	})

	// GET /favourites - returns scraped favorites
	mux.HandleFunc("GET /favourites", func(w http.ResponseWriter, r *http.Request) {
		movies, err := scrapeFavorites(config.Username)
		if err != nil {
			http.Error(w, fmt.Sprintf("Failed to scrape favorites: %v", err), http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		w.Header().Set("Access-Control-Allow-Origin", "*")
		json.NewEncoder(w).Encode(movies)
	})

	// POST /favourites - scrapes and saves to MongoDB
	mux.HandleFunc("POST /favourites", func(w http.ResponseWriter, r *http.Request) {
		if config.MongoDBURI == "" {
			http.Error(w, "MongoDB URI not configured", http.StatusInternalServerError)
			return
		}

		movies, err := scrapeFavorites(config.Username)
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

		err = updateDatabase(r.Context(), client, movies)
		if err != nil {
			http.Error(w, "Failed to update database", http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.WriteHeader(http.StatusCreated)
		json.NewEncoder(w).Encode(map[string]string{
			"message": "Successfully saved favorites to database",
			"count":   fmt.Sprintf("%d", len(movies)),
		})
	})

	return mux
}

func scrapeFavorites(username string) ([]Movie, error) {
	url := fmt.Sprintf("https://letterboxd.com/%s/", username)

	// Set up a context with a timeout
	opts := append(chromedp.DefaultExecAllocatorOptions[:],
			chromedp.Headless, // Run Chrome in headless mode
			chromedp.DisableGPU, // Disable GPU usage for headless mode
			chromedp.NoSandbox, // Optionally disable sandbox for certain environments
	)
	allocCtx, cancel := chromedp.NewExecAllocator(context.Background(), opts...)
	defer cancel()

	ctx, cancel := chromedp.NewContext(allocCtx)
	defer cancel()

	// Set up a timeout to prevent hanging forever
	ctx, cancel = context.WithTimeout(ctx, 30*time.Second)
	defer cancel()

	var htmlContent string

	// Navigate to the page and wait for it to fully render
	err := chromedp.Run(ctx,
			chromedp.Navigate(url),
			chromedp.WaitVisible(`#favourites`), // Wait for the favorites section to appear
			chromedp.OuterHTML("html", &htmlContent), // Capture the page's HTML content
	)
	if err != nil {
			return nil, fmt.Errorf("failed to load page: %v", err)
	}

	// Now use goquery to scrape from the rendered HTML content
	doc, err := goquery.NewDocumentFromReader(strings.NewReader(htmlContent))
	if err != nil {
			return nil, fmt.Errorf("failed to parse HTML: %v", err)
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

	config := Config{
		Username:   *username,
		MongoDBURI: *mongoURI,
	}

	log.Fatal(startServer(config))
}