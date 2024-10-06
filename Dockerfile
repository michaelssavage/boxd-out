FROM golang:1.19
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o /boxd
EXPOSE 8080
CMD ["/boxd"]