package utils

import (
	"flag"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/golang-jwt/jwt"
	"github.com/joho/godotenv"
)

// GenerateToken creates a new JWT token
func GenerateToken(username string, secretWord string) (string, error) {
	// First, verify the secret word
	expectedSecretWord := os.Getenv("AUTH_SECRET_WORD")
	expectedUsername := os.Getenv("LETTERBOXD_USERNAME")
	
	if secretWord != expectedSecretWord {
			return "", fmt.Errorf("invalid secret word")
	}

	if username != expectedUsername {
		return "", fmt.Errorf("invalid username")
}

	token := jwt.New(jwt.SigningMethodHS256)
	claims := token.Claims.(jwt.MapClaims)

	claims["authorized"] = true
	claims["username"] = username
	claims["exp"] = time.Now().Add(time.Hour * 24 * 365).Unix()

	tokenString, err := token.SignedString([]byte(os.Getenv("JWT_SECRET")))
	if err != nil {
			return "", err
	}

	return tokenString, nil
}

// ValidateToken checks if a token is valid
func ValidateToken(tokenString string, username string) bool {
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
			return []byte(os.Getenv("JWT_SECRET")), nil
	})
	
	if err != nil {
			return false
	}
	
	if claims, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {
			tokenUsername, ok := claims["username"].(string)
			if !ok {
					return false
			}
			return tokenUsername == username
	}
	
	return false
}

func main() {
	err := godotenv.Load()
	if err != nil {
			log.Println("Warning: Error loading .env file")
	}
	
	username := flag.String("username", "", "Letterboxd username")
	
	secretWord := flag.String("secret-word", "", "Secret word")
	flag.Parse()

	
	if *username == "" {
		log.Fatal("username not provided")
}

	if *secretWord == "" {
			log.Fatal("secret word not provided")
	}
	
	token, err := GenerateToken(*username, *secretWord)
	if err != nil {
			log.Fatalf("Error generating token: %v", err)
	}
	
	fmt.Println("Your Bearer Token:")
	fmt.Println(token)
	fmt.Println("\nUse this token in your Authorization header:")
	fmt.Printf("Authorization: Bearer %s\n", token)
}