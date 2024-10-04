package service

import (
	"context"
	"fmt"
	"strings"
	"time"

	"boxd/models"

	"github.com/PuerkitoBio/goquery"
	"github.com/chromedp/chromedp"
)

func ScrapeFavourites(username string) ([]models.Movie, error) {
	url := fmt.Sprintf("https://letterboxd.com/%s/", username)

	opts := append(chromedp.DefaultExecAllocatorOptions[:],
			chromedp.Headless,
			chromedp.DisableGPU,
	)
	allocCtx, cancel := chromedp.NewExecAllocator(context.Background(), opts...)
	defer cancel()

	ctx, cancel := chromedp.NewContext(allocCtx)
	defer cancel()

	ctx, cancel = context.WithTimeout(ctx, 30*time.Second)
	defer cancel()

	var htmlContent string

	err := chromedp.Run(ctx,
			chromedp.Navigate(url),
			chromedp.WaitVisible(`#favourites`),
			chromedp.Sleep(2*time.Second),
			chromedp.OuterHTML("html", &htmlContent),
	)
	if err != nil {
			return nil, fmt.Errorf("failed to load page: %v", err)
	}

	doc, err := goquery.NewDocumentFromReader(strings.NewReader(htmlContent))
	if err != nil {
			return nil, fmt.Errorf("failed to parse HTML: %v", err)
	}

	var movies []models.Movie
	doc.Find("#favourites .poster-container").Each(func(i int, s *goquery.Selection) {
			poster := s.Find(".film-poster")

			movie := models.Movie{
					Title:     poster.AttrOr("data-film-name", ""),
					Year:      poster.AttrOr("data-film-release-year", ""),
					ImageURL:  poster.Find("img").AttrOr("src", ""),
					MovieURL:  "https://letterboxd.com" + poster.AttrOr("data-film-link", ""),
					UpdatedAt: time.Now(),
			}
			movies = append(movies, movie)
	})

	if len(movies) == 0 {
		return nil, fmt.Errorf("no movies found, possibly failed to load dynamic content")
}

	return movies, nil
}