package utils

import "time"

type Config struct {
	Username   string
	MongoDBURI string
	PublicKey  string
}

type AuthKey struct {
	PublicKey string    `bson:"public_key"`
	CreatedAt time.Time `bson:"created_at"`
	LastUsed  time.Time `bson:"last_used"`
	IsActive  bool      `bson:"is_active"`
}