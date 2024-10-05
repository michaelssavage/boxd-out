package utils

import (
	"fmt"
	"log"
	"os"
	"time"

	"github.com/golang-jwt/jwt"
	"github.com/joho/godotenv"
)

func generateToken() (string, error) {
    token := jwt.New(jwt.SigningMethodHS256)
    claims := token.Claims.(jwt.MapClaims)
    
    claims["authorized"] = true
    claims["exp"] = time.Now().Add(time.Hour * 24 * 365).Unix() // Token expires in 1 year
    
    tokenString, err := token.SignedString([]byte(os.Getenv("JWT_SECRET")))
    if err != nil {
        return "", err
    }
    
    return tokenString, nil
}

func main() {
    err := godotenv.Load()
    if err != nil {
        log.Fatal("Error loading .env file")
    }
    
    token, err := generateToken()
    if err != nil {
        log.Fatal(err)
    }
    fmt.Println("Your Bearer Token:", token)
}