from datetime import datetime, timedelta

import jwt
from django.conf import settings


def generate_token(username: str, secret_word: str) -> str:
    """
    Generate a new JWT token
    
    Args:
        username: Letterboxd username
        secret_word: Secret word for verification
        
    Returns:
        JWT token string
        
    Raises:
        ValueError: If credentials are invalid
    """
    # Get expected values from environment/settings
    expected_secret_word = getattr(settings, 'AUTH_SECRET_WORD', None)
    expected_username = getattr(settings, 'LETTERBOXD_USERNAME', None)
    jwt_secret = getattr(settings, 'JWT_SECRET', None)
    
    if not expected_secret_word:
        raise ValueError("AUTH_SECRET_WORD not configured")
    if not expected_username:
        raise ValueError("LETTERBOXD_USERNAME not configured")
    if not jwt_secret:
        raise ValueError("JWT_SECRET not configured")
    
    # Verify credentials
    if secret_word != expected_secret_word:
        raise ValueError("invalid secret word")
    if username != expected_username:
        raise ValueError("invalid username")
    
    # Create token payload
    payload = {
        'authorized': True,
        'username': username,
        'exp': datetime.utcnow() + timedelta(days=365)  # Expires in 1 year
    }
    
    # Generate token
    token = jwt.encode(payload, jwt_secret, algorithm='HS256')
    return token


def validate_token(token_string: str, username: str) -> bool:
    """
    Validate JWT token
    
    Args:
        token_string: JWT token to validate
        username: Expected username
        
    Returns:
        bool: True if token is valid, False otherwise
    """
    try:
        jwt_secret = getattr(settings, 'JWT_SECRET', None)
        if not jwt_secret:
            return False
        
        # Decode token
        payload = jwt.decode(token_string, jwt_secret, algorithms=['HS256'])
        
        # Check if token has required claims
        if not payload.get('authorized'):
            return False
        
        # Check username
        token_username = payload.get('username')
        if not token_username or token_username != username:
            return False
        
        return True
        
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False
    except Exception:
        return False