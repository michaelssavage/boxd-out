// models/movie.go
package models

import "time"

// Movie represents a movie scraped from Letterboxd
type Movie struct {
    Title     string    `json:"title"`
    Year      string    `json:"year"`
    ImageURL  string    `json:"imageUrl"`
    MovieURL  string    `json:"movieUrl"`
    UpdatedAt time.Time `json:"updatedAt"`
}

// FavoriteMovies represents a user's favorite movies and the last updated time
type FavoriteMovies struct {
    ID          string    `json:"id"`
    Movies      []Movie   `json:"movies"`
    LastUpdated time.Time `json:"lastUpdated"`
}
