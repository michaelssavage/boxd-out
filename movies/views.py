from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .repository import MovieRepository
from .services import ImageOptimizer, LetterboxdScraper


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