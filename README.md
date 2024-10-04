# movie-box

A Go REST API that scrapes your Letterboxd favorites and provides endpoints to fetch and store the data.

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
- MongoDB instance (optional, only needed for POST endpoint)

### Environment Variables

You can set these environment variables or override them with command-line flags:

- `LETTERBOXD_USERNAME`: Your Letterboxd username (required)
- `MONGODB_URI`: MongoDB connection string (required for POST endpoint)
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

Returns a JSON array of your Letterboxd favorite movies.

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

Scrapes your Letterboxd favorites and saves them to MongoDB.

Example response:

```json
{
  "message": "Successfully saved favorites to database",
  "count": "4"
}
```

Both endpoints have CORS enabled, allowing requests from any origin.
