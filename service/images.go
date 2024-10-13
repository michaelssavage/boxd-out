package service

import (
	"fmt"
	"regexp"
	"strings"

	"boxd/models"
)

type ImageService struct {
	DefaultWidth  int
	DefaultHeight int
}

func NewImageService(width, height int) *ImageService {
	return &ImageService{
		DefaultWidth:  width,
		DefaultHeight: height,
	}
}

func (s *ImageService) UpdateImageURL(url string) string {
	// Remove any query parameters
	url = strings.Split(url, "?")[0]

	// Update the dimensions in the URL
	re := regexp.MustCompile(`-0-\d+-0-\d+-crop`)
	replacement := fmt.Sprintf("-0-%d-0-%d-crop", s.DefaultWidth, s.DefaultHeight)
	return re.ReplaceAllString(url, replacement)
}

func (s *ImageService) UpdateMovieImageURLs(movies []models.Movie) []models.Movie {
	for i := range movies {
		movies[i].ImageURL = s.UpdateImageURL(movies[i].ImageURL)
	}
	return movies
}
