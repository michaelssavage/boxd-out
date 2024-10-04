# movie-box

## Setup

```
- go mod init boxd
- go mod tidy
```

## For local execution, you can run the program with various command-line flags:

**Run locally with text output**  
`go run main.go -local -username=yourusername`

**Run locally with JSON output**  
`go run main.go -local -username=yourusername -format=json`

**Run locally and update MongoDB**  
`go run main.go -local -username=yourusername -mongodb-uri="your-mongodb-uri"`

## To build the program:

`go build -o movie-box`

## Then you can run the compiled program:

`./movie-box -local -username=yourusername`

## Local Testing:

When testing locally with netlify dev, the function will be available at:  
`http://localhost:8888/api/boxd?username=someusername`
