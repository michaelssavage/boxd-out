from django.urls import path

from . import views

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),
    
    # Scraping endpoints
    path('scrape/favourites/', views.scrape_favourites, name='scrape_favourites'),
    path('scrape/favourites/save/', views.save_favourites, name='save_favourites'),
    
    # Movie endpoints
    path('movies/', views.get_all_movies, name='get_all_movies'),
    path('movies/favourites/', views.get_favourites, name='get_favourites'),
    path('movies/saved/', views.get_saved_movies, name='get_saved_movies'),
    
    # Movie management endpoints
    path('movies/<int:movie_id>/status/', views.update_movie_status, name='update_movie_status'),
    path('movies/<int:movie_id>/delete/', views.delete_movie, name='delete_movie'),
]