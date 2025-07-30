from typing import Any, Dict, List, Optional

from django.db import transaction

from .models import Movie
from .serializers import MovieSerializer


class MovieRepository:
    
    @staticmethod
    def serialize_movies(movies: List[Movie]) -> List[Dict[str, Any]]:
        """Helper method to serialize movies using DRF serializer"""
        serializer = MovieSerializer(movies, many=True)
        return serializer.data
    
    @staticmethod
    def save_favourites(movies_data: List[Dict[str, Any]]) -> bool:
        """
        Save favorite movies to the database.
        If a movie already exists with FAVORITE status, it will not be updated.
        """
        try:
            with transaction.atomic():
                for movie_data in movies_data:
                    title = movie_data.get('title')
                    year = movie_data.get('year')
                    
                    try:
                        existing_movie = Movie.objects.get(title=title, year=year)
                        if existing_movie.status == Movie.Status.FAVORITE:
                            continue
                        existing_movie.status = Movie.Status.FAVORITE
                        existing_movie.save()
                    except Movie.DoesNotExist:
                        Movie.objects.create(
                            title=title,
                            year=year,
                            status=Movie.Status.FAVORITE,
                            image_url=movie_data.get('image_url', ''),
                            link_url=movie_data.get('link_url', ''),
                        )
                return True
        except Exception as e:
            print(f"Error saving favorites: {e}")
            return False
    
    @staticmethod
    def get_favourites() -> List[Dict[str, Any]]:
        """
        Get favorite movies from the database.
        Returns serialized data using DRF serializer.
        """
        try:
            favorites = Movie.objects.filter(
                status=Movie.Status.FAVORITE
            ).order_by('-created_at')
            return MovieRepository.serialize_movies(favorites)
        except Exception as e:
            print(f"Error getting favorites data: {e}")
            return []
    
    @staticmethod
    def save_movie(title: str, year: str, image_url: str, link_url: str, 
                   status: str = Movie.Status.SAVED) -> Optional[Movie]:
        """
        Save a single movie to the database.
        Returns the model instance (not serialized).
        """
        try:
            movie, created = Movie.objects.update_or_create(
                title=title,
                year=year,
                defaults={
                    'status': status,
                    'image_url': image_url,
                    'link_url': link_url,
                }
            )
            return movie
        except Exception as e:
            print(f"Error saving movie: {e}")
            return None
    
    @staticmethod
    def get_all_movies() -> List[Dict[str, Any]]:
        """
        Get all movies regardless of status.
        Returns serialized data using DRF serializer.
        """
        try:
            movies = Movie.objects.all().order_by('-created_at')
            return MovieRepository.serialize_movies(movies)
        except Exception as e:
            print(f"Error getting all movies: {e}")
            return []
    
    @staticmethod
    def get_saved_movies() -> List[Dict[str, Any]]:
        """
        Get movies with SAVED status.
        Returns serialized data using DRF serializer.
        """
        try:
            saved_movies = Movie.objects.filter(
                status=Movie.Status.SAVED
            ).order_by('-created_at')
            return MovieRepository.serialize_movies(saved_movies)
        except Exception as e:
            print(f"Error getting saved movies: {e}")
            return []
    
    @staticmethod
    def update_movie_status(movie_id: int, status: str) -> bool:
        """
        Update a movie's status.
        Returns boolean success status.
        """
        try:
            movie = Movie.objects.get(id=movie_id)
            movie.status = status
            movie.save()
            return True
        except Movie.DoesNotExist:
            print(f"Movie with ID {movie_id} not found")
            return False
        except Exception as e:
            print(f"Error updating movie status: {e}")
            return False
    
    @staticmethod
    def delete_movie(movie_id: int) -> bool:
        """
        Delete a movie from the database.
        Returns boolean success status.
        """
        try:
            movie = Movie.objects.get(id=movie_id)
            movie.delete()
            return True
        except Movie.DoesNotExist:
            print(f"Movie with ID {movie_id} not found")
            return False
        except Exception as e:
            print(f"Error deleting movie: {e}")
            return False