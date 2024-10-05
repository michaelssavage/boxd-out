package middleware

import (
	"boxd/utils"
	"net/http"
	"strings"
)

func Authenticate(next http.HandlerFunc) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        authHeader := r.Header.Get("Authorization")
        if authHeader == "" {
            http.Error(w, "Authorization header required", http.StatusUnauthorized)
            return
        }
        
        tokenParts := strings.Split(authHeader, " ")
        if len(tokenParts) != 2 || tokenParts[0] != "Bearer" {
            http.Error(w, "Invalid authorization header", http.StatusUnauthorized)
            return
        }
        
        if !utils.ValidateToken(tokenParts[1]) {
            http.Error(w, "Invalid token", http.StatusUnauthorized)
            return
        }
        
        next(w, r)
    }
}