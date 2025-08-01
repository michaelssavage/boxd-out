from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .repository import MovieRepository
from .services import ImageOptimizer, LetterboxdScraper, SingleMovieScraper


@api_view(["GET"])
def health_check(request):
    """Simple health check endpoint"""
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'database': 'postgresql'
    })


@api_view(["GET"])
def scrape_favourites(request):
    """Scrape favorites from Letterboxd without saving to database"""
    try:
        username = getattr(settings, 'LETTERBOXD_USERNAME', None)
        if not username:
            return Response(
                {'error': 'Letterboxd username not configured'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        scraping_service = LetterboxdScraper()
        movies = scraping_service.scrape_favourites(username)
        
        return Response({
            'movies': movies,
            'count': len(movies),
            'scraped_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def get_favourites(request):
    """Get saved favorites from PostgreSQL database"""
    try:
        movies_data = MovieRepository.get_favourites()
        
        if not movies_data:
            return Response({
                'movies': [],
                'count': 0,
                'message': 'No favorites found'
            })
        
        return Response({
            'movies': movies_data,
            'count': len(movies_data),
            'retrieved_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response({
            'error': 'Failed to get favorites',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def save_new_movie(request):
    """
    Save a movie to favourites by scraping from Letterboxd
    
    Expected POST body:
    {
        "movie_title": "bring-her-back",
        "status": "FAVORITE"  # or "SAVED"
    }
    """
    try:
        # Check if username is configured
        username = getattr(settings, 'LETTERBOXD_USERNAME', None)
        if not username:
            return Response(
                {'error': 'Letterboxd username not configured'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Validate request data
        movie_title = request.data.get('movie_title')
        movie_status = request.data.get('status')
        
        if not movie_title:
            return Response(
                {"error": "movie_title is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not movie_status:
            movie_status = "SAVED"
        
        scraper = SingleMovieScraper()
        try:
            movie_data = scraper.scrape_movie(movie_title)
        except Exception as e:
            return Response(
                {"error": f"Failed to scrape movie: {str(e)}"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate that we have the minimum required data
        if not movie_data.get('title') or not movie_data.get('year'):
            return Response(
                {"error": "Failed to extract required movie data (title and year)"}, 
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        
        # Save using repository
        movie = MovieRepository.save_movie(
            title=movie_data['title'],
            year=movie_data['year'],
            image_url=movie_data['image_url'],
            link_url=movie_data['link_url'],
            status=movie_status
        )
        
        if not movie:
            return Response(
                {"error": "Failed to save movie to database"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Determine if this was a creation or update
        # Since save_movie uses update_or_create, we can check if it was just created
        # by comparing timestamps (within a few seconds)
        import datetime

        from django.utils import timezone
        created = (timezone.now() - movie.created_at) < datetime.timedelta(seconds=5)
        
        # Prepare response data
        response_data = {
            'id': movie.id,
            'title': movie.title,
            'year': movie.year,
            'status': movie.status,
            'image_url': movie.image_url,
            'link_url': movie.link_url,
            'created_at': movie.created_at,
            'updated_at': movie.updated_at,
            'created': created,  # True if new record, False if updated
        }
        
        return Response(
            response_data, 
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            {"error": f"Internal server error: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["POST"])
@csrf_exempt
def save_favourites(request):
    """Scrape favorites and save them to PostgreSQL database with updated image URLs"""
    try:
        username = getattr(settings, 'LETTERBOXD_USERNAME', None)
        if not username:
            return Response(
                {'error': 'Letterboxd username not configured'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Initialize services
        image_service = ImageOptimizer(width=2000, height=3000)
        scraping_service = LetterboxdScraper()
        
        # Scrape favorites
        movies = scraping_service.scrape_favourites(username)
        
        if not movies:
            return Response({
                'error': 'No movies found during scraping'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Update image URLs before saving
        movies = image_service.update_movie_image_urls(movies)
        
        # Save to PostgreSQL database using repository
        success = MovieRepository.save_favourites(movies)
        
        if not success:
            return Response({
                'error': 'Failed to save favorites to database'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Get updated count of favorites
        saved_favorites = MovieRepository.get_favourites()
        
        response_data = {
            'message': 'Successfully saved favorites to database',
            'scraped_count': len(movies),
            'total_favorites': len(saved_favorites),
            'saved_at': timezone.now().isoformat()
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        error_message = str(e)
        if "failed to scrape" in error_message.lower():
            return Response({
                'error': f'Failed to scrape favorites: {error_message}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        elif "timeout" in error_message.lower():
            return Response({
                'error': f'Scraping timeout: {error_message}'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
        else:
            return Response({
                'error': f'Unexpected error: {error_message}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def get_all_movies(request):
    """Get all movies (both saved and favorites) from database"""
    try:
        movies_data = MovieRepository.get_all_movies()
        
        return Response({
            'movies': movies_data,
            'count': len(movies_data),
            'retrieved_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response({
            'error': 'Failed to get movies',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def get_saved_movies(request):
    """Get only movies with SAVED status from database"""
    try:
        movies_data = MovieRepository.get_saved_movies()
        
        return Response({
            'movies': movies_data,
            'count': len(movies_data),
            'retrieved_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response({
            'error': 'Failed to get saved movies',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["PUT"])
@csrf_exempt
def update_movie_status(request, movie_id):
    """Update a movie's status"""
    try:
        new_status = request.data.get('status')
        
        if new_status not in ['SAVED', 'FAVORITE']:
            return Response({
                'error': 'Invalid status. Must be SAVED or FAVORITE'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        success = MovieRepository.update_movie_status(movie_id, new_status)
        
        if not success:
            return Response({
                'error': 'Movie not found or failed to update'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'message': f'Movie status updated to {new_status}',
            'movie_id': movie_id,
            'new_status': new_status,
            'updated_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to update movie status: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["DELETE"])
@csrf_exempt
def delete_movie(request, movie_id):
    """Delete a movie from the database"""
    try:
        success = MovieRepository.delete_movie(movie_id)
        
        if not success:
            return Response({
                'error': 'Movie not found or failed to delete'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'message': 'Movie deleted successfully',
            'movie_id': movie_id,
            'deleted_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to delete movie: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)