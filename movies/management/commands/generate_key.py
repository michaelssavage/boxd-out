from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key


class Command(BaseCommand):
    help = "Generates a new Django SECRET_KEY"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS(get_random_secret_key()))
