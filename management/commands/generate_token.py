from django.core.management.base import BaseCommand

from ...utils import generate_token


class Command(BaseCommand):
    help = 'Generate JWT token for API authentication'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Letterboxd username',
            required=True
        )
        parser.add_argument(
            '--secret-word',
            type=str,
            help='Secret word for authentication',
            required=True
        )
    
    def handle(self, *args, **options):
        username = options['username']
        secret_word = options['secret_word']
        
        try:
            token = generate_token(username, secret_word)
            
            self.stdout.write(
                self.style.SUCCESS('Your Bearer Token:')
            )
            self.stdout.write(token)
            self.stdout.write('\nUse this token in your Authorization header:')
            self.stdout.write(f'Authorization: Bearer {token}')
            
        except ValueError as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating token: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {e}')
            )