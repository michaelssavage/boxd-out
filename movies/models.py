from django.core.validators import MinLengthValidator
from django.db import models


class Movie(models.Model):
    class Status(models.TextChoices):
        SAVED = 'SAVED', 'Saved'
        FAVORITE = 'FAVORITE', 'Favorite'

    title = models.TextField(
        validators=[MinLengthValidator(1)],
        help_text="Full movie title"
    )
    
    year = models.CharField(
        max_length=4,
        validators=[MinLengthValidator(4)],
        help_text="Release year (YYYY)"
    )
    
    status = models.CharField(
        max_length=8,
        choices=Status.choices,
        default=Status.SAVED,
        help_text="SAVED or FAVORITE"
    )
    
    image_url = models.URLField(
        max_length=512,
        blank=True,
        help_text="URL to movie poster image"
    )
    
    link_url = models.URLField(
        max_length=512,
        blank=True,
        help_text="URL to movie page on Letterboxd"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['title', 'year']
        ordering = ['-created_at']  # Default ordering for DRF
        verbose_name = "Movie"
        verbose_name_plural = "Movies"

    def __str__(self):
        return f"{self.title} ({self.year})"