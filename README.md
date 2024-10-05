# movie-box

A Go REST API for scraping my Letterboxd favorites and provides endpoints to fetch and store the data. JWT token is generated using a secret word and username flag.

## Setup

```bash
# Initialize Go module
go mod init boxd

# Install dependencies
go mod tidy
```

## Running the Server

### Prerequisites

- Go 1.16 or later
- MongoDB instance

### Environment Variables

Letterboxd username and monogdb can be set via a flag when starting the server.

- `LETTERBOXD_USERNAME`: Letterboxd username
- `MONGODB_URI`: MongoDB connection string (required for POST endpoint)
- `JWT_SECRET`: jwt token used to authenticate requests against
- `AUTH_SECRET_WORD`: for validating a jwt token generation.
- `PORT`: Server port (defaults to 8080)

### Command-line Flags

- `-username`: Override the Letterboxd username
- `-mongodb-uri`: Override the MongoDB connection URI

### Example

Start the server:

```bash
export LETTERBOXD_USERNAME=yourusername
export MONGODB_URI=mongodb://localhost:27017
go run main.go
```

## API Endpoints

### GET /favourites

Returns a JSON array of Letterboxd favorite movies.

Example response:

```json
[
  {
    "title": "The Godfather",
    "year": "1972",
    "imageUrl": "https://letterboxd.com/path/to/image.jpg",
    "movieUrl": "https://letterboxd.com/film/the-godfather/",
    "updatedAt": "2024-03-21T15:04:05Z"
  }
]
```

### POST /favourites

Scrapes Letterboxd favorites and saves them to MongoDB.

Example response:

```json
{
  "message": "Successfully saved favorites to database",
  "count": "4"
}
```

Both endpoints have CORS enabled, allowing requests from any origin.

## Authentication

All endpoints (except the health check endpoint /) require authentication using a Bearer token.

Include the token in the Authorization header for all requests. Example Requests:

```bash
# Get favorites
curl -X GET http://localhost:8080/favourites \
  -H "Authorization: Bearer your_token_here"

# Scrape and save favorites
curl -X POST http://localhost:8080/favourites \
  -H "Authorization: Bearer your_token_here"
```

Error Responses

Missing token:

```json
{
  "error": "Authorization header required"
}
```

Invalid token:

```json
{
  "error": "Invalid token"
}
```
