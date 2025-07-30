import re
from typing import Any, Dict, List


class ImageOptimizer:
    """
    Image URL optimization service for Letterboxd movie posters
    Equivalent to Go's ImageService
    """
    
    def __init__(self, width: int = 2000, height: int = 3000):
        """
        Initialize ImageService with default dimensions
        
        Args:
            width: Default image width
            height: Default image height
        """
        self.default_width = width
        self.default_height = height
    
    def update_image_url(self, url: str) -> str:
        """
        Update image URL with new dimensions
        
        Args:
            url: Original image URL
            
        Returns:
            Updated image URL with new dimensions
        """
        if not url:
            return url
        
        # Remove any query parameters (equivalent to strings.Split(url, "?")[0])
        url = url.split('?')[0]
        
        # Update the dimensions in the URL using regex
        # Pattern matches: -0-{width}-0-{height}-crop
        pattern = r'-0-\d+-0-\d+-crop'
        replacement = f'-0-{self.default_width}-0-{self.default_height}-crop'
        
        updated_url = re.sub(pattern, replacement, url)
        return updated_url
    
    def update_movie_image_urls(self, movies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Update image URLs for a list of movies
        
        Args:
            movies: List of movie dictionaries
            
        Returns:
            List of movies with updated image URLs
        """
        for movie in movies:
            if 'image_url' in movie:
                movie['image_url'] = self.update_image_url(movie['image_url'])
        
        return movies
    
    def get_optimized_url(self, original_url: str, width: int = None, height: int = None) -> str:
        """
        Get optimized image URL with custom dimensions
        
        Args:
            original_url: Original image URL
            width: Custom width (uses default if None)
            height: Custom height (uses default if None)
            
        Returns:
            Optimized image URL
        """
        if not original_url:
            return original_url
        
        # Use custom dimensions or fall back to defaults
        target_width = width or self.default_width
        target_height = height or self.default_height
        
        # Remove query parameters
        url = original_url.split('?')[0]
        
        # Update dimensions
        pattern = r'-0-\d+-0-\d+-crop'
        replacement = f'-0-{target_width}-0-{target_height}-crop'
        
        return re.sub(pattern, replacement, url)
    
    def extract_current_dimensions(self, url: str) -> tuple[int, int]:
        """
        Extract current dimensions from image URL
        
        Args:
            url: Image URL
            
        Returns:
            Tuple of (width, height), or (0, 0) if not found
        """
        if not url:
            return (0, 0)
        
        # Pattern to extract dimensions: -0-{width}-0-{height}-crop
        pattern = r'-0-(\d+)-0-(\d+)-crop'
        match = re.search(pattern, url)
        
        if match:
            width = int(match.group(1))
            height = int(match.group(2))
            return (width, height)
        
        return (0, 0)
    
    def is_optimized(self, url: str) -> bool:
        """
        Check if URL is already optimized with target dimensions
        
        Args:
            url: Image URL to check
            
        Returns:
            True if URL has target dimensions, False otherwise
        """
        current_width, current_height = self.extract_current_dimensions(url)
        return (current_width == self.default_width and 
                current_height == self.default_height)


# Factory function for easy instantiation (equivalent to Go's NewImageService)
def create_image_optimizer(width: int = 2000, height: int = 3000) -> ImageOptimizer:
    """
    Factory function to create ImageService instance
    
    Args:
        width: Image width
        height: Image height
        
    Returns:
        ImageService instance
    """
    return ImageOptimizer(width, height)


# Utility functions for common operations
def optimize_movie_images(movies: List[Dict[str, Any]], 
                         width: int = 2000, 
                         height: int = 3000) -> List[Dict[str, Any]]:
    """
    Convenience function to optimize movie image URLs
    
    Args:
        movies: List of movie dictionaries
        width: Target image width
        height: Target image height
        
    Returns:
        Movies with optimized image URLs
    """
    service = ImageOptimizer(width, height)
    return service.update_movie_image_urls(movies)


def optimize_single_url(url: str, width: int = 2000, height: int = 3000) -> str:
    """
    Convenience function to optimize a single image URL
    
    Args:
        url: Original image URL
        width: Target width
        height: Target height
        
    Returns:
        Optimized image URL
    """
    service = ImageOptimizer(width, height)
    return service.update_image_url(url)