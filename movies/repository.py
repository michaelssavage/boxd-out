from typing import Any, Dict, List, Optional

from django.db import transaction

from .models import Movie


class MovieRepository:
    
    @staticmethod
    def save_favourites(movies_data: List[Dict[str, Any]]) -> bool:
        """
        Save favorite movies to the database.
        If a movie already exists with FAVORITE status, it will not be updated.
        
        Args:
            movies_data: List of dictionaries containing movie data with keys:
                        'title', 'year', 'image_url', 'link_url'
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with transaction.atomic():
                # Process each movie in the favorites list
                for movie_data in movies_data:
                    title = movie_data.get('title')
                    year = movie_data.get('year')
                    
                    # Check if movie already exists
                    try:
                        existing_movie = Movie.objects.get(title=title, year=year)
                        
                        # If it's already a favorite, skip updating it
                        if existing_movie.status == Movie.Status.FAVORITE:
                            continue
                        
                        # If it exists but is SAVED, update it to FAVORITE
                        existing_movie.status = Movie.Status.FAVORITE
                        existing_movie.save()
                        
                    except Movie.DoesNotExist:
                        # Movie doesn't exist, create it as a favorite
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
    def get_favourites() -> List[Movie]:
        """
        Get favorite movies from the database.
        
        Returns:
            List[Movie]: List of favorite movies ordered by creation date
        """
        try:
            favorites = Movie.objects.filter(status=Movie.Status.FAVORITE).order_by('-created_at')
            return [
                {
                    'id': movie.id,
                    'title': movie.title,
                    'year': movie.year,
                    'image_url': movie.image_url,
                    'link_url': movie.link_url,
                    'status': movie.status,
                    'created_at': movie.created_at.isoformat(),
                    'updated_at': movie.updated_at.isoformat(),
                }
                for movie in favorites
            ]
        except Exception as e:
            print(f"Error getting favorites data: {e}")
            return []
    
    @staticmethod
    def save_movie(title: str, year: str, image_url: str, link_url: str, 
                   status: str = Movie.Status.SAVED) -> Optional[Movie]:
        """
        Save a single movie to the database.
        
        Args:
            title: Movie title
            year: Movie year
            image_url: URL to movie poster/image
            link_url: URL to movie page
            status: Movie status (SAVED or FAVORITE)
            
        Returns:
            Movie: The created/updated movie object, None if error
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
    def get_all_movies() -> List[Movie]:
        """
        Get all movies regardless of status.
        
        Returns:
            List[Movie]: All movies ordered by creation date
        """
        try:
            return list(Movie.objects.all().order_by('-created_at'))
        except Exception as e:
            print(f"Error getting all movies: {e}")
            return []
    
    @staticmethod
    def get_saved_movies() -> List[Movie]:
        """
        Get movies with SAVED status.
        
        Returns:
            List[Movie]: Movies with SAVED status
        """
        try:
            return list(
                Movie.objects.filter(status=Movie.Status.SAVED)
                .order_by('-created_at')
            )
        except Exception as e:
            print(f"Error getting saved movies: {e}")
            return []
    
    @staticmethod
    def update_movie_status(movie_id: int, status: str) -> bool:
        """
        Update a movie's status.
        
        Args:
            movie_id: ID of the movie to update
            status: New status (SAVED or FAVORITE)
            
        Returns:
            bool: True if successful, False otherwise
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
        
        Args:
            movie_id: ID of the movie to delete
            
        Returns:
            bool: True if successful, False otherwise
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
