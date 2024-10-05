package utils

import (
	"os"
	"time"

	"github.com/golang-jwt/jwt"
)

// GenerateToken creates a new JWT token - you'll use this once to create your token
func GenerateToken() (string, error) {
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

// ValidateToken checks if a token is valid
func ValidateToken(tokenString string) bool {
    token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
        return []byte(os.Getenv("JWT_SECRET")), nil
    })
    
    return err == nil && token.Valid
}