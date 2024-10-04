# movie-box

A Go application that scrapes your Letterboxd favorites and can either display them locally or store them in MongoDB. It can run as a local command-line tool or as an AWS Lambda function.

## Setup

```bash
# Initialize Go module
go mod init boxd

# Install dependencies
go mod tidy
```

## Running Locally

### Prerequisites

- Go 1.16 or later
- MongoDB instance (if not running in local-only mode)

### Environment Variables

You can set these environment variables or override them with command-line flags:

- `LETTERBOXD_USERNAME`: Your Letterboxd username
- `MONGODB_URI`: MongoDB connection string (not required for local-only execution)

### Command-line Flags

- `-local`: Run in local mode (outputs JSON to console instead of saving to MongoDB)
- `-username`: Override the Letterboxd username
- `-mongodb-uri`: Override the MongoDB connection URI

### Examples

1. Using environment variables:

```bash
export LETTERBOXD_USERNAME=yourusername
export MONGODB_URI=mongodb://localhost:27017
go run main.go -local
```

2. Using command-line flags:

```bash
go run main.go -local -username=yourusername
```

3. Running with MongoDB:

```bash
go run main.go -username=yourusername -mongodb-uri=mongodb://localhost:27017
```

## Deploying as AWS Lambda

### Prerequisites

- AWS account
- AWS CLI configured
- Docker (for building the Lambda deployment package)

### Building for Lambda

1. Build the binary:

```bash
GOOS=linux GOARCH=amd64 go build -o main
```

2. Create a Lambda deployment package:

```bash
zip function.zip main
```

### Deploying to AWS Lambda

1. Create a new Lambda function using the AWS Console or CLI
2. Upload the `function.zip` file
3. Set the required environment variables in the Lambda configuration:
   - `LETTERBOXD_USERNAME`
   - `MONGODB_URI`

### Lambda Function Configuration

- Handler: Use `main` as the handler name
- Runtime: Go 1.x
- Memory: 128 MB should be sufficient
- Timeout: 30 seconds recommended

## MongoDB Schema

The application stores data in MongoDB using the following schema:

```json
{
  "_id": "latest",
  "movies": [
    {
      "title": "Movie Title",
      "year": "2024",
      "imageUrl": "https://letterboxd.com/path/to/image.jpg",
      "movieUrl": "https://letterboxd.com/film/movie-title/",
      "updatedAt": "2024-03-21T15:04:05Z"
    }
  ],
  "lastUpdated": "2024-03-21T15:04:05Z"
}
```

## Development

### Project Structure

```
movie-box/
├── main.go        # Main application code
├── go.mod         # Go module file
├── go.sum         # Go module checksum
└── README.md      # This file
```

### Dependencies

- github.com/PuerkitoBio/goquery - HTML parsing
- github.com/aws/aws-lambda-go - AWS Lambda support
- go.mongodb.org/mongo-driver - MongoDB driver

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
