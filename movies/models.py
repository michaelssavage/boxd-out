from django.db import models


class Movie(models.Model):
    class Status(models.TextChoices):
        SAVED = 'SAVED', 'Saved'
        FAVORITE = 'FAVORITE', 'Favorite'

    title = models.TextField()
    year = models.TextField()
    status = models.CharField(
        max_length=8,
        choices=Status.choices,
        default=Status.SAVED
    )
    image_url = models.TextField()
    link_url = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['title', 'year']

    def __str__(self):
        return f"{self.title} ({self.year})"
