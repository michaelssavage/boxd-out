import json

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .repository import MovieRepository
from .services import ImageOptimizer, LetterboxdScraper


@require_http_methods(["GET"])
def health_check(request):
    """Simple health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'database': 'postgresql'
    })


@require_http_methods(["GET"])
def scrape_favourites(request):
    """Scrape favorites from Letterboxd without saving to database"""
    try:
        username = getattr(settings, 'LETTERBOXD_USERNAME', None)
        if not username:
            return JsonResponse(
                {'error': 'Letterboxd username not configured'}, 
                status=500
            )
        
        scraping_service = LetterboxdScraper()
        movies = scraping_service.scrape_favourites(username)
        
        return JsonResponse({
            'movies': movies,
            'count': len(movies),
            'scraped_at': timezone.now().isoformat()
        }, safe=False)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_favourites(request):
    """Get saved favorites from PostgreSQL database"""
    try:
        # Get favorites using the repository
        movies = MovieRepository.get_favourites()
        
        if not movies:
            return JsonResponse({
                'movies': [],
                'count': 0,
                'message': 'No favorites found'
            }, status=200)  # Changed from 404 to 200 for empty results
        
        # Convert Django model instances to dictionaries
        movies_data = []
        for movie in movies:
            movies_data.append({
                'id': movie.id,
                'title': movie.title,
                'year': movie.year,
                'status': movie.status,
                'image_url': movie.image_url,
                'link_url': movie.link_url,
                'created_at': movie.created_at.isoformat(),
                'updated_at': movie.updated_at.isoformat(),
            })
        
        return JsonResponse({
            'movies': movies_data,
            'count': len(movies_data),
            'retrieved_at': timezone.now().isoformat()
        }, safe=False)
        
    except Exception as e:
        return JsonResponse({
            'error': 'Failed to get favorites',
            'details': str(e)
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def save_favourites(request):
    """Scrape favorites and save them to PostgreSQL database with updated image URLs"""
    try:
        username = getattr(settings, 'LETTERBOXD_USERNAME', None)
        if not username:
            return JsonResponse(
                {'error': 'Letterboxd username not configured'}, 
                status=500
            )
        
        # Initialize services
        image_service = ImageOptimizer(width=2000, height=3000)
        scraping_service = LetterboxdScraper()
        
        # Scrape favorites
        movies = scraping_service.scrape_favourites(username)
        
        if not movies:
            return JsonResponse({
                'error': 'No movies found during scraping'
            }, status=404)
        
        # Update image URLs before saving
        movies = image_service.update_movie_image_urls(movies)
        
        # Save to PostgreSQL database using repository
        success = MovieRepository.save_favourites(movies)
        
        if not success:
            return JsonResponse({
                'error': 'Failed to save favorites to database'
            }, status=500)
        
        # Get updated count of favorites
        saved_favorites = MovieRepository.get_favourites()
        
        response = JsonResponse({
            'message': 'Successfully saved favorites to database',
            'scraped_count': len(movies),
            'total_favorites': len(saved_favorites),
            'saved_at': timezone.now().isoformat()
        }, status=201)
        
        # Add CORS header (equivalent to Go's c.Header)
        response['Access-Control-Allow-Origin'] = '*'
        
        return response
        
    except Exception as e:
        error_message = str(e)
        if "failed to scrape" in error_message.lower():
            return JsonResponse({
                'error': f'Failed to scrape favorites: {error_message}'
            }, status=500)
        elif "timeout" in error_message.lower():
            return JsonResponse({
                'error': f'Scraping timeout: {error_message}'
            }, status=408)
        else:
            return JsonResponse({
                'error': f'Unexpected error: {error_message}'
            }, status=500)


@require_http_methods(["GET"])
def get_all_movies(request):
    """Get all movies (both saved and favorites) from database"""
    try:
        movies = MovieRepository.get_all_movies()
        
        movies_data = []
        for movie in movies:
            movies_data.append({
                'id': movie.id,
                'title': movie.title,
                'year': movie.year,
                'status': movie.status,
                'image_url': movie.image_url,
                'link_url': movie.link_url,
                'created_at': movie.created_at.isoformat(),
                'updated_at': movie.updated_at.isoformat(),
            })
        
        return JsonResponse({
            'movies': movies_data,
            'count': len(movies_data),
            'retrieved_at': timezone.now().isoformat()
        }, safe=False)
        
    except Exception as e:
        return JsonResponse({
            'error': 'Failed to get movies',
            'details': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_saved_movies(request):
    """Get only movies with SAVED status from database"""
    try:
        movies = MovieRepository.get_saved_movies()
        
        movies_data = []
        for movie in movies:
            movies_data.append({
                'id': movie.id,
                'title': movie.title,
                'year': movie.year,
                'status': movie.status,
                'image_url': movie.image_url,
                'link_url': movie.link_url,
                'created_at': movie.created_at.isoformat(),
                'updated_at': movie.updated_at.isoformat(),
            })
        
        return JsonResponse({
            'movies': movies_data,
            'count': len(movies_data),
            'retrieved_at': timezone.now().isoformat()
        }, safe=False)
        
    except Exception as e:
        return JsonResponse({
            'error': 'Failed to get saved movies',
            'details': str(e)
        }, status=500)


@require_http_methods(["PUT"])
@csrf_exempt
def update_movie_status(request, movie_id):
    """Update a movie's status"""
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if new_status not in ['SAVED', 'FAVORITE']:
            return JsonResponse({
                'error': 'Invalid status. Must be SAVED or FAVORITE'
            }, status=400)
        
        success = MovieRepository.update_movie_status(movie_id, new_status)
        
        if not success:
            return JsonResponse({
                'error': 'Movie not found or failed to update'
            }, status=404)
        
        return JsonResponse({
            'message': f'Movie status updated to {new_status}',
            'movie_id': movie_id,
            'new_status': new_status,
            'updated_at': timezone.now().isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Failed to update movie status: {str(e)}'
        }, status=500)


@require_http_methods(["DELETE"])
@csrf_exempt
def delete_movie(request, movie_id):
    """Delete a movie from the database"""
    try:
        success = MovieRepository.delete_movie(movie_id)
        
        if not success:
            return JsonResponse({
                'error': 'Movie not found or failed to delete'
            }, status=404)
        
        return JsonResponse({
            'message': 'Movie deleted successfully',
            'movie_id': movie_id,
            'deleted_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Failed to delete movie: {str(e)}'
        }, status=500)